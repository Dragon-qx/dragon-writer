#!/usr/bin/env python3
"""哈希绑定的章节事务状态机。

状态只能经本脚本推进；事件使用前一事件哈希形成可验证链。文学审计报告仍是
Markdown，本文件只保存报告路径、哈希和通过状态。
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Optional

from _contract import file_sha256, now_iso, safe_join
from _schema import validate_document


TRANSITIONS = {
    "": {"prepared", "legacy_closed"},
    "prepared": {"drafted"},
    "reopened": {"drafted"},
    "drafted": {"gated", "reopened"},
    "gated": {"audited", "reopened"},
    "audited": {"closed", "reopened"},
    "closed": {"reopened"},
    "legacy_closed": {"reopened"},
}


def transaction_path(book_dir: str, chapter: int) -> str:
    return os.path.join(book_dir, "story", "runtime", f"chapter-{chapter:04d}.transaction.json")


def audit_path(book_dir: str, chapter: int) -> str:
    return os.path.join(book_dir, "story", "runtime", f"chapter-{chapter:04d}.audit.json")


def gate_path(book_dir: str, chapter: int) -> str:
    return os.path.join(book_dir, "story", "runtime", f"chapter-{chapter:04d}.gate.json")


def draft_path(book_dir: str, chapter: int) -> str:
    return os.path.join(book_dir, "story", "runtime", f"chapter-{chapter:04d}.draft.md")


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _atomic_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temp, path)


def _supersede(path: str, marker: str) -> None:
    """可恢复地移走已失效派生记录，不静默删除审计证据。"""
    if not os.path.isfile(path):
        return
    base = f"{path}.superseded-{marker[:12]}"
    target = base
    counter = 1
    while os.path.exists(target):
        target = f"{base}-{counter}"
        counter += 1
    os.replace(path, target)


def _event_hash(event: dict) -> str:
    body = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _append_event(txn: dict, new_state: str, **details) -> None:
    old_state = txn.get("state", "")
    if new_state not in TRANSITIONS.get(old_state, set()):
        raise ValueError(f"非法事务跃迁：{old_state or '<none>'} → {new_state}")
    events = txn.setdefault("events", [])
    previous = events[-1]["eventHash"] if events else ""
    event = {
        "sequence": len(events) + 1,
        "from": old_state,
        "to": new_state,
        "timestamp": now_iso(),
        "previousEventHash": previous,
        **details,
    }
    event["eventHash"] = _event_hash(event)
    events.append(event)
    txn["state"] = new_state


def verify_transaction(txn: dict) -> list:
    errors = validate_document(txn, "chapter-transaction.schema.json")
    previous = ""
    state = ""
    for index, event in enumerate(txn.get("events", []), start=1):
        supplied = event.get("eventHash", "")
        body = dict(event)
        body.pop("eventHash", None)
        expected = _event_hash(body)
        if event.get("sequence") != index:
            errors.append(f"events[{index - 1}] sequence 不连续")
        if event.get("previousEventHash", "") != previous:
            errors.append(f"events[{index - 1}] previousEventHash 断链")
        if supplied != expected:
            errors.append(f"events[{index - 1}] eventHash 不匹配")
        if event.get("from", "") != state or event.get("to") not in TRANSITIONS.get(state, set()):
            errors.append(f"events[{index - 1}] 非法跃迁 {event.get('from')} → {event.get('to')}")
        state = event.get("to", state)
        previous = supplied
    if txn.get("state") != state:
        errors.append("当前 state 与事件链末状态不一致")
    return errors


def load_transaction(book_dir: str, chapter: int) -> Optional[dict]:
    path = transaction_path(book_dir, chapter)
    return _load(path) if os.path.isfile(path) else None


def create_prepared(book_dir: str, chapter: int) -> dict:
    path = transaction_path(book_dir, chapter)
    if os.path.exists(path):
        raise ValueError(f"事务文件已存在：{path}")
    if chapter > 1:
        previous = load_transaction(book_dir, chapter - 1)
        if not previous or previous.get("state") not in {"closed", "legacy_closed"}:
            raise ValueError(f"第 {chapter - 1} 章没有可验证的 closed/legacy_closed 事务")
        errors = verify_transaction(previous)
        if errors:
            raise ValueError("上一章事务无效：" + "; ".join(errors))
    txn = {"schemaVersion": "4.0", "chapter": chapter, "state": "", "events": []}
    _append_event(txn, "prepared")
    _atomic_json(path, txn)
    return txn


def mark_drafted(book_dir: str, chapter: int) -> dict:
    txn = load_transaction(book_dir, chapter)
    if not txn:
        raise ValueError("请先 prepare 当前章")
    draft = draft_path(book_dir, chapter)
    if not os.path.isfile(draft):
        raise ValueError(f"草稿不存在：{draft}")
    digest = file_sha256(draft)
    _append_event(txn, "drafted", draftSha256=digest)
    txn["draftSha256"] = digest
    _atomic_json(transaction_path(book_dir, chapter), txn)
    return txn


def mark_gated(book_dir: str, chapter: int) -> dict:
    from check_chapter_draft import check_draft

    txn = load_transaction(book_dir, chapter)
    if not txn:
        raise ValueError("缺少事务文件")
    draft = draft_path(book_dir, chapter)
    digest = file_sha256(draft)
    if txn.get("draftSha256") != digest:
        raise ValueError("草稿在 marked-drafted 后发生变化，请重新 mark-drafted")
    result = check_draft(book_dir, chapter, draft)
    report = result.to_dict()
    report["draftSha256"] = digest
    report["schemaVersion"] = "4.0"
    _atomic_json(gate_path(book_dir, chapter), report)
    if not result.ok:
        raise ValueError("机械门禁失败：" + "; ".join(result.errors))
    _append_event(txn, "gated", draftSha256=digest, gateReportSha256=file_sha256(gate_path(book_dir, chapter)))
    _atomic_json(transaction_path(book_dir, chapter), txn)
    return txn


def record_audit(book_dir: str, chapter: int, kind: str, report_path: str, status: str) -> dict:
    if kind not in {"informed", "cold"} or status not in {"pass", "fail"}:
        raise ValueError("审计 kind/status 不合法")
    txn = load_transaction(book_dir, chapter)
    if not txn or txn.get("state") != "gated":
        raise ValueError("只有 gated 状态可以登记审计")
    report = report_path if os.path.isabs(report_path) else os.path.join(book_dir, report_path)
    if os.path.commonpath((os.path.abspath(book_dir), os.path.abspath(report))) != os.path.abspath(book_dir):
        raise ValueError("审计报告必须位于书籍目录内")
    if not os.path.isfile(report):
        raise ValueError(f"审计报告不存在：{report}")
    draft = draft_path(book_dir, chapter)
    digest = file_sha256(draft)
    if txn.get("draftSha256") != digest:
        raise ValueError("审计前草稿已改变，机械门禁失效")
    path = audit_path(book_dir, chapter)
    data = _load(path) if os.path.isfile(path) else {
        "schemaVersion": "4.0", "chapter": chapter, "draftSha256": digest
    }
    data["informedAudit" if kind == "informed" else "coldRead"] = {
        "status": status,
        "reportPath": os.path.relpath(report, book_dir).replace(os.sep, "/"),
        "reportSha256": file_sha256(report),
    }
    _atomic_json(path, data)
    if {"informedAudit", "coldRead"}.issubset(data) and all(
        data[key]["status"] == "pass" for key in ("informedAudit", "coldRead")
    ):
        errors = validate_document(data, "chapter-audit.schema.json")
        if errors:
            raise ValueError("审计清单无效：" + "; ".join(errors))
        _append_event(txn, "audited", draftSha256=digest, auditManifestSha256=file_sha256(path))
        _atomic_json(transaction_path(book_dir, chapter), txn)
    return txn


def _verify_bound_reports(book_dir: str, chapter: int, txn: dict) -> None:
    """关闭前重新核验门禁、审计报告与 manifest，防止登记后被替换。"""
    gate = gate_path(book_dir, chapter)
    audit = audit_path(book_dir, chapter)
    if not os.path.isfile(gate) or not os.path.isfile(audit):
        raise ValueError("缺少门禁或审计 manifest")
    gated_event = next((event for event in reversed(txn["events"]) if event.get("to") == "gated"), None)
    audited_event = next((event for event in reversed(txn["events"]) if event.get("to") == "audited"), None)
    if not gated_event or gated_event.get("gateReportSha256") != file_sha256(gate):
        raise ValueError("机械门禁报告在登记后发生变化")
    if not audited_event or audited_event.get("auditManifestSha256") != file_sha256(audit):
        raise ValueError("审计 manifest 在登记后发生变化")
    data = _load(audit)
    errors = validate_document(data, "chapter-audit.schema.json")
    if errors:
        raise ValueError("审计 manifest 无效：" + "; ".join(errors))
    for key in ("informedAudit", "coldRead"):
        item = data[key]
        report = safe_join(book_dir, item["reportPath"])
        if item.get("status") != "pass" or not os.path.isfile(report):
            raise ValueError(f"{key} 报告缺失或未通过")
        if item.get("reportSha256") != file_sha256(report):
            raise ValueError(f"{key} 报告在登记后发生变化")


def find_final(book_dir: str, chapter: int) -> Optional[str]:
    import glob
    matches = sorted(glob.glob(os.path.join(book_dir, "chapters", f"{chapter:04d}_*.md")))
    return matches[0] if len(matches) == 1 else None


def close_transaction(book_dir: str, chapter: int) -> dict:
    txn = load_transaction(book_dir, chapter)
    if not txn or txn.get("state") != "audited":
        raise ValueError("只有 audited 状态可以封板")
    draft = draft_path(book_dir, chapter)
    digest = file_sha256(draft)
    if txn.get("draftSha256") != digest:
        raise ValueError("审计后草稿发生变化，必须重新门禁和审计")
    _verify_bound_reports(book_dir, chapter, txn)
    final = find_final(book_dir, chapter)
    if not final:
        raise ValueError("正式章节不存在或同章存在多个文件")
    final_digest = file_sha256(final)
    if final_digest != digest:
        raise ValueError("正式章节与已审计草稿字节不一致")
    from snapshot_book import verify_snapshot
    snapshot = verify_snapshot(book_dir, chapter)
    if not snapshot.get("ok"):
        raise ValueError("缺少有效章末快照，不能封板：" + snapshot.get("error", str(snapshot)))
    from validate_book import validate
    validation = validate(book_dir)
    if validation.errors:
        raise ValueError("全书验证失败，不能封板：" + "; ".join(validation.errors))
    _append_event(txn, "closed", draftSha256=digest, finalSha256=final_digest)
    txn["finalSha256"] = final_digest
    _atomic_json(transaction_path(book_dir, chapter), txn)
    return txn


def reopen(book_dir: str, chapter: int) -> dict:
    txn = load_transaction(book_dir, chapter)
    if not txn:
        raise ValueError("缺少事务文件")
    prior_state = txn.get("state", "")
    _append_event(txn, "reopened", previousFinalSha256=txn.get("finalSha256", ""))
    marker = txn["events"][-1]["eventHash"].split(":", 1)[-1]
    _supersede(gate_path(book_dir, chapter), marker)
    _supersede(audit_path(book_dir, chapter), marker)
    txn.pop("draftSha256", None)
    txn.pop("finalSha256", None)
    txn["events"][-1]["invalidatedState"] = prior_state
    # 添加细节后重算当前事件哈希，保持事件链可验证。
    txn["events"][-1].pop("eventHash", None)
    txn["events"][-1]["eventHash"] = _event_hash(txn["events"][-1])
    _atomic_json(transaction_path(book_dir, chapter), txn)
    return txn


def main() -> None:
    parser = argparse.ArgumentParser(description="Dragon Writer 章节事务状态机")
    parser.add_argument("book_dir")
    parser.add_argument("--chapter", type=int, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "mark-drafted", "gate", "close", "reopen", "verify"):
        sub.add_parser(name)
    audit = sub.add_parser("record-audit")
    audit.add_argument("--kind", choices=["informed", "cold"], required=True)
    audit.add_argument("--report", required=True)
    audit.add_argument("--status", choices=["pass", "fail"], required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = create_prepared(args.book_dir, args.chapter)
        elif args.command == "mark-drafted":
            result = mark_drafted(args.book_dir, args.chapter)
        elif args.command == "gate":
            result = mark_gated(args.book_dir, args.chapter)
        elif args.command == "record-audit":
            result = record_audit(args.book_dir, args.chapter, args.kind, args.report, args.status)
        elif args.command == "close":
            result = close_transaction(args.book_dir, args.chapter)
        elif args.command == "reopen":
            result = reopen(args.book_dir, args.chapter)
        else:
            result = load_transaction(args.book_dir, args.chapter)
            errors = verify_transaction(result or {})
            if errors:
                raise ValueError("; ".join(errors))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
