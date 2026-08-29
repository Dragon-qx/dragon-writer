#!/usr/bin/env python3
"""章节串行事务、硬门禁与无背景冷读包测试。"""

import json
import os
import sys


SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from build_cold_read_packet import build_explicit_packet  # noqa: E402
from chapter_txn import _append_event, _atomic_json  # noqa: E402
from _contract import file_sha256  # noqa: E402
from check_chapter_draft import check_draft, check_preflight  # noqa: E402
from init_book import create_book  # noqa: E402


def _book(tmp_path, minimum=80, target=100, maximum=180):
    (tmp_path / "chapters").mkdir()
    (tmp_path / "story" / "runtime").mkdir(parents=True)
    (tmp_path / "book.json").write_text(
        json.dumps(
            {
                "chapterWordCount": target,
                "chapterMinChars": minimum,
                "chapterTargetChars": target,
                "chapterMaxChars": maximum,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return tmp_path


def _intent(state="drafted", minimum=80, target=100, maximum=180, evidence_quote="他推开木门"):
    return f"""# Chapter Intent

## Chapter Transaction（章节事务，必填）
- transaction_state: {state}
- min_chars: {minimum}
- target_chars: {target}
- max_chars: {maximum}
- previous_chapter_state: closed

## Required Scene Beats（必要场景节点，必填）
| beat_id | mode | dramatic_function | goal_or_pressure | conflict_or_turn | required_result | time_space_anchor | description_obligation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| beat-01 | scene | 建立选择 | 主角要进屋 | 门后传来异响 | 主角仍然开门 | 夜晚 / 木屋门外 | 用动作呈现犹豫与空间关系 |

## Draft Evidence Map（草稿证据映射，起草后必填）
| beat_id | paragraph_refs | evidence_quote | status |
| --- | --- | --- | --- |
| beat-01 | P2 | {evidence_quote} | pass |
"""


def _write_chapter(book, chapter, body, intent=None, final=False):
    if final:
        path = book / "chapters" / f"{chapter:04d}_测试.md"
    else:
        path = book / "story" / "runtime" / f"chapter-{chapter:04d}.draft.md"
    path.write_text(f"# 测试\n\n{body}\n", encoding="utf-8")
    if intent is not None:
        (book / "story" / "runtime" / f"chapter-{chapter:04d}.intent.md").write_text(
            intent, encoding="utf-8"
        )


def test_draft_gate_passes_length_and_evidence(tmp_path):
    book = _book(tmp_path)
    body = "他推开木门，门轴发出一声轻响。" * 8
    _write_chapter(book, 1, body, _intent())
    result = check_draft(str(book), 1)
    assert result.ok, result.errors
    assert result.character_count >= 80


def test_draft_gate_blocks_short_chapter(tmp_path):
    book = _book(tmp_path, minimum=120, target=150, maximum=220)
    _write_chapter(book, 1, "他推开木门。", _intent(minimum=120, target=150, maximum=220))
    result = check_draft(str(book), 1)
    assert not result.ok
    assert any("字符数不足" in message for message in result.errors)


def test_draft_gate_blocks_unmatched_scene_evidence(tmp_path):
    book = _book(tmp_path)
    body = "他推开木门，门轴发出一声轻响。" * 8
    _write_chapter(book, 1, body, _intent(evidence_quote="正文里不存在的句子"))
    result = check_draft(str(book), 1)
    assert not result.ok
    assert any("evidence_quote 未在草稿正文命中" in message for message in result.errors)


def test_next_chapter_requires_previous_closed(tmp_path):
    book = _book(tmp_path)
    body = "他推开木门，门轴发出一声轻响。" * 8
    _write_chapter(book, 1, body, _intent(state="audited"))
    _write_chapter(book, 2, body, _intent(state="drafted"))
    result = check_draft(str(book), 2)
    assert not result.ok
    assert any("缺少结构化 transaction.json" in message for message in result.errors)


def test_preflight_blocks_creating_next_chapter_before_close(tmp_path):
    book = _book(tmp_path)
    body = "他推开木门，门轴发出一声轻响。" * 8
    _write_chapter(book, 1, body, _intent(state="audited"))
    result = check_preflight(str(book), 2)
    assert not result.ok
    assert any("缺少结构化 transaction.json" in message for message in result.errors)


def test_cold_read_packet_contains_only_prompt_and_manuscript(tmp_path):
    book = _book(tmp_path)
    book_json = json.loads((book / "book.json").read_text(encoding="utf-8"))
    book_json["chapterLengthGateFromChapter"] = 2
    (book / "book.json").write_text(json.dumps(book_json, ensure_ascii=False), encoding="utf-8")
    manuscript = "# 章节\n\n这是读者能看到的正文。"
    (book / "chapters" / "0001_章节.md").write_text(manuscript, encoding="utf-8")
    (book / "story" / "current_state.md").write_text(
        "隐藏秘密：主角其实来自未来。", encoding="utf-8"
    )
    (book / "story" / "runtime" / "chapter-0001.intent.md").write_text(
        "作者要求：审计时重点检查关系跳级。", encoding="utf-8"
    )

    final = book / "chapters" / "0001_章节.md"
    txn = {
        "schemaVersion": "4.0", "chapter": 1, "state": "", "events": [],
        "legacyMigration": True,
        "legacySourcePath": "chapters/0001_章节.md",
        "legacySourceSha256": file_sha256(str(final)),
        "assuranceLevel": "source-hash-only",
    }
    _append_event(txn, "imported_closed")
    _atomic_json(str(book / "story" / "runtime" / "chapter-0001.transaction.json"), txn)
    (book / "story" / "import-manifest.json").write_text(json.dumps({
        "schemaVersion": "4.0", "firstChapter": 1, "lastChapter": 1,
        "files": [{
            "chapter": 1, "path": "chapters/0001_章节.md",
            "sha256": file_sha256(str(final)),
        }],
    }, ensure_ascii=False), encoding="utf-8")
    (book / "chapters" / "index.json").write_text(json.dumps({
        "chapters": [{"number": 1, "file": "0001_章节.md", "wordCount": 1}],
    }, ensure_ascii=False), encoding="utf-8")
    packet, _ = build_explicit_packet(str(book), final_chapters=[1])
    assert "这是读者能看到的正文" in packet
    assert "主角其实来自未来" not in packet
    assert "重点检查关系跳级" not in packet
    assert "目标字数" not in packet


def test_skill_forbids_parallel_subagent_drafting():
    root = os.path.join(os.path.dirname(__file__), "..")
    skill = open(os.path.join(root, "SKILL.md"), encoding="utf-8").read()
    workflow = open(
        os.path.join(root, "references", "workflow-continue.md"), encoding="utf-8"
    ).read()
    assert "禁止子代理写正文、补片段、改段落、提前写后章" in skill
    assert "第 N 章未封板为 `closed`，不得开始第 N+1 章" in skill
    assert "最小连续性事实" not in workflow
    assert "不附一审报告" in workflow


def test_new_book_writes_explicit_length_contract(tmp_path):
    path = create_book(
        title="长度门禁测试",
        genre="自定义混合题材",
        root=str(tmp_path),
        chapter_word_count=1200,
    )
    data = json.loads(open(os.path.join(path, "book.json"), encoding="utf-8").read())
    assert data["chapterMinChars"] == 1200
    assert data["chapterTargetChars"] == 1200
    assert data["chapterMaxChars"] == 1620
    assert data["chapterLengthGateFromChapter"] == 1
