#!/usr/bin/env python3
"""把 3.13 章节运行态迁移到 4.0，保留旧 Markdown，不伪造历史审计。

已封板历史章只建立 legacy_closed 事务。只有旧 intent 本身含完整场景表时才
转换结构化 intent；缺失计划不会被反向编造。
"""

import argparse
import glob
import json
import os
import re
import shutil

from _contract import file_sha256
from check_chapter_draft import _norm_quote, _paragraphs, _scalar, _section, _table
from chapter_txn import _append_event, _atomic_json, transaction_path
from render_intent import render
from _schema import validate_document


def _chapter_number(path: str) -> int:
    match = re.search(r"chapter-(\d+)\.intent\.md$", path)
    return int(match.group(1)) if match else 0


def _source_manuscript(book_dir: str, chapter: int):
    draft = os.path.join(book_dir, "story", "runtime", f"chapter-{chapter:04d}.draft.md")
    if os.path.isfile(draft):
        return draft
    finals = sorted(glob.glob(os.path.join(book_dir, "chapters", f"{chapter:04d}_*.md")))
    return finals[0] if len(finals) == 1 else None


def migrate_intent(book_dir: str, path: str, warnings: list) -> None:
    chapter = _chapter_number(path)
    text = open(path, encoding="utf-8").read()
    _, beats = _table(_section(text, "Required Scene Beats"))
    _, evidence = _table(_section(text, "Draft Evidence Map"))
    source = _source_manuscript(book_dir, chapter)
    if not beats or not source:
        warnings.append(f"第 {chapter} 章缺少真实旧计划或唯一正文，只建立事务，不生成 intent.json")
        return
    required_legacy_fields = {
        "dramaticQuestion": _scalar(text, "dramatic_question"),
        "pov": _scalar(text, "pov"),
        "start": _scalar(text, "chapter_start_time"),
        "end": _scalar(text, "chapter_end_time"),
        "elapsed": _scalar(text, "elapsed"),
        "cutReason": _scalar(text, "cut_reason"),
    }
    missing = [key for key, value in required_legacy_fields.items() if not value]
    if missing:
        warnings.append(
            f"第 {chapter} 章旧 intent 缺少 {', '.join(missing)}；不猜测历史计划，保留 Markdown"
        )
        return
    digest = file_sha256(source)
    manuscript = open(source, encoding="utf-8").read()
    paragraphs = _paragraphs(manuscript)
    scene_beats = []
    for row in beats:
        required = {
            "beatId": row.get("beat_id", ""), "mode": row.get("mode", "scene"),
            "dramaticFunction": row.get("dramatic_function", ""),
            "goalOrPressure": row.get("goal_or_pressure", ""),
            "conflictOrTurn": row.get("conflict_or_turn", ""),
            "requiredResult": row.get("required_result", ""),
            "timeSpaceAnchor": row.get("time_space_anchor", ""),
            "descriptionObligation": row.get("description_obligation", ""),
        }
        if not all(str(value).strip() for value in required.values()):
            warnings.append(f"第 {chapter} 章旧 scene beat 不完整，保留 Markdown，不生成 intent.json")
            return
        scene_beats.append(required)
    converted_evidence = []
    for row in evidence:
        if row.get("status", "").lower() != "pass":
            continue
        match = re.search(r"P(\d+)(?:\s*[-–—]\s*P?(\d+))?", row.get("paragraph_refs", ""), re.I)
        if not match:
            continue
        start = int(match.group(1))
        end = int(match.group(2) or match.group(1))
        quote = row.get("evidence_quote", "")
        if start < 1 or end < start or end > len(paragraphs):
            warnings.append(f"第 {chapter} 章旧 Evidence Map 段落范围无效；保留 Markdown")
            return
        selected = "\n\n".join(paragraphs[start - 1:end])
        if not _norm_quote(quote) or _norm_quote(quote) not in _norm_quote(selected):
            warnings.append(f"第 {chapter} 章旧 Evidence Map 短引未在指定段落命中；保留 Markdown")
            return
        converted_evidence.append({
            "beatId": row.get("beat_id", ""),
            "paragraphStart": start,
            "paragraphEnd": end,
            "quote": quote,
            "draftSha256": digest,
            "status": "pass",
        })
    beat_ids = [item["beatId"] for item in scene_beats]
    evidence_ids = [item["beatId"] for item in converted_evidence]
    if sorted(evidence_ids) != sorted(beat_ids) or len(evidence_ids) != len(set(evidence_ids)):
        warnings.append(
            f"第 {chapter} 章旧 Evidence Map 不能与场景节点一一对应；保留 Markdown，不生成 intent.json"
        )
        return
    data = {
        "schemaVersion": "4.0",
        "chapter": chapter,
        "dramaticQuestion": required_legacy_fields["dramaticQuestion"],
        "pov": required_legacy_fields["pov"],
        "timeArchitecture": {
            "start": required_legacy_fields["start"],
            "end": required_legacy_fields["end"],
            "elapsed": required_legacy_fields["elapsed"],
            "cutReason": required_legacy_fields["cutReason"],
        },
        "sceneBeats": scene_beats,
        "evidence": converted_evidence,
    }
    schema_errors = validate_document(data, "chapter-intent.schema.json")
    if schema_errors:
        warnings.append(f"第 {chapter} 章旧 intent 无法无损迁移：" + "; ".join(schema_errors))
        return
    json_path = path[:-3] + ".json"
    _atomic_json(json_path, data)
    legacy_path = path[:-3] + ".legacy.md"
    if not os.path.exists(legacy_path):
        shutil.copy2(path, legacy_path)
    render(json_path, path)


def migrate_transaction(book_dir: str, path: str) -> None:
    chapter = _chapter_number(path)
    target = transaction_path(book_dir, chapter)
    if os.path.exists(target):
        return
    state = _scalar(open(path, encoding="utf-8").read(), "transaction_state")
    txn = {"schemaVersion": "4.0", "chapter": chapter, "state": "", "events": [], "legacyMigration": True}
    if state == "closed":
        _append_event(txn, "legacy_closed", note="3.13 历史封板；未伪造机械门禁或冷读记录")
    else:
        _append_event(txn, "prepared", note=f"从 3.13 状态 {state or 'missing'} 迁移；须重新完成 4.0 门禁")
    _atomic_json(target, txn)


def migrate(book_dir: str) -> list:
    warnings = []
    runtime = os.path.join(book_dir, "story", "runtime")
    for path in sorted(glob.glob(os.path.join(runtime, "chapter-*.intent.md"))):
        migrate_transaction(book_dir, path)
        migrate_intent(book_dir, path, warnings)
    return warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="迁移 Dragon Writer 3.13 运行态到 4.0")
    parser.add_argument("book_dir")
    args = parser.parse_args()
    warnings = migrate(args.book_dir)
    print(json.dumps({"ok": True, "warnings": warnings}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
