#!/usr/bin/env python3
"""4.0 结构化事实源、哈希事务与稿源隔离的攻击性测试。"""

import json
import os
import sys

import pytest


SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from _contract import file_sha256  # noqa: E402
from build_cold_read_packet import build_explicit_packet  # noqa: E402
from chapter_txn import (  # noqa: E402
    close_transaction,
    create_prepared,
    mark_drafted,
    mark_gated,
    record_audit,
    reopen,
    verify_transaction,
)
from check_chapter_draft import check_draft  # noqa: E402
from init_book import create_book  # noqa: E402
from migrate_3_13_to_4_0 import migrate  # noqa: E402
from rebuild_index import rebuild  # noqa: E402
from render_intent import render  # noqa: E402
from snapshot_book import create_snapshot  # noqa: E402
from validate_book import (  # noqa: E402
    ValidationResult,
    check_structured_runtime,
    check_word_count_consistency,
)


def _structured_book(tmp_path):
    book = tmp_path / "book"
    (book / "chapters").mkdir(parents=True)
    (book / "story" / "runtime").mkdir(parents=True)
    (book / "book.json").write_text(json.dumps({
        "chapterWordCount": 40,
        "chapterMinChars": 40,
        "chapterTargetChars": 50,
        "chapterMaxChars": 200,
        "chapterLengthGateFromChapter": 1,
    }), encoding="utf-8")
    draft = book / "story" / "runtime" / "chapter-0001.draft.md"
    draft.write_text("# 测试\n\n他推开木门，停了一瞬，仍旧跨进屋内。" * 5 + "\n", encoding="utf-8")
    digest = file_sha256(str(draft))
    intent = {
        "schemaVersion": "4.0",
        "chapter": 1,
        "dramaticQuestion": "他是否进入屋内",
        "pov": "第三人称限制视角：他",
        "plannedTargetChars": 50,
        "timeArchitecture": {
            "start": "夜晚，门外",
            "end": "片刻后，屋内",
            "elapsed": "约一分钟",
            "cutReason": "跨门选择完成并产生新风险",
        },
        "knowledgeDeltas": [],
        "relationshipDeltas": [],
        "knowledgePermissions": [{
            "character": "他",
            "knownAtStart": ["屋内有异常声响"],
            "acquiredThisChapter": [],
            "stillUnknown": ["异常声响的来源"],
        }],
        "relationshipPermissions": [],
        "noveltyDelta": "第一次主动进入未知空间",
        "sceneBeats": [{
            "beatId": "beat-01",
            "mode": "scene",
            "dramaticFunction": "迫使人物作出选择",
            "goalOrPressure": "必须确认屋内动静",
            "conflictOrTurn": "明知危险仍要跨门",
            "requiredResult": "人物进入屋内",
            "timeSpaceAnchor": "夜晚，木门外到屋内",
            "descriptionObligation": "用停顿和跨门动作外化犹豫",
        }],
        "evidence": [{
            "beatId": "beat-01",
            "paragraphStart": 2,
            "paragraphEnd": 2,
            "quote": "他推开木门",
            "draftSha256": digest,
            "status": "pass",
        }],
    }
    source = book / "story" / "runtime" / "chapter-0001.intent.json"
    source.write_text(json.dumps(intent, ensure_ascii=False), encoding="utf-8")
    render(str(source), str(source.with_suffix(".md")))
    return book, draft, source


def test_transaction_rejects_jump_and_hash_tampering(tmp_path):
    book, _, _ = _structured_book(tmp_path)
    txn = create_prepared(str(book), 1)
    txn["state"] = "closed"
    errors = verify_transaction(txn)
    assert any("末状态" in message for message in errors)
    txn = create_prepared(str(tmp_path / "other"), 1)
    txn["events"][0]["to"] = "closed"
    errors = verify_transaction(txn)
    assert any("eventHash 不匹配" in message for message in errors)
    assert any("非法跃迁" in message for message in errors)


def test_json_intent_binds_evidence_to_exact_draft_and_paragraph(tmp_path):
    book, draft, source = _structured_book(tmp_path)
    create_prepared(str(book), 1)
    mark_drafted(str(book), 1)
    assert check_draft(str(book), 1).ok
    data = json.loads(source.read_text(encoding="utf-8"))
    data["evidence"][0]["paragraphStart"] = 1
    data["evidence"][0]["paragraphEnd"] = 1
    source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    result = check_draft(str(book), 1)
    assert any("限定所填段落范围" in message for message in result.errors)
    data["evidence"][0]["paragraphStart"] = 2
    data["evidence"][0]["paragraphEnd"] = 2
    data["dramaticQuestion"] = "<待填>"
    source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    result = check_draft(str(book), 1)
    assert any("占位内容" in message for message in result.errors)


