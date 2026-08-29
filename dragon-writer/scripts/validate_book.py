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
import glob
import hashlib
import json
import os
import re
import sys
from typing import List, Optional, Tuple


SCHEMA_VERSION = "1.0.0"

# 文件契约（canonical 路径 / 别名 / 必需 / 推荐 / 快照清单 / 哈希）统一来自 _contract，
# 避免与 references/file-contract.json 漂移。
import _contract  # noqa: E402
from _contract import (  # noqa: E402
    chapter_length_limits,
    count_characters,
    count_words,
    file_exists_with_alias,
    read_file,
    file_sha256,
    safe_join,
)
from _schema import validate_document  # noqa: E402


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


def check_missing_files(book_dir: str, result: ValidationResult):
    """检查缺失文件：必需报错、推荐告警、旧角色单文件格式提示。"""
    for path in _contract.required_files():
        exists, actual = file_exists_with_alias(book_dir, path)
        if not exists:
            result.add_error(f"缺失必需文件：{path}")
        elif actual != path:
            result.add_warning(f"文件使用旧名：{actual}（建议迁移到 {path}）")
    for path in _contract.recommended_files():
        exists, actual = file_exists_with_alias(book_dir, path)
        if not exists:
            result.add_warning(f"缺失推荐文件：{path}")
        elif actual != path:
            result.add_warning(f"文件使用旧名：{actual}（建议迁移到 {path}）")
    legacy = _contract.character_legacy_files()
    for legacy_path in legacy.get("paths", []):
        if os.path.isfile(os.path.join(book_dir, legacy_path)):
            result.add_warning(legacy.get(
                "message", f"旧角色文件 {legacy_path} 暂不支持，请迁移到 story/roles/"))


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

    length_fields = [
        "chapterWordCount", "chapterMinChars", "chapterTargetChars", "chapterMaxChars",
        "chapterLengthGateFromChapter",
    ]
    for field in length_fields:
        if field in data and (
            not isinstance(data[field], int) or isinstance(data[field], bool) or data[field] <= 0
        ):
            result.add_error(f"book.json.{field} 必须是正整数")
    minimum, target, maximum = chapter_length_limits(data)
    if not minimum <= target <= maximum:
        result.add_error(
            f"章节长度契约顺序错误：chapterMinChars={minimum}, "
            f"chapterTargetChars={target}, chapterMaxChars={maximum}"
        )

    # T14.3：生命周期字段陈旧提示（status / updatedAt / skillVersion）
    latest_chapter_ts = None
    any_completed = False
    index_path = os.path.join(book_dir, "chapters", "index.json")
    if os.path.isfile(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                idx = json.load(f)
            entries = idx.get("chapters", []) if isinstance(idx, dict) else idx
            for e in entries:
                if e.get("status") == "completed":
                    any_completed = True
                ts = e.get("updatedAt", "")
                if ts and (latest_chapter_ts is None or ts > latest_chapter_ts):
                    latest_chapter_ts = ts
        except (json.JSONDecodeError, OSError):
            pass
    if any_completed and data.get("status") == "outlining":
        result.add_warning(
            "存在已完成章节但 book.json.status 仍为 outlining，请更新为 drafting"
        )
    if latest_chapter_ts and data.get("updatedAt", "") < latest_chapter_ts:
        result.add_warning(
            "book.json.updatedAt 早于最新章节 updatedAt，请同步该书元数据"
        )
    cur_ver = _contract.skill_version()
    if cur_ver and data.get("skillVersion") and data.get("skillVersion") != cur_ver:
        result.add_info(
            f"book.json.skillVersion {data.get('skillVersion')} 与当前 {cur_ver} 不一致"
        )


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

    # 兼容新旧两种 index 格式：新版 {"chapters": [...]} 与旧版裸列表 [{...}]
    entries = index.get("chapters", []) if isinstance(index, dict) else index
    index_files = set()
    index_numbers = set()
    for entry in entries:
        f = entry.get("file", "")
        if not f:
            result.add_error("index 条目缺少 file")
            continue
        if f in index_files:
            result.add_error(f"index 重复引用章节文件：{f}")
        index_files.add(f)
        number = entry.get("number")
        if number in index_numbers:
            result.add_error(f"index 出现重复章号：{number}")
        index_numbers.add(number)
        full = os.path.join(book_dir, "chapters", f)
        if not os.path.isfile(full):
            result.add_error(f"index 引用了不存在的章节文件：{f}")

    # 检查实际文件是否在 index 中
    chapters_dir = os.path.join(book_dir, "chapters")
    if os.path.isdir(chapters_dir):
        for name in os.listdir(chapters_dir):
            if name.endswith(".md") and name not in index_files:
                result.add_error(f"章节文件 {name} 未在 index.json 中引用")


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
            if not line:
                # 空行 = 表边界：重置期望列数，允许下一张表不同列数（文件内多表场景）
                expected_cols = None
                continue
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
        except ValueError:
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
                actual_hash = file_sha256(full)
                if actual_hash != expected_hash:
                    result.add_error(f"快照 {name} 哈希不匹配：{fpath}")


# ---- 共享 Markdown 表格解析 / 章节定位 helper ----

def _parse_md_tables(text: str) -> List[List[List[str]]]:
    """解析文本中的 Markdown 表格，返回每张表的行列表（表头为第一行）。

    分隔行（--- / ---: / :---: 等）被跳过；表格由非 | 行分隔。
    """
    tables: List[List[List[str]]] = []
    cur: List[List[str]] = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.split("|")][1:-1]
            if cells and all(re.match(r"^:?-+:?$", c) for c in cells if c.strip()):
                continue
            cur.append(cells)
        else:
            if cur:
                tables.append(cur)
                cur = []
    if cur:
        tables.append(cur)
    return tables


