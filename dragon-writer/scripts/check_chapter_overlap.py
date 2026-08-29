#!/usr/bin/env python3
"""检测当前章与近章的近似文本重叠。

机械检查只负责表层重复：整章高度相似、多个近似段落、同构开头或收尾。
情节语义是否重复仍由审计维 42 结合 novelty_fingerprint 冷读判断。
"""

import argparse
import difflib
import json
import os
import re
import sys
from typing import Dict, List, Tuple


CHAPTER_RE = re.compile(r"^(\d+)_.*\.md$", re.IGNORECASE)


def _compact(text: str) -> str:
    """去掉 Markdown 噪声、空白和标点，保留文字与数字。"""
    text = re.sub(r"^#+\s+.*$", "", text, flags=re.MULTILINE)
    return "".join(ch.lower() for ch in text if ch.isalnum())


def _paragraphs(text: str, minimum: int = 50) -> List[str]:
    parts = re.split(r"\n\s*\n", text)
    return [p for p in (_compact(part) for part in parts) if len(p) >= minimum]


def _ngrams(text: str, size: int = 4) -> set:
    if len(text) < size:
        return {text} if text else set()
    return {text[i:i + size] for i in range(len(text) - size + 1)}


def _jaccard(a: str, b: str) -> float:
    left, right = _ngrams(a), _ngrams(b)
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _similarity(a: str, b: str) -> Tuple[float, float]:
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio(), _jaccard(a, b)


def _chapter_files(book_dir: str) -> List[Tuple[int, str]]:
    chapters_dir = os.path.join(book_dir, "chapters")
    found = []
    if not os.path.isdir(chapters_dir):
        return found
    for name in os.listdir(chapters_dir):
        match = CHAPTER_RE.match(name)
        if match:
            found.append((int(match.group(1)), os.path.join(chapters_dir, name)))
    return sorted(found)


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def compare_texts(target_text: str, previous_text: str, previous_chapter: int) -> List[Dict]:
    """返回一个前章相对于目标章的重叠发现。"""
    findings: List[Dict] = []
    target = _compact(target_text)
    previous = _compact(previous_text)

    if min(len(target), len(previous)) >= 500:
        whole_ratio, whole_jaccard = _similarity(target, previous)
        if whole_ratio >= 0.58 or whole_jaccard >= 0.52:
            findings.append({
                "severity": "blocking",
                "kind": "whole_chapter_overlap",
                "previous_chapter": previous_chapter,
                "ratio": round(whole_ratio, 3),
                "jaccard": round(whole_jaccard, 3),
                "message": "整章与前章高度相似，需先排除换词重写或重复情节。",
            })

    target_paragraphs = _paragraphs(target_text)
    previous_paragraphs = _paragraphs(previous_text)
    paragraph_hits = []
    for target_index, target_paragraph in enumerate(target_paragraphs, start=1):
        best = None
        for previous_index, previous_paragraph in enumerate(previous_paragraphs, start=1):
            ratio, jaccard = _similarity(target_paragraph, previous_paragraph)
            if ratio >= 0.86 or jaccard >= 0.78:
                candidate = (max(ratio, jaccard), previous_index, ratio, jaccard)
                if best is None or candidate[0] > best[0]:
                    best = candidate
        if best:
            _, previous_index, ratio, jaccard = best
            paragraph_hits.append({
                "target_paragraph": target_index,
                "previous_paragraph": previous_index,
                "ratio": round(ratio, 3),
                "jaccard": round(jaccard, 3),
            })
    if paragraph_hits:
        findings.append({
            "severity": "blocking" if len(paragraph_hits) >= 2 else "warning",
            "kind": "paragraph_overlap",
            "previous_chapter": previous_chapter,
            "matches": paragraph_hits,
            "message": f"发现 {len(paragraph_hits)} 组近似段落。",
        })

    for label, target_slice, previous_slice in (
        ("opening", target[:260], previous[:260]),
        ("closing", target[-260:], previous[-260:]),
    ):
        if min(len(target_slice), len(previous_slice)) < 120:
            continue
        ratio, jaccard = _similarity(target_slice, previous_slice)
        if ratio >= 0.76 or jaccard >= 0.66:
            findings.append({
                "severity": "warning",
                "kind": f"{label}_overlap",
                "previous_chapter": previous_chapter,
                "ratio": round(ratio, 3),
                "jaccard": round(jaccard, 3),
                "message": f"章{('首' if label == 'opening' else '末')}与前章近似，检查是否复用同一动作与功能。",
            })
    return findings


def analyze_book(book_dir: str, chapter: int = 0, window: int = 10) -> Dict:
    chapters = _chapter_files(book_dir)
    if not chapters:
        raise ValueError("chapters/ 下没有可识别的 NNNN_*.md 章节")
    target_number = chapter or chapters[-1][0]
    by_number = dict(chapters)
    if target_number not in by_number:
        raise ValueError(f"找不到第 {target_number} 章")
    previous = [(num, path) for num, path in chapters if num < target_number][-window:]
    target_text = _read(by_number[target_number])
    findings: List[Dict] = []
    for previous_number, previous_path in previous:
        findings.extend(compare_texts(target_text, _read(previous_path), previous_number))
    blocking = sum(1 for finding in findings if finding["severity"] == "blocking")
    warnings = sum(1 for finding in findings if finding["severity"] == "warning")
    return {
        "chapter": target_number,
        "window": window,
        "compared_chapters": [num for num, _ in previous],
        "status": "fail" if blocking else "pass",
        "blocking_count": blocking,
        "warning_count": warnings,
        "findings": findings,
        "note": "本脚本只检查近似文本；情节语义重复须结合 novelty_fingerprint 运行审计维 42。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查当前章与近章的近似文本重叠")
    parser.add_argument("book_dir", help="书籍根目录")
    parser.add_argument("--chapter", type=int, default=0, help="目标章号；默认最新章")
    parser.add_argument("--window", type=int, default=10, help="向前比较章数，默认 10")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()
    try:
        report = analyze_book(args.book_dir, args.chapter, max(1, args.window))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"第 {report['chapter']} 章：{report['status']} "
            f"(blocking={report['blocking_count']}, warning={report['warning_count']})"
        )
        for finding in report["findings"]:
            print(
                f"  [{finding['severity']}] 对比第 {finding['previous_chapter']} 章："
                f"{finding['message']}"
            )
        print(f"  注：{report['note']}")
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
