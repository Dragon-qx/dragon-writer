#!/usr/bin/env python3
"""信息、关系与跨章重复护栏测试。"""

import os
import sys


SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from check_chapter_overlap import analyze_book  # noqa: E402
from select_audit import DIMENSION_NAMES, select_audit  # noqa: E402


def _write_chapter(book, number, title, body):
    chapters = book / "chapters"
    chapters.mkdir(exist_ok=True)
    (chapters / f"{number:04d}_{title}.md").write_text(
        f"# {title}\n\n{body}\n", encoding="utf-8"
    )


def test_dimension_27_is_relationship_guard_not_content_filter():
    result = select_audit("", risk_flags=["关系跃迁"])
    dim_27 = next(item for item in result["dimensions"] if item["dimension"] == 27)
    assert dim_27["name"] == "关系熟悉度与权限"
    assert dim_27["severity"] == "critical"
    assert all("敏感" not in name for name in DIMENSION_NAMES.values())


def test_information_guard_is_always_enabled_and_critical():
    result = select_audit("自定义混合题材")
    dim_9 = next(item for item in result["dimensions"] if item["dimension"] == 9)
    dim_2 = next(item for item in result["dimensions"] if item["dimension"] == 2)
    assert dim_9["name"] == "信息获知链"
    assert dim_9["severity"] == "critical"
    assert dim_9["executor"] == "main_agent"
    assert dim_2["name"] == "叙事时间与章节切分"
    assert dim_2["executor"] == "main_agent"


def test_reader_visible_and_split_dimensions_are_routed_without_hidden_context():
    result = select_audit("仙侠")
    dim_17 = next(item for item in result["dimensions"] if item["dimension"] == 17)
    dim_42 = next(item for item in result["dimensions"] if item["dimension"] == 42)
    dim_8 = next(item for item in result["dimensions"] if item["dimension"] == 8)
    dim_16 = next(item for item in result["dimensions"] if item["dimension"] == 16)
    dim_19 = next(item for item in result["dimensions"] if item["dimension"] == 19)
    assert dim_17["executor"] == "cold_reader"
    assert dim_42["executor"] == "split"
    assert {dim_8["executor"], dim_16["executor"], dim_19["executor"]} == {"split"}
    assert 9 not in result["cold_read_dimensions"]
    assert 27 not in result["cold_read_dimensions"]


def test_long_time_span_risk_activates_chronicle_guard():
    result = select_audit("自定义混合题材", risk_flags=["长时间跨度"])
    ids = {item["dimension"] for item in result["dimensions"]}
    assert 17 in ids
    assert result["risk_flags"] == ["长时间跨度"]


def test_overlap_guard_blocks_two_near_duplicate_paragraphs(tmp_path):
    repeated_a = "陆恒推开木门，看见石桌上压着一封没有署名的信。" * 5
    repeated_b = "他没有立刻拆信，只先检查窗框、门闩和地上的泥印。" * 5
    _write_chapter(tmp_path, 1, "旧章", repeated_a + "\n\n" + repeated_b)
    _write_chapter(
        tmp_path,
        2,
        "新章",
        repeated_a.replace("木门", "房门") + "\n\n"
        + repeated_b.replace("立刻", "马上"),
    )
    report = analyze_book(str(tmp_path), chapter=2, window=1)
    assert report["status"] == "fail"
    assert any(item["kind"] == "paragraph_overlap" for item in report["findings"])


def test_overlap_guard_allows_distinct_chapter(tmp_path):
    _write_chapter(tmp_path, 1, "旧章", "陆恒在雨夜追踪失窃的药箱。" * 30)
    _write_chapter(tmp_path, 2, "新章", "苏霜在议事堂拒绝长老提出的婚约。" * 30)
    report = analyze_book(str(tmp_path), chapter=2, window=1)
    assert report["status"] == "pass"