def _find_chapter_file(book_dir: str, num: int) -> Optional[str]:
    """按章号定位章节文件（支持 0001_ / 1_ 前缀）。"""
    chapters_dir = os.path.join(book_dir, "chapters")
    if not os.path.isdir(chapters_dir):
        return None
    for name in sorted(os.listdir(chapters_dir)):
        m = re.match(r"^0*(\d+)", name)
        if m and name.endswith(".md") and int(m.group(1)) == num:
            return os.path.join(chapters_dir, name)
    return None


def _norm_text(s: str) -> str:
    """证据引文比对用的归一化：去掉标点 / 空白，保留中英文数字。"""
    return re.sub(r"[^一-鿿A-Za-z0-9]", "", s)


def _parse_props(text: str):
    """解析 current_state.md 的道具账本表，返回 {header, rows, prop_idx, origin_idx}。"""
    for table in _parse_md_tables(text):
        if not table or "prop_id" not in table[0]:
            continue
        header = table[0]
        return {
            "header": header,
            "rows": table[1:],
            "prop_idx": header.index("prop_id"),
            "origin_idx": header.index("origin") if "origin" in header else -1,
        }
    return None


# ---- 账本一致性检查 ----

def check_alias_conflicts(book_dir: str, result: ValidationResult):
    """T1.2：canonical 路径与别名同时存在 → error（双源，内容可能分叉）。"""
    for canonical, aliases in _contract.aliases().items():
        if not os.path.isfile(os.path.join(book_dir, canonical)):
            continue
        for alias in aliases:
            if os.path.isfile(os.path.join(book_dir, alias)):
                result.add_error(
                    f"规范名与别名并存：{alias} 与 {canonical} 同时存在，"
                    f"请合并到规范名并删除别名"
                )


ROLE_TIERS = [
    ("major", ["major", "主要角色"]),
    ("minor", ["minor", "次要角色"]),
]


def _role_dir_files(book_dir: str, subdirs: List[str]):
    """枚举角色目录下的 <目录名, 角色名>。"""
    for sub in subdirs:
        d = os.path.join(book_dir, "story", "roles", sub)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".md"):
                    yield sub, f[:-3]


def check_role_name_conflicts(book_dir: str, result: ValidationResult):
    """T2.2：同一角色同时存在于 major/ 与 minor/ → error（晋升未清理）。"""
    major_names = {name for _, name in _role_dir_files(book_dir, ROLE_TIERS[0][1])}
    minor_names = {name for _, name in _role_dir_files(book_dir, ROLE_TIERS[1][1])}
    for name in sorted(major_names & minor_names):
        result.add_error(
            f"角色同名双卡：story/roles/major/{name}.md 与 minor/{name}.md 并存，"
            f"请按晋升规则移动并只保留一份"
        )


