#!/usr/bin/env python3
"""哈希绑定的章节事务状态机。

状态只能经本脚本推进；事件使用前一事件哈希形成可验证链。文学审计报告仍是
Markdown，本文件只保存报告路径、哈希和通过状态。
"""

import argparse
import glob
import hashlib
import json
import os
import re
import sys
from typing import Optional

from _contract import file_sha256, now_iso, safe_join
from _schema import validate_document


TRANSITIONS = {
    "": {"prepared", "imported_closed", "legacy_closed"},
    "prepared": {"drafted"},
    "reopened": {"drafted"},
    "drafted": {"gated", "reopened"},
    "gated": {"audited", "reopened"},
    "audited": {"closed", "reopened"},
    "closed": {"reopened"},
    "legacy_closed": {"reopened"},
    "imported_closed": {"reopened"},
}


def transaction_path(book_dir: str, chapter: int) -> str:
    return os.path.join(book_dir, "story", "runtime", f"chapter-{chapter:04d}.transaction.json")


def audit_path(book_dir: str, chapter: int) -> str:
    return os.path.join(book_dir, "story", "runtime", f"chapter-{chapter:04d}.audit.json")


def gate_path(book_dir: str, chapter: int) -> str:
    return os.path.join(book_dir, "story", "runtime", f"chapter-{chapter:04d}.gate.json")


def overlap_path(book_dir: str, chapter: int) -> str:
    return os.path.join(book_dir, "story", "runtime", f"chapter-{chapter:04d}.overlap.json")


def intent_path(book_dir: str, chapter: int) -> str:
    return os.path.join(book_dir, "story", "runtime", f"chapter-{chapter:04d}.intent.json")


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
    if not os.path.exists(path):
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


def _json_hash(data: dict) -> str:
    body = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _book_contract_hash(book_dir: str) -> str:
    path = os.path.join(book_dir, "book.json")
    data = _load(path)
    keys = (
        "chapterWordCount", "chapterMinChars", "chapterTargetChars",
        "chapterMaxChars", "chapterLengthGateFromChapter",
    )
    return _json_hash({key: data.get(key) for key in keys})


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


def verify_transaction(txn: dict, expected_chapter: Optional[int] = None) -> list:
    errors = validate_document(txn, "chapter-transaction.schema.json")
    if expected_chapter is not None and txn.get("chapter") != expected_chapter:
        errors.append(f"事务章号 {txn.get('chapter')} 与文件/请求章号 {expected_chapter} 不一致")
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


def _require_transaction(book_dir: str, chapter: int, states) -> dict:
    txn = load_transaction(book_dir, chapter)
    if not txn:
        raise ValueError("缺少事务文件")
    errors = verify_transaction(txn, chapter)
    if errors:
        raise ValueError("事务无效：" + "; ".join(errors))
    allowed = {states} if isinstance(states, str) else set(states)
    if txn.get("state") not in allowed:
        raise ValueError(f"事务状态必须为 {sorted(allowed)}，当前 {txn.get('state')}")
    return txn


def _transaction_files(book_dir: str):
    runtime = os.path.join(book_dir, "story", "runtime")
    for path in sorted(glob.glob(os.path.join(runtime, "chapter-*.transaction.json"))):
        match = re.search(r"chapter-(\d+)\.transaction\.json$", path)
        if match:
            yield int(match.group(1)), path


def _verify_gate_bindings(book_dir: str, chapter: int, txn: dict, check_current_contract: bool = True) -> None:
    draft = draft_path(book_dir, chapter)
    intent = intent_path(book_dir, chapter)
    gate = gate_path(book_dir, chapter)
    overlap = overlap_path(book_dir, chapter)
    event = next((row for row in reversed(txn.get("events", [])) if row.get("to") == "gated"), None)
    if not event:
        raise ValueError("事务缺少 gated 事件")
    checks = (
        (draft, txn.get("draftSha256"), "草稿"),
        (intent, event.get("intentSha256"), "章节 intent"),
        (gate, event.get("gateReportSha256"), "机械门禁报告"),
        (overlap, event.get("overlapReportSha256"), "跨章重复报告"),
    )
    for path, expected, label in checks:
        if not os.path.isfile(path) or not expected or file_sha256(path) != expected:
            suffix = "哈希缺失或在登记后发生变化" if label == "草稿" else "缺失或在登记后发生变化"
            raise ValueError(f"{label}{suffix}")
    if check_current_contract and event.get("bookContractSha256") != _book_contract_hash(book_dir):
        raise ValueError("书级字数契约在门禁后发生变化")
    gate_data = _load(gate)
    overlap_data = _load(overlap)
    if gate_data.get("draftSha256") != txn.get("draftSha256") or gate_data.get("intentSha256") != event.get("intentSha256"):
        raise ValueError("机械门禁报告没有绑定当前草稿与 intent")
    if overlap_data.get("status") != "pass" or overlap_data.get("draftSha256") != txn.get("draftSha256"):
        raise ValueError("跨章重复报告未通过或未绑定当前草稿")