def test_generated_markdown_conflict_is_detected_as_stale_view(tmp_path):
    book, _, source = _structured_book(tmp_path)
    create_prepared(str(book), 1)
    data = json.loads(source.read_text(encoding="utf-8"))
    data["dramaticQuestion"] = "修改后的权威戏剧问题"
    source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    result = ValidationResult()
    check_structured_runtime(str(book), result)
    assert any("生成视图已过期" in message for message in result.errors)


def test_close_rejects_audit_report_changed_after_registration(tmp_path):
    book, draft, _ = _structured_book(tmp_path)
    create_prepared(str(book), 1)
    mark_drafted(str(book), 1)
    mark_gated(str(book), 1)
    informed = book / "story" / "runtime" / "chapter-0001.informed.md"
    cold = book / "story" / "runtime" / "chapter-0001.cold.md"
    informed.write_text("PASS：知情连续性审计", encoding="utf-8")
    cold.write_text("PASS：无背景冷读", encoding="utf-8")
    record_audit(str(book), 1, "informed", str(informed), "pass")
    record_audit(str(book), 1, "cold", str(cold), "pass")
    (book / "chapters" / "0001_测试.md").write_bytes(draft.read_bytes())
    cold.write_text("报告登记后被替换", encoding="utf-8")
    with pytest.raises(ValueError, match="coldRead 报告在登记后发生变化"):
        close_transaction(str(book), 1)


def test_reopen_invalidates_old_gate_and_audit_manifests(tmp_path):
    book, _, _ = _structured_book(tmp_path)
    create_prepared(str(book), 1)
    mark_drafted(str(book), 1)
    mark_gated(str(book), 1)
    informed = book / "story" / "runtime" / "chapter-0001.informed.md"
    cold = book / "story" / "runtime" / "chapter-0001.cold.md"
    informed.write_text("pass", encoding="utf-8")
    cold.write_text("pass", encoding="utf-8")
    record_audit(str(book), 1, "informed", str(informed), "pass")
    record_audit(str(book), 1, "cold", str(cold), "pass")
    txn = reopen(str(book), 1)
    assert txn["state"] == "reopened"
    assert not (book / "story" / "runtime" / "chapter-0001.gate.json").exists()
    assert not (book / "story" / "runtime" / "chapter-0001.audit.json").exists()
    superseded = list((book / "story" / "runtime").glob("*.superseded-*"))
    assert len(superseded) == 2
    assert not verify_transaction(txn)


def test_happy_path_closes_only_after_snapshot_and_full_validation(tmp_path):
    source_book, source_draft, source_intent = _structured_book(tmp_path / "source")
    book = __import__("pathlib").Path(create_book(
        "封板测试", "任意混合题材", str(tmp_path / "project"), chapter_word_count=40,
        chapter_target_chars=50, chapter_max_chars=200,
    ))
    runtime = book / "story" / "runtime"
    draft = runtime / "chapter-0001.draft.md"
    draft.write_bytes(source_draft.read_bytes())
    intent = runtime / "chapter-0001.intent.json"
    intent.write_bytes(source_intent.read_bytes())
    render(str(intent), str(intent.with_suffix(".md")))
    create_prepared(str(book), 1)
    mark_drafted(str(book), 1)
    mark_gated(str(book), 1)
    informed = runtime / "chapter-0001.informed.md"
    cold = runtime / "chapter-0001.cold.md"
    informed.write_text("pass", encoding="utf-8")
    cold.write_text("pass", encoding="utf-8")
    record_audit(str(book), 1, "informed", str(informed), "pass")
    record_audit(str(book), 1, "cold", str(cold), "pass")
    (book / "chapters" / "0001_测试.md").write_bytes(draft.read_bytes())
    assert rebuild(str(book))["ok"]
    with pytest.raises(ValueError, match="章末快照"):
        close_transaction(str(book), 1)
    assert create_snapshot(str(book), 1)["ok"]
    txn = close_transaction(str(book), 1)
    assert txn["state"] == "closed"
    assert txn["draftSha256"] == txn["finalSha256"]


def test_explicit_cold_packet_never_prefers_stale_draft(tmp_path):
    book = tmp_path / "book"
    (book / "chapters").mkdir(parents=True)
    (book / "story" / "runtime").mkdir(parents=True)
    (book / "chapters" / "0001_正式.md").write_text("正式版本唯一内容", encoding="utf-8")
    (book / "story" / "runtime" / "chapter-0001.draft.md").write_text(
        "过期草稿不应出现", encoding="utf-8"
    )
    packet, manifest = build_explicit_packet(str(book), final_chapters=[1])
    assert "正式版本唯一内容" in packet
    assert "过期草稿不应出现" not in packet
    assert manifest["sources"][0]["role"] == "final"
    with pytest.raises(ValueError, match="同一章不能同时"):
        build_explicit_packet(str(book), final_chapters=[1], draft_chapter=1)


