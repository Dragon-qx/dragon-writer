#!/usr/bin/env python3
"""章节草稿硬门禁：串行锁、字符下限与必要场景证据。

用法：
    python scripts/check_chapter_draft.py <book-dir> --chapter 12 --preflight
    python scripts/check_chapter_draft.py <book-dir> --chapter 12
    python scripts/check_chapter_draft.py <book-dir> --chapter 12 --draft path/to/draft.md --json

本脚本只检查可确定的契约，不尝试用词频代理文学质量。文学与连续性判断
分别由主代理知情审计和无背景冷读完成。
"""

import argparse
import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from _contract import chapter_length_limits, count_characters, file_sha256
from _schema import validate_document


ALLOWED_STATES = {"drafted", "gated", "audited", "closed"}
REQUIRED_BEAT_COLUMNS = {
    "beat_id",
    "mode",
    "dramatic_function",
    "goal_or_pressure",
    "conflict_or_turn",
    "required_result",
    "time_space_anchor",
    "description_obligation",
}
REQUIRED_EVIDENCE_COLUMNS = {"beat_id", "paragraph_refs", "evidence_quote", "status"}


@dataclass
class GateResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    infos: List[str] = field(default_factory=list)
    chapter: int = 0
    draft_path: str = ""
    character_count: int = 0
    minimum: int = 0
    target: int = 0
    maximum: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "chapter": self.chapter,
            "draftPath": self.draft_path,
            "characterCount": self.character_count,
            "limits": {
                "minimum": self.minimum,
                "target": self.target,
                "maximum": self.maximum,
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
        }


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _intent_path(book_dir: str, chapter: int) -> Optional[str]:
    runtime = os.path.join(book_dir, "story", "runtime")
    candidates = [
        os.path.join(runtime, f"chapter-{chapter:04d}.intent.md"),
        os.path.join(runtime, f"chapter-{chapter}.intent.md"),
    ]
    return next((p for p in candidates if os.path.isfile(p)), None)


def _intent_json_path(book_dir: str, chapter: int) -> Optional[str]:
    runtime = os.path.join(book_dir, "story", "runtime")
    candidates = [
        os.path.join(runtime, f"chapter-{chapter:04d}.intent.json"),
        os.path.join(runtime, f"chapter-{chapter}.intent.json"),
    ]
    return next((p for p in candidates if os.path.isfile(p)), None)