def verify_closed_bindings(book_dir: str, chapter: int, txn: Optional[dict] = None) -> list:
    """验证可解锁下一章的完整封板；导入章只接受 manifest 绑定的来源哈希。"""
    txn = txn or load_transaction(book_dir, chapter)
    errors = verify_transaction(txn or {}, chapter)
    if errors:
        return errors
    state = txn.get("state")
    if state in {"legacy_closed", "imported_closed"}:
        rel = txn.get("legacySourcePath", "")
        expected = txn.get("legacySourceSha256", "")
        try:
            source = safe_join(book_dir, rel)
        except ValueError as exc:
            return [str(exc)]
        if not rel or not expected or not os.path.isfile(source) or file_sha256(source) != expected:
            return ["导入封板缺少有效的正式正文来源绑定"]
        manifest_path = os.path.join(book_dir, "story", "import-manifest.json")
        if not os.path.isfile(manifest_path):
            return ["导入封板缺少 import manifest"]
        manifest = _load(manifest_path)
        schema_errors = validate_document(manifest, "import-manifest.schema.json")
        if schema_errors:
            return ["import manifest 无效：" + "; ".join(schema_errors)]
        rows = [row for row in manifest.get("files", []) if row.get("chapter") == chapter]
        if len(rows) != 1 or rows[0].get("path") != rel or rows[0].get("sha256") != expected:
            return ["导入封板与 import manifest 不一致"]
        first, last = manifest.get("firstChapter"), manifest.get("lastChapter")
        listed = sorted(row.get("chapter") for row in manifest.get("files", []))
        if not isinstance(first, int) or not isinstance(last, int) or listed != list(range(first, last + 1)):
            return ["import manifest 未连续覆盖完整导入区间"]
        book_path = os.path.join(book_dir, "book.json")
        if not os.path.isfile(book_path) or _load(book_path).get("chapterLengthGateFromChapter") != last + 1:
            return ["book.json 的长度门禁起始章必须紧接 import manifest 末章"]
        index_path = os.path.join(book_dir, "chapters", "index.json")
        if not os.path.isfile(index_path):
            return ["导入封板缺少章节索引"]
        index = _load(index_path)
        entries = index.get("chapters", []) if isinstance(index, dict) else index
        for row in manifest.get("files", []):
            number = row.get("chapter")
            row_rel = row.get("path", "")
            matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("number") == number]
            if len(matches) != 1 or f"chapters/{matches[0].get('file', '')}" != row_rel:
                return [f"导入章 {number} 不是索引中的唯一正式稿"]
            try:
                row_source = safe_join(book_dir, row_rel)
            except ValueError as exc:
                return [str(exc)]
            if not os.path.isfile(row_source) or file_sha256(row_source) != row.get("sha256"):
                return [f"导入章 {number} 与 import manifest 哈希不一致"]
        return []
    if state != "closed":
        return [f"事务尚未封板：{state}"]
    try:
        _verify_bound_reports(book_dir, chapter, txn, check_current_contract=False)
        from snapshot_book import verify_snapshot
        snapshot_check = verify_snapshot(book_dir, chapter)
        if not snapshot_check.get("ok"):
            raise ValueError(snapshot_check.get("error") or "章末快照校验失败")
        final = find_final(book_dir, chapter)
        if not final or txn.get("finalSha256") != file_sha256(final):
            raise ValueError("正式正文与 closed 事务哈希不一致")
        closed = next((row for row in reversed(txn.get("events", [])) if row.get("to") == "closed"), {})
        snapshot_manifest = os.path.join(book_dir, "story", "snapshots", f"{chapter:04d}", "manifest.json")
        snapshot_root = os.path.dirname(snapshot_manifest)
        ledger = os.path.join(snapshot_root, "story", "current_state.md")
        index = os.path.join(snapshot_root, "chapters", "index.json")
        for path, key, label in (
            (snapshot_manifest, "snapshotManifestSha256", "章末快照 manifest"),
            (ledger, "stateLedgerSha256", "状态账本"),
            (index, "indexSha256", "章节索引"),
        ):
            expected = closed.get(key, "")
            if not os.path.isfile(path) or not expected or file_sha256(path) != expected:
                raise ValueError(f"{label}与 closed 事件绑定不一致")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]
    return []