def check_word_count_consistency(book_dir: str, result: ValidationResult):
    """index wordCount 与正文重算值核对；执行章节字符硬下限与软上限。"""
    index_path = os.path.join(book_dir, "chapters", "index.json")
    if not os.path.isfile(index_path):
        return
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    except (json.JSONDecodeError, OSError):
        return
    entries = index.get("chapters", []) if isinstance(index, dict) else index
    book_data = {}
    try:
        with open(os.path.join(book_dir, "book.json"), "r", encoding="utf-8") as f:
            book_data = json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    minimum, target, maximum = chapter_length_limits(book_data)
    gate_from = book_data.get("chapterLengthGateFromChapter", 1)
    if not isinstance(gate_from, int) or isinstance(gate_from, bool) or gate_from <= 0:
        gate_from = 1
    if gate_from > 1:
        manifest_path = os.path.join(book_dir, "story", "import-manifest.json")
        if not os.path.isfile(manifest_path):
            result.add_error(
                "chapterLengthGateFromChapter > 1 只能由 story/import-manifest.json 证明"
            )
        else:
            try:
                with open(manifest_path, "r", encoding="utf-8") as handle:
                    manifest = json.load(handle)
                for message in validate_document(manifest, "import-manifest.schema.json"):
                    result.add_error("import manifest：" + message)
                if manifest.get("lastChapter", 0) + 1 != gate_from:
                    result.add_error("chapterLengthGateFromChapter 必须等于 import manifest.lastChapter + 1")
                first = manifest.get("firstChapter")
                last = manifest.get("lastChapter")
                rows = manifest.get("files", [])
                if isinstance(first, int) and isinstance(last, int) and first > last:
                    result.add_error("import manifest.firstChapter 不得大于 lastChapter")
                listed = []
                for row in rows if isinstance(rows, list) else []:
                    chapter = row.get("chapter") if isinstance(row, dict) else None
                    rel_path = row.get("path", "") if isinstance(row, dict) else ""
                    listed.append(chapter)
                    try:
                        source_path = safe_join(book_dir, rel_path)
                    except ValueError as exc:
                        result.add_error(f"import manifest 路径不安全：{exc}")
                        continue
                    if not os.path.isfile(source_path):
                        result.add_error(f"import manifest 文件不存在：{rel_path}")
                    elif row.get("sha256") != file_sha256(source_path):
                        result.add_error(f"import manifest 哈希不匹配：{rel_path}")
                if isinstance(first, int) and isinstance(last, int) and first <= last:
                    expected = list(range(first, last + 1))
                    if sorted(listed) != expected:
                        result.add_error(
                            "import manifest.files 必须恰好覆盖 firstChapter..lastChapter，且每章一条"
                        )
            except (OSError, json.JSONDecodeError) as exc:
                result.add_error(f"import manifest 无法读取：{exc}")
    for e in entries:
        fname = e.get("file", "")
        recorded = e.get("wordCount", 0)
        full = os.path.join(book_dir, "chapters", fname)
        if not os.path.isfile(full):
            continue
        with open(full, "r", encoding="utf-8") as f:
            text = f.read()
        actual = count_words(text)
        chars = count_characters(text)
        if recorded and actual:
            dev = abs(actual - recorded) / recorded
            if dev > 0.05:
                result.add_error(
                    f"wordCount 与正文不符：{fname} index 记 {recorded}，"
                    f"实际 {actual}（偏差 {dev:.0%}），请运行 rebuild_index.py"
                )
        elif recorded == 0:
            result.add_warning(f"wordCount 缺失（0）：{fname}，请运行 rebuild_index.py")
        recorded_chars = e.get("manuscriptChars")
        if recorded_chars is not None and recorded_chars != chars:
            result.add_error(
                f"manuscriptChars 与正文不符：{fname} index 记 {recorded_chars}，实际 {chars}"
            )
        # 长度门禁用去空白字符数，不用 index 的词段数
        chapter_match = re.match(r"^(\d+)", fname)
        chapter_number = int(chapter_match.group(1)) if chapter_match else 0
        if os.path.isfile(full) and chapter_number >= gate_from:
            if chars == 0:
                result.add_error(f"章节为空：{fname}")
            elif chars < minimum:
                result.add_error(
                    f"章节字符数不足：{fname} 实际 {chars}，硬下限 {minimum}"
                    f"（目标 {target}）；必须补足缺失叙事节点，禁止注水"
                )
            elif chars > maximum:
                result.add_warning(
                    f"章节字符数超过软上限：{fname} 实际 {chars}，上限 {maximum}"
                    f"（目标 {target}），请检查拖沓或重复"
                )


