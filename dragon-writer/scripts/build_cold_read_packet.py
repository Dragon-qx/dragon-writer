#!/usr/bin/env python3
"""从章节正文确定性构造无背景冷读包，不读取任何项目设定或 Runtime 状态。"""

import argparse
import glob
import os
import json
import sys
from typing import Iterable, List, Optional, Tuple

from _contract import file_sha256, now_iso, safe_join


NEUTRAL_PROMPT = (
    "你是一名第一次接触这份稿件的小说编辑。只依据下面提供的正文阅读，"
    "不推测作者未提供的设定或意图。报告会影响普通读者理解或阅读体验的问题。"
    "每项包含：严重度、正文位置与短引、读者影响、修复方向。"
    "不要续写、改写正文，也不要声称核实了正文之外的事实；证据不足时写 unknown。"
)


def _chapter_path(book_dir: str, chapter: int, prefer_draft: bool) -> Optional[str]:
    if prefer_draft:
        runtime = os.path.join(book_dir, "story", "runtime")
        for name in (f"chapter-{chapter:04d}.draft.md", f"chapter-{chapter}.draft.md"):
            path = os.path.join(runtime, name)
            if os.path.isfile(path):
                return path
    matches = sorted(glob.glob(os.path.join(book_dir, "chapters", f"{chapter:04d}_*.md")))
    if not matches:
        matches = sorted(glob.glob(os.path.join(book_dir, "chapters", f"{chapter}_*.md")))
    return matches[0] if matches else None


def build_packet(book_dir: str, chapters: Iterable[int], prefer_draft: bool = True) -> str:
    """3.x 兼容 API；新工作流应使用 build_explicit_packet。"""
    parts = [NEUTRAL_PROMPT]
    for chapter in chapters:
        path = _chapter_path(book_dir, chapter, prefer_draft)
        if not path:
            raise FileNotFoundError(f"找不到第 {chapter} 章正文或草稿")
        with open(path, "r", encoding="utf-8") as f:
            manuscript = f.read().strip()
        parts.append(f"===== 第 {chapter} 章 =====\n{manuscript}")
    return "\n\n".join(parts) + "\n"


def _final_path(book_dir: str, chapter: int) -> str:
    matches = sorted(glob.glob(os.path.join(book_dir, "chapters", f"{chapter:04d}_*.md")))
    if not matches:
        matches = sorted(glob.glob(os.path.join(book_dir, "chapters", f"{chapter}_*.md")))
    if len(matches) != 1:
        raise FileNotFoundError(f"第 {chapter} 章正式正文应恰好一份，当前 {len(matches)} 份")
    return matches[0]


def _draft_only_path(book_dir: str, chapter: int) -> str:
    runtime = os.path.join(book_dir, "story", "runtime")
    matches = [
        os.path.join(runtime, f"chapter-{chapter:04d}.draft.md"),
        os.path.join(runtime, f"chapter-{chapter}.draft.md"),
    ]
    existing = [path for path in matches if os.path.isfile(path)]
    if len(existing) != 1:
        raise FileNotFoundError(f"第 {chapter} 章草稿应恰好一份，当前 {len(existing)} 份")
    return existing[0]


