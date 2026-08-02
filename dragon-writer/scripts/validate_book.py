#!/usr/bin/env python3
"""validate_book — 验证书籍目录的完整性与一致性。

检查：
- 缺失文件
- JSON 合法性和 schema
- 章节编号连续性
- index 与文件一致性
- Markdown 表格列数
- 事实起始章是否合法
- hook 依赖是否存在
- 道具数量是否为非负整数
- 快照 manifest 和哈希

输出可读诊断和机器可读结果（JSON）。
"""

import argparse
import hashlib
import json
import os
import re
import sys
from typing import List, Tuple


SCHEMA_VERSION = "1.0.0"

# 必需文件
REQUIRED_FILES = [
    "book.json",
    "chapters/index.json",
    "story/author_intent.md",
    "story/current_focus.md",
    "story/book_rules.md",
    "story/current_state.md",
    "story/pending_hooks.md",
    "story/chapter_summaries.md",
    "story/outline/story_frame.md",
    "story/outline/volume_map.md",
]

# 兼容命名映射（与 file-contract.md 同步）
ALIASES = {
    "story/outline/story_frame.md": ["story/story_bible.md", "story/setting.md", "story/world.md"],
    "story/outline/volume_map.md": ["story/volume_outline.md", "story/outline.md", "story/plot.md"],
    "story/book_rules.md": ["story/rules.md", "story/writing_rules.md"],
    "story/author_intent.md": ["story/author.md", "story/intent.md"],
    "story/current_focus.md": ["story/focus.md", "story/next.md"],
    "story/current_state.md": ["story/state.md", "story/truth.md"],
    "story/pending_hooks.md": ["story/hooks.md", "story/foreshadowing.md"],
    "story/chapter_summaries.md": ["story/summaries.md"],
    "story/audit-drift.md": ["story/audit_drift.md"],
}


class ValidationResult:
    """收集验证结果。"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.infos: List[str] = []

    def add_error(self, msg: str):
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_info(self, msg: str):
        self.infos.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
        }


def file_exists_with_alias(book_dir: str, path: str) -> Tuple[bool, str]:
    """检查文件是否存在（含别名回退），返回 (是否存在, 实际路径)。"""
    full = os.path.join(book_dir, path)
    if os.path.isfile(full):
        return True, path
    for alias in ALIASES.get(path, []):
        alias_full = os.path.join(book_dir, alias)
        if os.path.isfile(alias_full):
            return True, alias
    return False, path


def read_file(book_dir: str, path: str) -> str:
    """读取文件（含别名回退）。"""
    exists, actual = file_exists_with_alias(book_dir, path)
    if not exists:
        return ""
    with open(os.path.join(book_dir, actual), "r", encoding="utf-8") as f:
        return f.read()


def file_sha256(path: str) -> str:
    """计算文件 SHA-256。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def check_missing_files(book_dir: str, result: ValidationResult):
    """检查缺失文件。"""
    for path in REQUIRED_FILES:
        exists, actual = file_exists_with_alias(book_dir, path)
        if not exists:
            result.add_error(f"缺失必需文件：{path}")
        elif actual != path:
            result.add_warning(f"文件使用旧名：{actual}（建议迁移到 {path}）")


def check_book_json(book_dir: str, result: ValidationResult):
    """检查 JSON 合法性和 schema。"""
    path = os.path.join(book_dir, "book.json")
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error(f"book.json 解析失败：{e}")
        return

    required_fields = ["id", "title", "language", "genre", "status", "createdAt", "updatedAt"]
    for field in required_fields:
        if field not in data:
            result.add_error(f"book.json 缺少必需字段：{field}")

    if "schemaVersion" not in data:
        result.add_warning("book.json 缺少 schemaVersion")
    elif data.get("schemaVersion") != SCHEMA_VERSION:
        result.add_info(f"book.json schemaVersion {data.get('schemaVersion')} 与当前 {SCHEMA_VERSION} 不一致")


def check_chapters_continuity(book_dir: str, result: ValidationResult):
    """检查章节编号连续性。"""
    chapters_dir = os.path.join(book_dir, "chapters")
    if not os.path.isdir(chapters_dir):
        return
    nums = []
    for name in os.listdir(chapters_dir):
        if name.endswith(".md"):
            m = re.match(r"^(\d+)", name)
            if m:
                nums.append(int(m.group(1)))
    if not nums:
        return
    nums.sort()
    expected = list(range(nums[0], nums[0] + len(nums)))
    if nums != expected:
        missing = set(expected) - set(nums)
        if missing:
            result.add_warning(f"章节编号不连续，缺失：{sorted(missing)}")


def check_index_consistency(book_dir: str, result: ValidationResult):
    """检查 index 与文件一致性。"""
    index_path = os.path.join(book_dir, "chapters", "index.json")
    if not os.path.isfile(index_path):
        result.add_error("缺失 chapters/index.json")
        return
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error(f"chapters/index.json 解析失败：{e}")
        return

    index_files = set()
    for entry in index.get("chapters", []):
        f = entry.get("file", "")
        index_files.add(f)
        full = os.path.join(book_dir, "chapters", f)
        if not os.path.isfile(full):
            result.add_error(f"index 引用了不存在的章节文件：{f}")

    # 检查实际文件是否在 index 中
    chapters_dir = os.path.join(book_dir, "chapters")
    if os.path.isdir(chapters_dir):
        for name in os.listdir(chapters_dir):
            if name.endswith(".md") and name not in index_files:
                result.add_warning(f"章节文件 {name} 未在 index.json 中引用")