def check_structured_runtime(book_dir: str, result: ValidationResult):
    """校验 4.0 结构化事实源、事务哈希链及生成 Markdown 新鲜度。"""
    runtime = os.path.join(book_dir, "story", "runtime")
    if not os.path.isdir(runtime):
        return
    schema_by_suffix = {".intent.json": "chapter-intent.schema.json"}
    for suffix, schema_name in schema_by_suffix.items():
        for path in glob.glob(os.path.join(runtime, f"chapter-*{suffix}")):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                for message in validate_document(data, schema_name):
                    result.add_error(f"{os.path.basename(path)}：{message}")
            except (OSError, json.JSONDecodeError) as exc:
                result.add_error(f"{os.path.basename(path)} 无法读取：{exc}")
    from chapter_txn import verify_transaction
    transactions = {}
    for path in glob.glob(os.path.join(runtime, "chapter-*.transaction.json")):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                txn = json.load(handle)
            transactions[txn.get("chapter")] = txn
            for message in verify_transaction(txn):
                result.add_error(f"{os.path.basename(path)}：{message}")
            chapter = txn.get("chapter")
            state = txn.get("state")
            draft = os.path.join(runtime, f"chapter-{chapter:04d}.draft.md") if isinstance(chapter, int) else ""
            if state in {"drafted", "gated", "audited", "closed"} and isinstance(chapter, int):
                if not os.path.isfile(draft) or txn.get("draftSha256") != file_sha256(draft):
                    result.add_error(f"{os.path.basename(path)}：draftSha256 与当前草稿不一致")
            if state in {"gated", "audited", "closed"} and isinstance(chapter, int):
                gate = os.path.join(runtime, f"chapter-{chapter:04d}.gate.json")
                event = next((row for row in reversed(txn.get("events", [])) if row.get("to") == "gated"), {})
                if not os.path.isfile(gate) or event.get("gateReportSha256") != file_sha256(gate):
                    result.add_error(f"{os.path.basename(path)}：机械门禁报告缺失或哈希不匹配")
            if state in {"audited", "closed"} and isinstance(chapter, int):
                audit_manifest = os.path.join(runtime, f"chapter-{chapter:04d}.audit.json")
                event = next((row for row in reversed(txn.get("events", [])) if row.get("to") == "audited"), {})
                if not os.path.isfile(audit_manifest) or event.get("auditManifestSha256") != file_sha256(audit_manifest):
                    result.add_error(f"{os.path.basename(path)}：审计清单缺失或哈希不匹配")
            if state == "closed" and isinstance(chapter, int):
                finals = sorted(glob.glob(os.path.join(book_dir, "chapters", f"{chapter:04d}_*.md")))
                if len(finals) != 1 or txn.get("finalSha256") != file_sha256(finals[0]):
                    result.add_error(f"{os.path.basename(path)}：finalSha256 与唯一正式稿不一致")
        except (OSError, json.JSONDecodeError) as exc:
            result.add_error(f"{os.path.basename(path)} 无法读取：{exc}")
    for path in glob.glob(os.path.join(runtime, "chapter-*.audit.json")):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                audit = json.load(handle)
            complete = {"informedAudit", "coldRead"}.issubset(audit)
            txn = transactions.get(audit.get("chapter"), {})
            state = txn.get("state")
            if complete:
                for message in validate_document(audit, "chapter-audit.schema.json"):
                    result.add_error(f"{os.path.basename(path)}：{message}")
            elif state in {"audited", "closed"}:
                result.add_error(f"{os.path.basename(path)}：audited/closed 事务缺少两类审计记录")
            else:
                allowed = {"schemaVersion", "chapter", "draftSha256", "informedAudit", "coldRead"}
                if set(audit) - allowed:
                    result.add_error(f"{os.path.basename(path)}：存在未知字段")
            if audit.get("draftSha256") != txn.get("draftSha256"):
                result.add_error(f"{os.path.basename(path)}：draftSha256 与事务不一致")
            for key in ("informedAudit", "coldRead"):
                item = audit.get(key)
                if item is None:
                    continue
                if not isinstance(item, dict) or item.get("status") not in {"pass", "fail"}:
                    result.add_error(f"{os.path.basename(path)}：{key} 记录无效")
                    continue
                try:
                    report_path = safe_join(book_dir, item.get("reportPath", ""))
                except ValueError as exc:
                    result.add_error(f"{os.path.basename(path)}：{key} 路径不安全：{exc}")
                    continue
                if not os.path.isfile(report_path):
                    result.add_error(f"{os.path.basename(path)}：{key} 报告不存在")
                elif item.get("reportSha256") != file_sha256(report_path):
                    result.add_error(f"{os.path.basename(path)}：{key} 报告哈希不匹配")
        except (OSError, json.JSONDecodeError) as exc:
            result.add_error(f"{os.path.basename(path)} 无法读取：{exc}")
    for source in glob.glob(os.path.join(runtime, "chapter-*.intent.json")):
        match_chapter = re.search(r"chapter-(\d+)\.intent\.json$", source)
        chapter = int(match_chapter.group(1)) if match_chapter else None
        if chapter not in transactions:
            result.add_error(f"{os.path.basename(source)}：缺少对应 transaction.json")
        view = source[:-5] + ".md"
        if not os.path.isfile(view):
            result.add_error(f"缺少 intent JSON 的生成视图：{os.path.basename(view)}")
            continue
        with open(view, encoding="utf-8") as handle:
            text = handle.read(300)
        match = re.search(r"source_sha256:\s*(sha256:[0-9a-f]{64})", text)
        if not match or match.group(1) != file_sha256(source):
            result.add_error(f"生成视图已过期：{os.path.basename(view)}，请运行 render_intent.py")