def create_prepared(book_dir: str, chapter: int) -> dict:
    if chapter < 1:
        raise ValueError("章节号必须大于 0")
    path = transaction_path(book_dir, chapter)
    if os.path.exists(path):
        raise ValueError(f"事务文件已存在：{path}")
    seen = []
    for file_chapter, txn_path in _transaction_files(book_dir):
        txn = _load(txn_path)
        errors = verify_transaction(txn, file_chapter)
        if errors:
            raise ValueError(f"既有事务 chapter-{file_chapter:04d} 无效：" + "; ".join(errors))
        if txn.get("state") not in {"closed", "legacy_closed", "imported_closed"}:
            raise ValueError(f"既有事务 chapter-{file_chapter:04d} 尚未封板")
        # 紧邻上一章在下方用更明确的错误消息验证；更早的封板也必须逐章复验。
        if file_chapter != chapter - 1:
            binding_errors = verify_closed_bindings(book_dir, file_chapter, txn)
            if binding_errors:
                raise ValueError(f"既有事务 chapter-{file_chapter:04d} 封板绑定无效：" + "; ".join(binding_errors))
        seen.append(file_chapter)
    finals = []
    for final_path in glob.glob(os.path.join(book_dir, "chapters", "*.md")):
        match = re.match(r"^(\d+)_", os.path.basename(final_path))
        if match:
            finals.append(int(match.group(1)))
    if any(number >= chapter for number in finals):
        raise ValueError("目标章或后续正式正文已存在；请先迁移或回滚，不能直接 prepare")
    if any(number >= chapter for number in seen):
        raise ValueError("只能准备最大既有事务之后的下一章")
    if seen and max(seen) != chapter - 1:
        raise ValueError("事务章号不连续，只能准备当前最后一章的下一章")
    previous_hash = ""
    if chapter > 1:
        previous = load_transaction(book_dir, chapter - 1)
        errors = verify_closed_bindings(book_dir, chapter - 1, previous)
        if errors:
            raise ValueError("上一章没有完整封板：" + "; ".join(errors))
        if previous.get("state") in {"legacy_closed", "imported_closed"}:
            manifest = _load(os.path.join(book_dir, "story", "import-manifest.json"))
            if manifest.get("lastChapter") != chapter - 1:
                raise ValueError("只能从 import manifest 的最后一个连续导入章之后续写")
        previous_hash = previous["events"][-1]["eventHash"]
    txn = {"schemaVersion": "4.1", "chapter": chapter, "state": "", "events": []}
    _append_event(txn, "prepared", previousChapterClosedEventHash=previous_hash)
    _atomic_json(path, txn)
    return txn


def mark_drafted(book_dir: str, chapter: int) -> dict:
    txn = _require_transaction(book_dir, chapter, {"prepared", "reopened"})
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

    txn = _require_transaction(book_dir, chapter, "drafted")
    draft = draft_path(book_dir, chapter)
    if not os.path.isfile(draft):
        raise ValueError("草稿不存在")
    digest = file_sha256(draft)
    if txn.get("draftSha256") != digest:
        raise ValueError("草稿在 marked-drafted 后发生变化，请重新 mark-drafted")
    result = check_draft(book_dir, chapter, draft)
    intent = intent_path(book_dir, chapter)
    if not os.path.isfile(intent):
        raise ValueError("结构化 intent 不存在，不能进入 4.x 门禁")
    intent_digest = file_sha256(intent)
    from check_chapter_overlap import analyze_draft
    overlap_report = analyze_draft(book_dir, chapter, draft, window=10)
    overlap_report.update({
        "schemaVersion": "4.1", "draftSha256": digest, "intentSha256": intent_digest,
    })
    report = result.to_dict()
    report["draftSha256"] = digest
    report["intentSha256"] = intent_digest
    report["bookContractSha256"] = _book_contract_hash(book_dir)
    report["schemaVersion"] = "4.1"
    _atomic_json(gate_path(book_dir, chapter), report)
    _atomic_json(overlap_path(book_dir, chapter), overlap_report)
    if not result.ok:
        raise ValueError("机械门禁失败：" + "; ".join(result.errors))
    if overlap_report.get("status") != "pass":
        raise ValueError("跨章重复门禁失败")
    _append_event(
        txn, "gated", draftSha256=digest, intentSha256=intent_digest,
        bookContractSha256=_book_contract_hash(book_dir),
        gateReportSha256=file_sha256(gate_path(book_dir, chapter)),
        overlapReportSha256=file_sha256(overlap_path(book_dir, chapter)),
    )
    _atomic_json(transaction_path(book_dir, chapter), txn)
    return txn