def check_markdown_table_columns(book_dir: str, result: ValidationResult):
    """检查 Markdown 表格列数一致性。"""
    files_to_check = [
        "story/current_state.md",
        "story/pending_hooks.md",
        "story/chapter_summaries.md",
    ]
    for path in files_to_check:
        exists, actual = file_exists_with_alias(book_dir, path)
        if not exists:
            continue
        with open(os.path.join(book_dir, actual), "r", encoding="utf-8") as f:
            lines = f.readlines()
        expected_cols = None
        for line in lines:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cols = len([c for c in line.split("|") if c.strip()])
            # 对齐行
            if all(re.match(r"^:?-+:?$", c.strip()) for c in line.split("|") if c.strip()):
                continue
            if expected_cols is None:
                expected_cols = cols
            elif cols != expected_cols:
                result.add_warning(f"{actual} 表格列数不一致：期望 {expected_cols}，实际 {cols}")


def check_fact_chapters(book_dir: str, result: ValidationResult):
    """检查事实起始章是否合法。"""
    text = read_file(book_dir, "story/current_state.md")
    if not text:
        return
    # 查找事实表
    table_match = re.search(r"##?.*已知事实[\s\S]*?\|.*\|\n\|[-\s|]+\n((?:\|.*\|\n)*)", text)
    if not table_match:
        return
    for line in table_match.group(1).strip().split("\n"):
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 5:
            continue
        # 起始章列（第 4 列，0-indexed 为 3）
        try:
            start_chap = int(cols[3])
            if start_chap < 0:
                result.add_warning(f"事实起始章不合法（负数）：{cols[0]}")
        except (ValueError, IndexError):
            pass


def check_hook_dependencies(book_dir: str, result: ValidationResult):
    """检查 hook 依赖是否存在。"""
    text = read_file(book_dir, "story/pending_hooks.md")
    if not text:
        return
    table_match = re.search(r"\|.*hook_id.*\|\n\|[-\s|]+\n((?:\|.*\|\n)*)", text)
    if not table_match:
        return
    hook_ids = set()
    dep_ids = set()
    for line in table_match.group(1).strip().split("\n"):
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 2:
            continue
        hook_ids.add(cols[0])
        # depends_on 列
        for col in cols[1:]:
            if col.startswith("hook-") and col not in ("—", "", "-"):
                dep_ids.add(col)
    missing = dep_ids - hook_ids
    for dep in missing:
        result.add_warning(f"hook 依赖不存在：{dep}")


def check_prop_quantities(book_dir: str, result: ValidationResult):
    """检查道具数量是否为非负整数。"""
    text = read_file(book_dir, "story/current_state.md")
    if not text:
        return
    table_match = re.search(r"##?.*道具账本[\s\S]*?\|.*\|\n\|[-\s|]+\n((?:\|.*\|\n)*)", text)
    if not table_match:
        return
    for line in table_match.group(1).strip().split("\n"):
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 4:
            continue
        try:
            qty = int(cols[3])
            if qty < 0:
                result.add_warning(f"道具数量为负：{cols[0]} = {qty}")
        except ValueError:
            pass


def check_snapshot_manifests(book_dir: str, result: ValidationResult):
    """检查快照 manifest 和哈希。"""
    snapshots_dir = os.path.join(book_dir, "story", "snapshots")
    if not os.path.isdir(snapshots_dir):
        return
    for name in sorted(os.listdir(snapshots_dir)):
        snap_path = os.path.join(snapshots_dir, name)
        if not os.path.isdir(snap_path):
            continue
        manifest_path = os.path.join(snap_path, "manifest.json")
        if not os.path.isfile(manifest_path):
            result.add_warning(f"快照 {name} 缺少 manifest.json")
            continue
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            result.add_error(f"快照 {name}/manifest.json 解析失败：{e}")
            continue
        # 验证哈希
        for fpath, expected_hash in manifest.get("fileHashes", {}).items():
            full = os.path.join(snap_path, fpath)
            if not os.path.isfile(full):
                result.add_error(f"快照 {name} 缺少文件：{fpath}")
            else:
                actual_hash = "sha256:" + file_sha256(full)
                if actual_hash != expected_hash:
                    result.add_error(f"快照 {name} 哈希不匹配：{fpath}")


def validate(book_dir: str) -> ValidationResult:
    """运行全部检查。"""
    result = ValidationResult()
    check_missing_files(book_dir, result)
    check_book_json(book_dir, result)
    check_chapters_continuity(book_dir, result)
    check_index_consistency(book_dir, result)
    check_markdown_table_columns(book_dir, result)
    check_fact_chapters(book_dir, result)
    check_hook_dependencies(book_dir, result)
    check_prop_quantities(book_dir, result)
    check_snapshot_manifests(book_dir, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="验证书籍目录")
    parser.add_argument("book_dir", help="书籍根目录")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()

    if not os.path.isdir(args.book_dir):
        print(f"错误：目录不存在 {args.book_dir}", file=sys.stderr)
        sys.exit(1)

    result = validate(args.book_dir)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        ok_mark = "PASS" if result.ok else "FAIL"
        if result.ok:
            print(f"[{ok_mark}] Validation passed")
        else:
            print(f"[{ok_mark}] Validation failed ({len(result.errors)} errors)")
        for e in result.errors:
            print(f"  [ERROR] {e}")
        for w in result.warnings:
            print(f"  [WARN] {w}")
        for i in result.infos:
            print(f"  [INFO] {i}")

    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