def check_fact_evidence(book_dir: str, result: ValidationResult):
    """T4.2：事实表 evidence 引文必须在 source_chapter 正文命中（防捏造事实）。

    无 evidence 列（旧表）→ 升级提示 warning；列存在但引文不命中 → error。
    """
    text = read_file(book_dir, "story/current_state.md")
    if not text:
        return
    for table in _parse_md_tables(text):
        if not table or "fact_id" not in table[0]:
            continue
        header = table[0]
        if "evidence" not in header:
            result.add_warning(
                "事实表缺少 evidence 列（原文短引），升级后启用引文核对（防事实捏造）"
            )
            return
        idx = {c: i for i, c in enumerate(header)}
        chapter_key = "source_chapter" if "source_chapter" in idx else "introduced_chapter"
        source_i, evi_i = idx[chapter_key], idx["evidence"]
        missing = 0
        for row in table[1:]:
            if len(row) <= max(source_i, evi_i):
                continue
            fact_id = row[0] if row else ""
            try:
                source_chapter = int(row[source_i])
            except ValueError:
                continue
            if source_chapter < 0:
                result.add_warning(f"事实来源章不合法（负数）：{fact_id}")
                continue
            evidence = row[evi_i].strip()
            if not evidence:
                missing += 1
                continue
            chap = _find_chapter_file(book_dir, source_chapter)
            if not chap:
                continue
            with open(chap, "r", encoding="utf-8") as f:
                chap_text = f.read()
            norm_ev = _norm_text(evidence)
            if norm_ev and norm_ev not in _norm_text(chap_text):
                result.add_error(
                    f"事实证据引文在章节 {source_chapter} 正文未命中：{fact_id} "
                    f"evidence=「{evidence[:30]}」（引文应出自第 {source_chapter} 章正文）"
                )
        if missing:
            result.add_warning(f"事实表有 {missing} 行缺少 evidence 引文")
        return


def check_knowledge_acquisition(book_dir: str, result: ValidationResult):
    """T4.3：逐角色获知路径必须完整，获知证据须在 known_from_chapter 命中。

    旧表缺列只给升级 warning；采用新 schema 后，缺少路径或证据属于 error。
    """
    text = read_file(book_dir, "story/current_state.md")
    if not text:
        return
    tables = _parse_md_tables(text)
    timeline_event_ids = set()
    for table in tables:
        if table and {"event_id", "start_time", "end_time", "presentation"}.issubset(table[0]):
            event_index = table[0].index("event_id")
            timeline_event_ids.update(
                row[event_index].strip() for row in table[1:] if len(row) > event_index
            )
    required = {
        "knower", "known_from_chapter", "acquisition_mode",
        "acquisition_event_id", "acquisition_evidence",
    }
    for table in tables:
        if not table or "fact_id" not in table[0]:
            continue
        header = table[0]
        missing_columns = sorted(required - set(header))
        if missing_columns:
            result.add_warning(
                "事实表缺少角色获知链列：" + ", ".join(missing_columns)
                + "（旧表兼容；升级后启用信息权限硬校验）"
            )
            return
        idx = {c: i for i, c in enumerate(header)}
        max_i = max(idx[c] for c in required)
        for row in table[1:]:
            if len(row) <= max_i:
                continue
            fact_id = row[0] if row else ""
            knower = row[idx["knower"]].strip()
            mode = row[idx["acquisition_mode"]].strip()
            event_id = row[idx["acquisition_event_id"]].strip()
            evidence = row[idx["acquisition_evidence"]].strip()
            missing_values = []
            if not knower:
                missing_values.append("knower")
            if not mode:
                missing_values.append("acquisition_mode")
            if not event_id:
                missing_values.append("acquisition_event_id")
            if not evidence:
                missing_values.append("acquisition_evidence")
            if missing_values:
                result.add_error(
                    f"角色获知链不完整：{fact_id} 缺少 {', '.join(missing_values)}"
                )
                continue
            if timeline_event_ids and event_id not in timeline_event_ids:
                result.add_error(
                    f"角色获知链引用不存在的时间轴事件：{fact_id} "
                    f"knower={knower} acquisition_event_id={event_id}"
                )
            try:
                known_from = int(row[idx["known_from_chapter"]])
            except ValueError:
                result.add_error(f"角色获知章不合法：{fact_id} knower={knower}")
                continue
            chap = _find_chapter_file(book_dir, known_from)
            if not chap:
                continue
            with open(chap, "r", encoding="utf-8") as f:
                chap_text = f.read()
            norm_ev = _norm_text(evidence)
            if norm_ev and norm_ev not in _norm_text(chap_text):
                result.add_error(
                    f"角色获知证据在章节 {known_from} 正文未命中：{fact_id} "
                    f"knower={knower} acquisition_evidence=「{evidence[:30]}」"
                )
        return