def test_draft_cold_packet_requires_informed_audit_and_frozen_hash(tmp_path):
    book, draft, _ = _structured_book(tmp_path)
    create_prepared(str(book), 1)
    mark_drafted(str(book), 1)
    mark_gated(str(book), 1)
    with pytest.raises(ValueError, match="知情审计"):
        build_explicit_packet(str(book), draft_chapter=1)
    informed = book / "story" / "runtime" / "chapter-0001.informed.md"
    informed.write_text("pass", encoding="utf-8")
    record_audit(str(book), 1, "informed", str(informed), "pass")
    packet, manifest = build_explicit_packet(str(book), draft_chapter=1)
    assert "他推开木门" in packet
    assert manifest["sources"][0]["sha256"] == file_sha256(str(draft))
    draft.write_text(draft.read_text(encoding="utf-8") + "篡改", encoding="utf-8")
    with pytest.raises(ValueError, match="草稿哈希"):
        build_explicit_packet(str(book), draft_chapter=1)


def test_new_book_template_contains_no_demo_story(tmp_path):
    book = create_book("真正空白", "不限定题材", str(tmp_path), chapter_word_count=50)
    chapter_files = list((__import__("pathlib").Path(book) / "chapters").glob("*.md"))
    index = json.loads(open(os.path.join(book, "chapters", "index.json"), encoding="utf-8").read())
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (__import__("pathlib").Path(book) / "story").rglob("*.md")
    )
    assert chapter_files == []
    assert index["chapters"] == []
    assert "陆恒" not in all_text and "苏霜" not in all_text


def test_import_exception_is_bound_to_exact_files(tmp_path):
    book = tmp_path / "book"
    (book / "chapters").mkdir(parents=True)
    (book / "story").mkdir()
    chapter = book / "chapters" / "0001_导入.md"
    chapter.write_text("短历史稿", encoding="utf-8")
    (book / "chapters" / "index.json").write_text(json.dumps({"chapters": [{
        "number": 1, "file": chapter.name, "wordCount": 1
    }]}), encoding="utf-8")
    (book / "book.json").write_text(json.dumps({
        "chapterWordCount": 100,
        "chapterMinChars": 100,
        "chapterTargetChars": 100,
        "chapterMaxChars": 150,
        "chapterLengthGateFromChapter": 2,
    }), encoding="utf-8")
    manifest = {
        "schemaVersion": "4.0",
        "firstChapter": 1,
        "lastChapter": 1,
        "files": [{
            "chapter": 1,
            "path": "chapters/0001_导入.md",
            "sha256": file_sha256(str(chapter)),
        }],
    }
    (book / "story" / "import-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    result = ValidationResult()
    check_word_count_consistency(str(book), result)
    assert not result.errors
    chapter.write_text("历史稿被改了", encoding="utf-8")
    result = ValidationResult()
    check_word_count_consistency(str(book), result)
    assert any("哈希不匹配" in message for message in result.errors)


def test_migration_marks_legacy_closed_without_inventing_missing_intent(tmp_path):
    book = tmp_path / "book"
    runtime = book / "story" / "runtime"
    chapters = book / "chapters"
    runtime.mkdir(parents=True)
    chapters.mkdir()
    (chapters / "0001_旧章.md").write_text("# 旧章\n\n真实旧正文。", encoding="utf-8")
    legacy = runtime / "chapter-0001.intent.md"
    legacy.write_text(
        "# old\n\n- transaction_state: closed\n\n"
        "## Required Scene Beats\n\n"
        "| beat_id | mode | dramatic_function | goal_or_pressure | conflict_or_turn | required_result | time_space_anchor | description_obligation |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| b1 | scene | 推进 | 寻找 | 受阻 | 找到 | 室内 | 动作 |\n",
        encoding="utf-8",
    )
    warnings = migrate(str(book))
    txn = json.loads((runtime / "chapter-0001.transaction.json").read_text(encoding="utf-8"))
    assert txn["state"] == "legacy_closed"
    assert txn["legacyMigration"] is True
    assert not (runtime / "chapter-0001.intent.json").exists()
    assert any("不猜测历史计划" in warning or "缺少" in warning for warning in warnings)
    assert "transaction_state: closed" in legacy.read_text(encoding="utf-8")