def record_audit(
    book_dir: str, chapter: int, kind: str, report_path: str, status: str,
    packet_manifest_path: Optional[str] = None,
) -> dict:
    if kind not in {"informed", "cold"} or status not in {"pass", "fail"}:
        raise ValueError("审计 kind/status 不合法")
    txn = _require_transaction(book_dir, chapter, "gated")
    _verify_gate_bindings(book_dir, chapter, txn)
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
    gated_event = next(row for row in reversed(txn["events"]) if row.get("to") == "gated")
    data = _load(path) if os.path.isfile(path) else {
        "schemaVersion": "4.1", "chapter": chapter, "draftSha256": digest,
        "intentSha256": gated_event["intentSha256"],
        "gateReportSha256": gated_event["gateReportSha256"],
        "overlapReportSha256": gated_event["overlapReportSha256"],
    }
    for key, expected in (
        ("draftSha256", digest), ("intentSha256", gated_event["intentSha256"]),
        ("gateReportSha256", gated_event["gateReportSha256"]),
        ("overlapReportSha256", gated_event["overlapReportSha256"]),
    ):
        if data.get(key) != expected:
            raise ValueError(f"既有审计 manifest 的 {key} 已失效")
    audit_item = {
        "status": status,
        "reportPath": os.path.relpath(report, book_dir).replace(os.sep, "/"),
        "reportSha256": file_sha256(report),
    }
    if kind == "cold":
        if not packet_manifest_path:
            raise ValueError("登记冷读必须提供纯正文包的 packet manifest")
        packet_manifest = (
            packet_manifest_path if os.path.isabs(packet_manifest_path)
            else os.path.join(book_dir, packet_manifest_path)
        )
        if os.path.commonpath((os.path.abspath(book_dir), os.path.abspath(packet_manifest))) != os.path.abspath(book_dir):
            raise ValueError("冷读 packet manifest 必须位于书籍目录内")
        if not os.path.isfile(packet_manifest):
            raise ValueError("冷读 packet manifest 不存在")
        packet_data = _load(packet_manifest)
        from build_cold_read_packet import verify_packet_manifest
        packet_errors = verify_packet_manifest(book_dir, packet_data, expected_draft_chapter=chapter)
        if packet_errors:
            raise ValueError("冷读 packet manifest 无效：" + "; ".join(packet_errors))
        audit_item.update({
            "packetManifestPath": os.path.relpath(packet_manifest, book_dir).replace(os.sep, "/"),
            "packetManifestSha256": file_sha256(packet_manifest),
            "packetSha256": packet_data.get("packetSha256", ""),
        })
    data["informedAudit" if kind == "informed" else "coldRead"] = audit_item
    _atomic_json(path, data)
    if {"informedAudit", "coldRead"}.issubset(data) and all(
        data[key]["status"] == "pass" for key in ("informedAudit", "coldRead")
    ):
        errors = validate_document(data, "chapter-audit.schema.json")
        if errors:
            raise ValueError("审计清单无效：" + "; ".join(errors))
        for key in ("informedAudit", "coldRead"):
            item = data[key]
            bound_report = safe_join(book_dir, item["reportPath"])
            if not os.path.isfile(bound_report) or item["reportSha256"] != file_sha256(bound_report):
                raise ValueError(f"{key} 报告在进入 audited 前已失效")
        _append_event(txn, "audited", draftSha256=digest, auditManifestSha256=file_sha256(path))
        _atomic_json(transaction_path(book_dir, chapter), txn)
    return txn


def _verify_bound_reports(
    book_dir: str, chapter: int, txn: dict, check_current_contract: bool = True
) -> None:
    """关闭前重新核验门禁、审计报告与 manifest，防止登记后被替换。"""
    _verify_gate_bindings(book_dir, chapter, txn, check_current_contract=check_current_contract)
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
        if key == "coldRead":
            manifest = safe_join(book_dir, item.get("packetManifestPath", ""))
            if not os.path.isfile(manifest) or item.get("packetManifestSha256") != file_sha256(manifest):
                raise ValueError("冷读稿源 manifest 缺失或在登记后发生变化")
            from build_cold_read_packet import verify_packet_manifest
            packet_errors = verify_packet_manifest(book_dir, _load(manifest), expected_draft_chapter=chapter)
            if packet_errors:
                raise ValueError("冷读稿源在封板前失效：" + "; ".join(packet_errors))