def check_relationship_permissions(book_dir: str, result: ValidationResult):
    """T4.4：关系许可账本必须有阶段、权限、催化事件与正文证据。"""
    text = read_file(book_dir, "story/current_state.md")
    if not text:
        return
    tables = _parse_md_tables(text)
    timeline_event_ids = set()
    for table in tables:
        if table and {"event_id", "start_time", "end_time", "presentation"}.issubset(table[0]):
            event_index = table[0].index("event_id")
            timeline_event_ids.update(
                row[event_index].strip() for row in table[1:] if len(row) > event_index
            )
    relation_table = next((table for table in tables if table and "pair_id" in table[0]), None)
    if relation_table is None:
        result.add_warning("缺少关系许可账本（旧书兼容；升级后启用关系熟悉度硬校验）")
        return
    required = {
        "pair_id", "A", "B", "first_met_chapter", "current_stage",
        "allowed_familiarity", "last_change_chapter", "catalyst_event_id", "evidence",
    }
    missing_columns = sorted(required - set(relation_table[0]))
    if missing_columns:
        result.add_error("关系许可账本缺列：" + ", ".join(missing_columns))
        return
    idx = {column: i for i, column in enumerate(relation_table[0])}
    max_i = max(idx[column] for column in required)
    for row in relation_table[1:]:
        if len(row) <= max_i:
            continue
        pair_id = row[idx["pair_id"]].strip()
        missing_values = [
            column for column in (
                "A", "B", "first_met_chapter", "current_stage", "allowed_familiarity",
                "last_change_chapter", "catalyst_event_id", "evidence",
            ) if not row[idx[column]].strip()
        ]
        if missing_values:
            result.add_error(
                f"关系许可链不完整：{pair_id} 缺少 {', '.join(missing_values)}"
            )
            continue
        event_id = row[idx["catalyst_event_id"]].strip()
        if timeline_event_ids and event_id not in timeline_event_ids:
            result.add_error(
                f"关系许可账本引用不存在的时间轴事件：{pair_id} catalyst_event_id={event_id}"
            )
        try:
            chapter = int(row[idx["last_change_chapter"]])
        except ValueError:
            result.add_error(f"关系变化章不合法：{pair_id}")
            continue
        chap = _find_chapter_file(book_dir, chapter)
        if not chap:
            continue
        evidence = row[idx["evidence"]].strip()
        with open(chap, "r", encoding="utf-8") as f:
            chapter_text = f.read()
        if _norm_text(evidence) not in _norm_text(chapter_text):
            result.add_error(
                f"关系变化证据在章节 {chapter} 正文未命中：{pair_id} "
                f"evidence=「{evidence[:30]}」"
            )


def check_prop_origin_drift(book_dir: str, result: ValidationResult):
    """T5.2：道具 origin 在最近快照间变化且未同步失效旧事实 → 结构提示。

    机器只做"origin 变了"的确定性提示，是否 canon 变更由审计裁决。
    """
    text = read_file(book_dir, "story/current_state.md")
    props = _parse_props(text)
    if not props or props["origin_idx"] < 0:
        return
    snap_dir = os.path.join(book_dir, "story", "snapshots")
    if not os.path.isdir(snap_dir):
        return
    nums = [int(n) for n in os.listdir(snap_dir) if n.isdigit()]
    if not nums:
        return
    latest = f"{max(nums):04d}"
    snap_state = os.path.join(snap_dir, latest, "story", "current_state.md")
    if not os.path.isfile(snap_state):
        return
    with open(snap_state, "r", encoding="utf-8") as f:
        old = _parse_props(f.read())
    if not old or old["origin_idx"] < 0:
        return
    old_map = {r[old["prop_idx"]]: r for r in old["rows"] if len(r) > old["prop_idx"]}
    cur_map = {r[props["prop_idx"]]: r for r in props["rows"] if len(r) > props["prop_idx"]}
    for pid, cur in cur_map.items():
        old_row = old_map.get(pid)
        if not old_row or len(old_row) <= old["origin_idx"] or len(cur) <= props["origin_idx"]:
            continue
        ov = old_row[old["origin_idx"]].strip()
        cv = cur[props["origin_idx"]].strip()
        if ov and cv and ov != cv:
            result.add_warning(
                f"道具 {pid} 的 origin 在快照间变化：'{ov}' -> '{cv}'。"
                f"origin 变更属 canon 变更，请确认事实表对应旧事实已标 invalidated_chapter"
            )