def _draft_path(book_dir: str, chapter: int, explicit: Optional[str]) -> Optional[str]:
    if explicit:
        path = explicit if os.path.isabs(explicit) else os.path.join(book_dir, explicit)
        return path if os.path.isfile(path) else None
    runtime = os.path.join(book_dir, "story", "runtime")
    candidates = [
        os.path.join(runtime, f"chapter-{chapter:04d}.draft.md"),
        os.path.join(runtime, f"chapter-{chapter}.draft.md"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    final = sorted(glob.glob(os.path.join(book_dir, "chapters", f"{chapter:04d}_*.md")))
    if not final:
        final = sorted(glob.glob(os.path.join(book_dir, "chapters", f"{chapter}_*.md")))
    return final[0] if final else None


def _scalar(text: str, key: str) -> Optional[str]:
    match = re.search(rf"(?mi)^\s*-\s*{re.escape(key)}\s*:\s*(.*?)\s*$", text)
    return match.group(1).strip() if match else None


def _positive_int(text: str, key: str) -> Optional[int]:
    value = _scalar(text, key)
    if value is None or not re.fullmatch(r"\d+", value):
        return None
    number = int(value)
    return number if number > 0 else None


def _section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^##\s+{re.escape(heading)}(?:\s|（|\().*?\n(.*?)(?=^##\s+|\Z)"
    )
    match = pattern.search(text)
    return match.group(1) if match else ""


def _table(section: str) -> Tuple[List[str], List[Dict[str, str]]]:
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return [], []

    def cells(line: str) -> List[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    header = cells(lines[0])
    rows: List[Dict[str, str]] = []
    for line in lines[1:]:
        values = cells(line)
        if values and all(re.fullmatch(r":?-{3,}:?", value) for value in values):
            continue
        if len(values) != len(header):
            continue
        rows.append(dict(zip(header, values)))
    return header, rows


def _norm_quote(text: str) -> str:
    return re.sub(r"\s+", "", text).strip("`<>《》")


def _paragraphs(text: str) -> List[str]:
    """以空行分隔并确定性编号 P1..Pn；标题也占一个段落。"""
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def _placeholder(value: str) -> bool:
    return bool(re.search(r"<[^>]+>|待填|待补|TODO|TBD", value, flags=re.IGNORECASE))


def _placeholder_paths(value, prefix: str = "$") -> List[str]:
    """递归找出结构化意图中的占位字符串，避免字段齐全但内容仍是假数据。"""
    found = []
    if isinstance(value, str) and _placeholder(value):
        found.append(prefix)
    elif isinstance(value, dict):
        for key, item in value.items():
            found.extend(_placeholder_paths(item, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_placeholder_paths(item, f"{prefix}[{index}]"))
    return found


def _ref_range(value: str) -> Optional[Tuple[int, int]]:
    match = re.search(r"\bP(\d+)(?:\s*[-–—]\s*P?(\d+))?", value, flags=re.IGNORECASE)
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2) or start)
    return (start, end) if start <= end else None


def _check_v41_semantics(intent: dict, result: GateResult) -> None:
    """JSON Schema 管形状；这里核验跨字段的时间、信息和关系引用。"""
    if intent.get("schemaVersion") != "4.1":
        result.warnings.append("当前 intent 为 4.0 兼容格式；新章应迁移到 4.1 语义契约")
        return
    segments = intent.get("timeArchitecture", {}).get("segments", [])
    if not segments:
        result.errors.append("4.1 intent 必须提供 timeArchitecture.segments")
    segment_ids = [row.get("segmentId", "") for row in segments]
    orders = [row.get("order") for row in segments]
    if len(segment_ids) != len(set(segment_ids)):
        result.errors.append("timeArchitecture.segmentId 必须唯一")
    if any(not isinstance(value, int) for value in orders) or orders != sorted(set(orders)):
        result.errors.append("timeArchitecture.segments.order 必须严格递增且唯一")
    for row in segments:
        if row.get("mode") in {"summary", "ellipsis", "transition"} and not row.get("cutReason"):
            result.errors.append(f"时间段 {row.get('segmentId')} 的压缩/跳时必须说明 cutReason")
    if not intent.get("noveltyFingerprint"):
        result.errors.append("4.1 intent 必须填写结构化 noveltyFingerprint")

    holders = {}
    for permission in intent.get("knowledgePermissions", []):
        character_id = permission.get("characterId", "")
        if not character_id:
            result.errors.append(f"信息权限 {permission.get('character', '<unknown>')} 缺少 characterId")
            continue
        facts = set(permission.get("knownFactIds", []))
        for acquired in permission.get("acquiredThisChapter", []):
            fact_id = acquired.get("factId", "")
            if not fact_id:
                result.errors.append(f"{character_id} 的本章获知项缺少 factId")
            else:
                facts.add(fact_id)
        holders[character_id] = facts

    relation_pairs = {}
    for permission in intent.get("relationshipPermissions", []):
        pair_id = permission.get("pairId", "")
        participants = permission.get("participants", [])
        if len(participants) != 2:
            result.errors.append(f"关系权限 {pair_id or '<empty>'} 必须明确两个参与角色")
        relation_pairs[pair_id] = set(participants)

    for beat in intent.get("sceneBeats", []):
        beat_id = beat.get("beatId", "<empty>")
        participants = beat.get("participants", [])
        if not participants:
            result.errors.append(f"场景节点 {beat_id} 缺少 participants")
        if beat.get("timeSegmentId") not in set(segment_ids):
            result.errors.append(f"场景节点 {beat_id} 引用了不存在的 timeSegmentId")
        for use in beat.get("knowledgeUses", []):
            character_id = use.get("characterId", "")
            fact_id = use.get("factId", "")
            if character_id not in participants:
                result.errors.append(f"场景节点 {beat_id} 的信息使用者 {character_id} 不在参与角色中")
            if fact_id not in holders.get(character_id, set()):
                result.errors.append(
                    f"场景节点 {beat_id}：{character_id} 使用了未获知事实 {fact_id}"
                )
        refs = beat.get("relationshipRefs", [])
        if len(participants) > 1 and not refs:
            result.errors.append(f"多人场景节点 {beat_id} 必须引用关系权限")
        for pair_id in refs:
            if pair_id not in relation_pairs:
                result.errors.append(f"场景节点 {beat_id} 引用了不存在的关系权限 {pair_id}")
            elif not relation_pairs[pair_id].issubset(set(participants)):
                result.errors.append(f"场景节点 {beat_id} 的关系 {pair_id} 角色不在该场景参与者中")


def _check_previous_lock(book_dir: str, chapter: int, result: GateResult) -> None:
    if chapter <= 1:
        return
    from chapter_txn import load_transaction, verify_closed_bindings

    previous_txn = load_transaction(book_dir, chapter - 1)
    if previous_txn:
        errors = verify_closed_bindings(book_dir, chapter - 1, previous_txn)
        if errors:
            result.errors.append("上一章没有完整封板：" + "; ".join(errors))
        return
    result.errors.append(
        f"上一章缺少结构化 transaction.json；先迁移并建立可验证封板，禁止直接开始第 {chapter} 章"
    )


def check_draft(book_dir: str, chapter: int, draft: Optional[str] = None) -> GateResult:
    result = GateResult(chapter=chapter)
    _check_previous_lock(book_dir, chapter, result)

    intent_json_path = _intent_json_path(book_dir, chapter)
    intent_path = _intent_path(book_dir, chapter)
    intent_data = None
    intent = ""
    if intent_json_path:
        try:
            intent_data = json.loads(_read(intent_json_path))
        except json.JSONDecodeError as exc:
            result.errors.append(f"intent JSON 解析失败：{exc}")
            return result
        result.errors.extend(
            "intent JSON：" + message
            for message in validate_document(intent_data, "chapter-intent.schema.json")
        )
        _check_v41_semantics(intent_data, result)
        placeholders = _placeholder_paths(intent_data)
        if placeholders:
            result.errors.append("intent JSON 仍含占位内容：" + ", ".join(placeholders))
        if intent_data.get("chapter") != chapter:
            result.errors.append("intent JSON 的 chapter 与当前章号不一致")
        from chapter_txn import load_transaction, verify_transaction
        txn = load_transaction(book_dir, chapter)
        if not txn:
            result.errors.append("结构化 intent 缺少对应 transaction.json；请先 prepare / mark-drafted")
        else:
            txn_errors = verify_transaction(txn)
            if txn_errors:
                result.errors.append("当前章事务链无效：" + "; ".join(txn_errors))
            elif txn.get("state") not in {"drafted", "gated", "audited"}:
                result.errors.append(
                    f"当前章事务状态为 {txn.get('state')}，机械门禁要求 drafted"
                )
    elif intent_path:
        intent = _read(intent_path)
        result.warnings.append("正在使用 3.x Markdown intent 兼容模式；请迁移为 intent.json")
        state = _scalar(intent, "transaction_state")
        if state not in ALLOWED_STATES:
            result.errors.append(
                f"当前章 transaction_state={state or 'missing'}，完成草稿后应为 drafted 再运行门禁"
            )
    else:
        result.errors.append(
            f"缺少当前章权威 intent：story/runtime/chapter-{chapter:04d}.intent.json"
        )
        return result

    draft_path = _draft_path(book_dir, chapter, draft)
    if not draft_path:
        result.errors.append(f"找不到第 {chapter} 章草稿或正文")
        return result
    result.draft_path = os.path.relpath(draft_path, book_dir).replace(os.sep, "/")
    draft_text = _read(draft_path)

    book_path = os.path.join(book_dir, "book.json")
    try:
        book_data = json.loads(_read(book_path))
    except (OSError, json.JSONDecodeError):
        book_data = {}
        result.errors.append("book.json 无法读取，不能确定章节长度契约")
    default_min, default_target, default_max = chapter_length_limits(book_data)

    if intent_data is not None:
        planned_target = intent_data.get("plannedTargetChars", default_target)
        result.minimum = default_min
        result.target = max(default_target, planned_target)
        result.maximum = max(default_max, result.target)
    else:
        intent_min = _positive_int(intent, "min_chars")
        intent_target = _positive_int(intent, "target_chars")
        intent_max = _positive_int(intent, "max_chars")
        for key, value in (
            ("min_chars", intent_min),
            ("target_chars", intent_target),
            ("max_chars", intent_max),
        ):
            if value is None:
                result.errors.append(f"intent 的 {key} 必须填写正整数，不能保留占位符")
        if intent_min is not None and intent_min < default_min:
            result.errors.append(
                f"intent.min_chars={intent_min} 低于 book.json 硬下限 {default_min}，不得降低书级契约"
            )
        result.minimum = max(default_min, intent_min or default_min)
        result.target = max(default_target, intent_target or default_target, result.minimum)
        result.maximum = max(default_max, intent_max or default_max, result.target)
    if not result.minimum <= result.target <= result.maximum:
        result.errors.append(
            f"章节长度契约顺序错误：min={result.minimum}, target={result.target}, max={result.maximum}"
        )

    result.character_count = count_characters(draft_text)
    if result.character_count < result.minimum:
        result.errors.append(
            f"章节字符数不足：实际 {result.character_count}，硬下限 {result.minimum}；"
            "必须按缺失场景节点补足叙事工作，禁止注水"
        )
    elif result.character_count > result.maximum:
        result.warnings.append(
            f"章节字符数超过软上限：实际 {result.character_count}，上限 {result.maximum}；请检查拖沓或重复"
        )
    else:
        result.infos.append(
            f"章节字符数 {result.character_count}（下限 {result.minimum} / 目标 {result.target} / 上限 {result.maximum}）"
        )

    if intent_data is not None:
        beats = [{
            "beat_id": row.get("beatId", ""),
            "mode": row.get("mode", ""),
            "dramatic_function": row.get("dramaticFunction", ""),
            "goal_or_pressure": row.get("goalOrPressure", ""),
            "conflict_or_turn": row.get("conflictOrTurn", ""),
            "required_result": row.get("requiredResult", ""),
            "time_space_anchor": row.get("timeSpaceAnchor", ""),
            "description_obligation": row.get("descriptionObligation", ""),
        } for row in intent_data.get("sceneBeats", [])]
        beat_header = sorted(REQUIRED_BEAT_COLUMNS)
        evidence_rows = [{
            "beat_id": row.get("beatId", ""),
            "paragraph_refs": f"P{row.get('paragraphStart', 0)}-P{row.get('paragraphEnd', 0)}",
            "evidence_quote": row.get("quote", ""),
            "status": row.get("status", ""),
            "draft_sha256": row.get("draftSha256", ""),
            "shared_reason": row.get("sharedEvidenceReason", ""),
        } for row in intent_data.get("evidence", [])]
        evidence_header = sorted(REQUIRED_EVIDENCE_COLUMNS)
    else:
        beat_header, beats = _table(_section(intent, "Required Scene Beats"))
        evidence_header, evidence_rows = _table(_section(intent, "Draft Evidence Map"))
    missing_beat_columns = sorted(REQUIRED_BEAT_COLUMNS - set(beat_header))
    missing_evidence_columns = sorted(REQUIRED_EVIDENCE_COLUMNS - set(evidence_header))
    if missing_beat_columns:
        result.errors.append("Required Scene Beats 缺少列：" + ", ".join(missing_beat_columns))
    if missing_evidence_columns:
        result.errors.append("Draft Evidence Map 缺少列：" + ", ".join(missing_evidence_columns))
    if missing_beat_columns or missing_evidence_columns:
        return result
    if not beats:
        result.errors.append("Required Scene Beats 至少需要一个实际场景节点")
        return result

    beat_ids = [row.get("beat_id", "").strip() for row in beats]
    if any(not beat_id for beat_id in beat_ids):
        result.errors.append("Required Scene Beats 存在空 beat_id")
    if len(set(beat_ids)) != len(beat_ids):
        result.errors.append("Required Scene Beats 的 beat_id 必须唯一")
    for row in beats:
        beat_id = row.get("beat_id", "").strip() or "<empty>"
        missing_values = [column for column in REQUIRED_BEAT_COLUMNS if not row.get(column, "").strip()]
        if missing_values:
            result.errors.append(f"场景节点 {beat_id} 缺少内容：{', '.join(sorted(missing_values))}")
        for column in REQUIRED_BEAT_COLUMNS:
            if _placeholder(row.get(column, "")):
                result.errors.append(f"场景节点 {beat_id} 的 {column} 仍是占位内容")

    evidence_by_id: Dict[str, List[Dict[str, str]]] = {}
    for row in evidence_rows:
        evidence_by_id.setdefault(row.get("beat_id", "").strip(), []).append(row)
    paragraphs = _paragraphs(draft_text)
    draft_digest = file_sha256(draft_path)
    quote_owners: Dict[str, str] = {}
    for beat_id in beat_ids:
        matches = evidence_by_id.get(beat_id, [])
        if len(matches) != 1:
            result.errors.append(f"场景节点 {beat_id} 必须恰好有一行证据，当前 {len(matches)} 行")
            continue
        evidence = matches[0]
        refs = evidence.get("paragraph_refs", "").strip()
        quote = evidence.get("evidence_quote", "").strip()
        status = evidence.get("status", "").strip().lower()
        bounds = _ref_range(refs)
        if not bounds:
            result.errors.append(f"场景节点 {beat_id} 的 paragraph_refs 必须是有效 P+段落范围")
            selected = ""
        else:
            start, end = bounds
            if start < 1 or end > len(paragraphs):
                result.errors.append(
                    f"场景节点 {beat_id} 的 paragraph_refs 越界：{refs}，正文共 {len(paragraphs)} 段"
                )
                selected = ""
            else:
                selected = "\n\n".join(paragraphs[start - 1:end])
        normalized_quote = _norm_quote(quote)
        if not normalized_quote or normalized_quote not in _norm_quote(selected):
            result.errors.append(
                f"场景节点 {beat_id} 的 evidence_quote 未在草稿正文命中（限定所填段落范围）"
            )
        if intent_data is not None and evidence.get("draft_sha256") != draft_digest:
            result.errors.append(f"场景节点 {beat_id} 的 evidence 已因草稿哈希变化而失效")
        owner = quote_owners.get(normalized_quote)
        if normalized_quote and owner and not evidence.get("shared_reason"):
            result.errors.append(f"场景节点 {beat_id} 与 {owner} 复用了同一证据且未说明共享原因")
        elif normalized_quote:
            quote_owners[normalized_quote] = beat_id
        if status != "pass":
            result.errors.append(f"场景节点 {beat_id} 的证据状态必须为 pass，当前 {status or 'missing'}")

    extra_ids = sorted(set(evidence_by_id) - set(beat_ids) - {""})
    if extra_ids:
        result.warnings.append("Draft Evidence Map 含未声明节点：" + ", ".join(extra_ids))
    return result


def check_preflight(book_dir: str, chapter: int) -> GateResult:
    """在创建当前章 intent / draft 前检查上一章封板锁。"""
    result = GateResult(chapter=chapter)
    _check_previous_lock(book_dir, chapter, result)
    if result.ok:
        result.infos.append(f"第 {chapter} 章可以进入 prepared")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="检查章节草稿硬门禁")
    parser.add_argument("book_dir", help="书籍根目录")
    parser.add_argument("--chapter", type=int, required=True, help="章节编号")
    parser.add_argument("--draft", help="草稿路径（相对书根或绝对路径）")
    parser.add_argument("--preflight", action="store_true", help="只检查上一章 closed 锁，不要求当前草稿")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    if not os.path.isdir(args.book_dir):
        print(f"错误：目录不存在 {args.book_dir}", file=sys.stderr)
        raise SystemExit(1)
    if args.chapter < 1:
        print("错误：chapter 必须大于 0", file=sys.stderr)
        raise SystemExit(1)

    result = (
        check_preflight(args.book_dir, args.chapter)
        if args.preflight
        else check_draft(args.book_dir, args.chapter, args.draft)
    )
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print("[PASS] Chapter draft gate passed" if result.ok else "[FAIL] Chapter draft gate failed")
        for message in result.errors:
            print(f"  [ERROR] {message}")
        for message in result.warnings:
            print(f"  [WARN] {message}")
        for message in result.infos:
            print(f"  [INFO] {message}")
    raise SystemExit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