def find_final(book_dir: str, chapter: int) -> Optional[str]:
    import glob
    matches = sorted(glob.glob(os.path.join(book_dir, "chapters", f"{chapter:04d}_*.md")))
    return matches[0] if len(matches) == 1 else None


def close_transaction(book_dir: str, chapter: int) -> dict:
    txn = _require_transaction(book_dir, chapter, "audited")
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
    snapshot = verify_snapshot(book_dir, chapter, compare_current=True)
    if not snapshot.get("ok"):
        raise ValueError("缺少有效章末快照，不能封板：" + snapshot.get("error", str(snapshot)))
    from validate_book import validate
    validation = validate(book_dir)
    if validation.errors:
        raise ValueError("全书验证失败，不能封板：" + "; ".join(validation.errors))
    gated_event = next(row for row in reversed(txn["events"]) if row.get("to") == "gated")
    audited_event = next(row for row in reversed(txn["events"]) if row.get("to") == "audited")
    snapshot_manifest = os.path.join(book_dir, "story", "snapshots", f"{chapter:04d}", "manifest.json")
    ledger = os.path.join(book_dir, "story", "current_state.md")
    index = os.path.join(book_dir, "chapters", "index.json")
    _append_event(
        txn, "closed", draftSha256=digest, finalSha256=final_digest,
        intentSha256=gated_event["intentSha256"],
        bookContractSha256=gated_event["bookContractSha256"],
        gateReportSha256=gated_event["gateReportSha256"],
        overlapReportSha256=gated_event["overlapReportSha256"],
        auditManifestSha256=audited_event["auditManifestSha256"],
        snapshotManifestSha256=file_sha256(snapshot_manifest),
        stateLedgerSha256=file_sha256(ledger) if os.path.isfile(ledger) else "",
        indexSha256=file_sha256(index) if os.path.isfile(index) else "",
    )
    txn["finalSha256"] = final_digest
    _atomic_json(transaction_path(book_dir, chapter), txn)
    return txn


def reopen(book_dir: str, chapter: int) -> dict:
    txn = _require_transaction(
        book_dir, chapter, {"drafted", "gated", "audited", "closed", "legacy_closed", "imported_closed"}
    )
    later = [number for number, _ in _transaction_files(book_dir) if number > chapter]
    later_finals = []
    for path in glob.glob(os.path.join(book_dir, "chapters", "*.md")):
        match = re.match(r"^(\d+)_", os.path.basename(path))
        if match and int(match.group(1)) > chapter:
            later_finals.append(path)
    if later or later_finals:
        raise ValueError("存在后续章节或事务，禁止直接 reopen；请先执行级联回滚归档")
    prior_state = txn.get("state", "")
    _append_event(txn, "reopened", previousFinalSha256=txn.get("finalSha256", ""))
    marker = txn["events"][-1]["eventHash"].split(":", 1)[-1]
    txn.pop("draftSha256", None)
    txn.pop("finalSha256", None)
    txn["events"][-1]["invalidatedState"] = prior_state
    # 添加细节后重算当前事件哈希，保持事件链可验证。
    txn["events"][-1].pop("eventHash", None)
    txn["events"][-1]["eventHash"] = _event_hash(txn["events"][-1])
    _atomic_json(transaction_path(book_dir, chapter), txn)
    _supersede(gate_path(book_dir, chapter), marker)
    _supersede(overlap_path(book_dir, chapter), marker)
    _supersede(audit_path(book_dir, chapter), marker)
    _supersede(os.path.join(book_dir, "story", "snapshots", f"{chapter:04d}"), marker)
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
    audit.add_argument("--packet-manifest", help="冷读时必填：build_cold_read_packet 生成的稿源 manifest")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = create_prepared(args.book_dir, args.chapter)
        elif args.command == "mark-drafted":
            result = mark_drafted(args.book_dir, args.chapter)
        elif args.command == "gate":
            result = mark_gated(args.book_dir, args.chapter)
        elif args.command == "record-audit":
            result = record_audit(
                args.book_dir, args.chapter, args.kind, args.report, args.status,
                args.packet_manifest,
            )
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