def check_number_anchor_selfconflict(book_dir: str, result: ValidationResult):
    """T6.4：角色卡 canon 数字锚点表内同一事项多值且无递增生效章衔接 → warning。

    锚点表是本角色硬数字的单一权威源；多值只有在按生效章严格递增形成"变更链"
    时才合法（如 身高 1章=5尺2寸 → 24章=5尺4寸），否则视为卡内自相矛盾。
    """
    roles_dir = os.path.join(book_dir, "story", "roles")
    if not os.path.isdir(roles_dir):
        return
    for root, _, files in os.walk(roles_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            with open(os.path.join(root, fname), "r", encoding="utf-8") as f:
                text = f.read()
            for table in _parse_md_tables(text):
                if not table or "anchor_id" not in table[0]:
                    continue
                header = table[0]
                item_i = header.index("事项")
                val_i = header.index("值")
                chap_i = header.index("生效章")
                groups = {}
                for row in table[1:]:
                    if len(row) <= max(item_i, val_i, chap_i):
                        continue
                    item = row[item_i].strip()
                    val = row[val_i].strip()
                    try:
                        chap = int(row[chap_i])
                    except ValueError:
                        chap = -1
                    groups.setdefault(item, []).append((val, chap))
                for item, entries in groups.items():
                    if len({v for v, _ in entries}) <= 1:
                        continue
                    ordered = sorted(entries, key=lambda e: e[1])
                    ok = all(a[0] == b[0] or a[1] < b[1]
                             for a, b in zip(ordered, ordered[1:]))
                    if not ok:
                        result.add_warning(
                            f"角色卡 {fname} canon 数字锚点：事项「{item}」多值且无递增"
                            f"生效章衔接：{entries}，请统一为单一权威值或标注变更链"
                        )
                return  # 每卡只处理第一个锚点表


def _parse_sections(text: str):
    """将文本解析为 [(小节名, 行列表)]，小节名取最近一个 `##` 标题。"""
    sections = []
    cur_name = ""
    cur_lines = []
    for line in text.split("\n"):
        if line.startswith("##"):
            if cur_lines:
                sections.append((cur_name, cur_lines))
            cur_name = line.lstrip("#").strip()
            cur_lines = []
        else:
            cur_lines.append(line)
    if cur_lines:
        sections.append((cur_name, cur_lines))
    return sections


def _norm_dim(s: str) -> str:
    """维度名归一化（去标点/空白，如 体型/外貌快照 -> 体型外貌快照）。"""
    return re.sub(r"[^一-鿿A-Za-z0-9]", "", s)


def _section_dim_names(lines):
    """从 book_rules 的维度声明小节提取维度名集合（表头含"维度名"）。"""
    for table in _parse_md_tables("\n".join(lines)):
        if not table or "维度名" not in table[0]:
            continue
        names = set()
        for row in table[1:]:
            if len(row) > 1 and row[1].strip():
                names.add(_norm_dim(row[1]))
        return names if names else None
    return None


def _timeline_columns(lines):
    """从角色卡时间线小节提取数据列（排除固定列 章 / 变化事件）。"""
    for table in _parse_md_tables("\n".join(lines)):
        if not table:
            continue
        header = table[0]
        if not any("章" in c for c in header):
            continue
        cols = set()
        for c in header:
            nc = _norm_dim(c)
            if nc and nc not in ("章", "变化事件"):
                cols.add(nc)
        return cols
    return None


def check_dimension_columns(book_dir: str, result: ValidationResult):
    """角色卡物理/逻辑数据时间线列必须与 book_rules 维度声明一致。

    与「物理数据维度」「逻辑数据维度」声明对齐：不声明的列（如仙侠题材的三围）
    不应出现在角色卡时间线里。book_rules 无对应声明时跳过（旧书兼容）。
    """
    rules = read_file(book_dir, "story/book_rules.md")
    if not rules:
        return
    decls = {}
    for name, lines in _parse_sections(rules):
        if "物理数据维度" in name:
            dims = _section_dim_names(lines)
            if dims:
                decls["物理"] = dims
        elif "逻辑数据维度" in name:
            dims = _section_dim_names(lines)
            if dims:
                decls["逻辑"] = dims
    if not decls:
        return
    roles_dir = os.path.join(book_dir, "story", "roles")
    if not os.path.isdir(roles_dir):
        return
    for root, _, files in os.walk(roles_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            with open(os.path.join(root, fname), "r", encoding="utf-8") as f:
                text = f.read()
            for kind, section in (("物理", "物理数据时间线"), ("逻辑", "逻辑数据时间线")):
                if kind not in decls:
                    continue
                for name, lines in _parse_sections(text):
                    if section in name:
                        cols = _timeline_columns(lines)
                        if cols is not None:
                            extra = cols - decls[kind]
                            if extra:
                                result.add_warning(
                                    f"角色卡 {fname}「{section}」存在未声明的列："
                                    f"{sorted(extra)}，请与 book_rules「"
                                    f"{'物理数据维度' if kind == '物理' else '逻辑数据维度'}」声明对齐"
                                )
                        break


def check_gender_address(book_dir: str, result: ValidationResult):
    """T7：性别称谓 lint——女角色被男性称谓 / 男角色被女性称谓（仅 warning，宁漏不误报）。

    角色性别从角色卡 `性别：男/女` 字段读取；只报"角色名 + 邻近异性称谓"的明确错位。
    """
    genders = {}
    roles_dir = os.path.join(book_dir, "story", "roles")
    if os.path.isdir(roles_dir):
        for root, _, files in os.walk(roles_dir):
            for f in files:
                if not f.endswith(".md"):
                    continue
                # 跳过模板文件（下划线前缀 / 文件名含"模板"），它们不是真实角色
                if f.startswith("_") or "模板" in f:
                    continue
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                except OSError:
                    continue
                m = re.search(r"性别[:：]\s*([男女])", content)
                if m:
                    genders[f[:-3]] = m.group(1)
    females = [n for n, g in genders.items() if g == "女"]
    males = [n for n, g in genders.items() if g == "男"]
    if not females and not males:
        return
    chapters_dir = os.path.join(book_dir, "chapters")
    if not os.path.isdir(chapters_dir):
        return
    male_markers = r"(?:一个|这个|那个|是个)?\s*(?:男的|男人|先生|哥们|老哥)"
    female_markers = r"(?:一个|这个|那个|是个)?\s*(?:女的|女人|小姐|姑娘)"
    for fname in sorted(os.listdir(chapters_dir)):
        if not fname.endswith(".md"):
            continue
        with open(os.path.join(chapters_dir, fname), "r", encoding="utf-8") as f:
            text = f.read()
        for fn in females:
            pat = re.escape(fn) + r"[^。！？!?\n]{0,8}" + male_markers
            for m in re.finditer(pat, text):
                result.add_warning(
                    f"{fname}：女角色「{fn}」被男性称谓：...{m.group(0)[:30]}..."
                    f"（请核对性别称谓）"
                )
        for mn in males:
            pat = re.escape(mn) + r"[^。！？!?\n]{0,8}" + female_markers
            for m in re.finditer(pat, text):
                result.add_warning(
                    f"{fname}：男角色「{mn}」被女性称谓：...{m.group(0)[:30]}..."
                    f"（请核对性别称谓）"
                )


def validate(book_dir: str) -> ValidationResult:
    """运行全部检查。"""
    result = ValidationResult()
    check_missing_files(book_dir, result)
    check_book_json(book_dir, result)
    check_chapters_continuity(book_dir, result)
    check_index_consistency(book_dir, result)
    check_markdown_table_columns(book_dir, result)
    check_fact_chapters(book_dir, result)
    check_fact_evidence(book_dir, result)
    check_knowledge_acquisition(book_dir, result)
    check_relationship_permissions(book_dir, result)
    check_hook_dependencies(book_dir, result)
    check_prop_quantities(book_dir, result)
    check_prop_origin_drift(book_dir, result)
    check_alias_conflicts(book_dir, result)
    check_role_name_conflicts(book_dir, result)
    check_word_count_consistency(book_dir, result)
    check_structured_runtime(book_dir, result)
    check_gender_address(book_dir, result)
    check_number_anchor_selfconflict(book_dir, result)
    check_dimension_columns(book_dir, result)
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