def build_explicit_packet(
    book_dir: str, final_chapters: Iterable[int] = (), draft_chapter: Optional[int] = None
) -> Tuple[str, dict]:
    """按显式稿源构造冷读包，并返回不进入包内的来源 manifest。"""
    final_chapters = list(final_chapters)
    if draft_chapter is not None and draft_chapter in final_chapters:
        raise ValueError("同一章不能同时作为 final 与 draft 进入冷读包")
    sources: List[Tuple[int, str, str]] = []
    for chapter in final_chapters:
        sources.append((chapter, "final", _final_path(book_dir, chapter)))
    if draft_chapter is not None:
        draft = _draft_only_path(book_dir, draft_chapter)
        from chapter_txn import audit_path, load_transaction, verify_transaction
        txn = load_transaction(book_dir, draft_chapter)
        if not txn or verify_transaction(txn) or txn.get("state") not in {"gated", "audited"}:
            raise ValueError("冷读草稿必须处于可验证的 gated/audited 事务")
        if txn.get("draftSha256") != file_sha256(draft):
            raise ValueError("冷读草稿哈希与事务不一致")
        audit_manifest = audit_path(book_dir, draft_chapter)
        if not os.path.isfile(audit_manifest):
            raise ValueError("冷读前必须先登记主代理知情审计")
        with open(audit_manifest, "r", encoding="utf-8") as handle:
            audit_data = json.load(handle)
        informed = audit_data.get("informedAudit", {})
        report = safe_join(book_dir, informed.get("reportPath", ""))
        if (
            audit_data.get("draftSha256") != file_sha256(draft)
            or informed.get("status") != "pass"
            or not os.path.isfile(report)
            or informed.get("reportSha256") != file_sha256(report)
        ):
            raise ValueError("主代理知情审计缺失、失败或哈希已失效")
        sources.append((draft_chapter, "draft", draft))
    if not sources:
        raise ValueError("至少指定一个 --final/--final-range 或 --draft")
    if len({chapter for chapter, _, _ in sources}) != len(sources):
        raise ValueError("同一章不能同时作为 final 与 draft 进入冷读包")
    sources.sort(key=lambda item: item[0])
    parts = [NEUTRAL_PROMPT]
    manifest_sources = []
    for chapter, role, path in sources:
        with open(path, "r", encoding="utf-8") as handle:
            manuscript = handle.read().strip()
        parts.append(f"===== 第 {chapter} 章 =====\n{manuscript}")
        manifest_sources.append({
            "chapter": chapter,
            "role": role,
            "path": os.path.relpath(path, book_dir).replace(os.sep, "/"),
            "sha256": file_sha256(path),
        })
    packet = "\n\n".join(parts) + "\n"
    import hashlib
    manifest = {
        "schemaVersion": "4.0",
        "createdAt": now_iso(),
        "sources": manifest_sources,
        "packetSha256": "sha256:" + hashlib.sha256(packet.encode("utf-8")).hexdigest(),
    }
    return packet, manifest


def _parse_range(value: str) -> List[int]:
    match = __import__("re").fullmatch(r"(\d+):(\d+)", value)
    if not match:
        raise ValueError("--final-range 必须使用 START:END")
    start, end = map(int, match.groups())
    if start < 1 or end < start:
        raise ValueError("--final-range 范围无效")
    return list(range(start, end + 1))


def main() -> None:
    parser = argparse.ArgumentParser(description="构造纯正文冷读包")
    parser.add_argument("book_dir", help="书籍根目录")
    parser.add_argument("--final", type=int, nargs="*", default=[], help="明确读取的正式章节")
    parser.add_argument("--draft", type=int, help="明确读取的唯一当前草稿")
    parser.add_argument("--final-range", help="正式章节闭区间 START:END")
    parser.add_argument("--manifest", help="把稿源与哈希写入包外 manifest JSON")
    args = parser.parse_args()
    if not os.path.isdir(args.book_dir):
        print(f"错误：目录不存在 {args.book_dir}", file=sys.stderr)
        raise SystemExit(1)
    final_chapters = list(args.final)
    try:
        if args.final_range:
            final_chapters.extend(_parse_range(args.final_range))
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
    if any(chapter < 1 for chapter in final_chapters) or (args.draft is not None and args.draft < 1):
        print("错误：章节号必须大于 0", file=sys.stderr)
        raise SystemExit(1)
    try:
        packet, manifest = build_explicit_packet(args.book_dir, final_chapters, args.draft)
        if args.manifest:
            manifest_path = args.manifest if os.path.isabs(args.manifest) else os.path.join(args.book_dir, args.manifest)
            os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
            with open(manifest_path, "w", encoding="utf-8") as handle:
                json.dump(manifest, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        sys.stdout.write(packet)
    except (OSError, FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
