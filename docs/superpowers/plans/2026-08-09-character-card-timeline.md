# 角色卡时间线数据丰富化 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 dragon-writer 角色卡在既有稳定属性之外，新增「物理数据时间线」与「逻辑数据时间线」两个章节锚定的追加式区块，并让快照/回滚覆盖角色卡。

**Architecture:** 改动集中在 skill 源目录 `dragon-writer/`（v3.7.0）。角色卡模板与 book_rules 模板新增时间线区块与维度声明；契约（`file-contract.md` / `file-contract.json`）同步更新职责与快照清单；`snapshot_book.py` / `rollback_book.py` 支持 `story/roles/**` glob 展开（共享 `_contract` 的新 helper，保证写入与回滚路径集一致）。文档侧同步更新 workflow、audit-dimensions、SKILL.md 与 skeleton。

**Tech Stack:** Python 3（scripts）、Markdown 模板、JSON 契约、pytest。

**Repo 根目录（本文所有路径相对它）：** `C:\Users\Administrator\WebstormProjects\dragon-writer\dragon-writer`

---

## Global Constraints

- 所有改动落在 repo 源 `dragon-writer/`（v3.7.0），**不**改动 `~/.claude/skills/dragon-writer`（旧安装 3.5.1，另作同步）。
- 角色卡时间线**追加式**：禁止修改旧行；首行 = 出场基线。
- 逻辑数据时间线维度列名必须与 `book_rules.md`「逻辑数据维度」声明完全一致。
- 快照写入与回滚读取必须使用**同一** glob 展开逻辑（`_contract` 单一来源）。
- 向后兼容：既有书不回填时间线不阻塞；既有稳定属性区块内容与用途不变。
- 中文界面文本优先；新增代码注释用中文，风格与现有脚本一致。

---

### Task 1: 快照/回滚支持角色卡 glob 展开（代码 + 契约）

这是唯一涉及代码的任务，独立可测。先写测试、再实现、后改契约配置。

**Files:**
- Modify: `scripts/_contract.py`（新增 `resolve_snapshot_files`，`import glob`）
- Modify: `scripts/snapshot_book.py:35-45`（改用 `_contract.resolve_snapshot_files`）
- Modify: `scripts/rollback_book.py:64-76`（恢复点收集改用同一 helper）
- Modify: `references/file-contract.json`（`snapshotFiles.paths` 增加 `story/roles/**`；角色卡 `description` 注明时间线）
- Test: `tests/test_snapshot_roles.py`（新建）

**Interfaces:**
- Consumes: `_contract.snapshot_files()`（返回配置的原始 pattern 列表，已有）
- Produces: `_contract.resolve_snapshot_files(book_dir: str) -> List[str]`——书根相对路径清单；非通配 pattern 原样返回（存在性由调用方检查并报告缺失），通配 pattern（`* ? [`）用 `glob.glob(recursive=True)` 展开为**存在的文件**清单，去重保序。

- [ ] **Step 1: 写失败测试**

新建 `tests/test_snapshot_roles.py`：

```python
#!/usr/bin/env python3
"""快照/回滚对角色卡 glob 展开的测试。

运行：python -m pytest tests/test_snapshot_roles.py -v
"""

import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import _contract
from snapshot_book import create_snapshot
from rollback_book import plan_rollback


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestResolveSnapshotFiles:
    def test_non_glob_pass_through(self, tmp_path):
        """非通配 pattern（current_state.md 等）原样返回。"""
        paths = _contract.resolve_snapshot_files(str(tmp_path))
        assert "story/current_state.md" in paths

    def test_glob_expands_to_existing_role_files(self, tmp_path):
        """story/roles/** 应展开为实际存在的角色文件，且不包含不存在的路径。"""
        book = tmp_path
        role = book / "story" / "roles" / "major" / "陆恒.md"
        role.parent.mkdir(parents=True, exist_ok=True)
        role.write_text("# 陆恒\n", encoding="utf-8")
        paths = _contract.resolve_snapshot_files(str(book))
        assert "story/roles/major/陆恒.md" in paths
        # 不存在的角色文件不应出现
        assert "story/roles/major/不存在.md" not in paths

    def test_glob_dedup_keeps_order(self, tmp_path):
        """重复 pattern 去重，输出稳定排序。"""
        book = tmp_path
        for name in ["甲.md", "乙.md"]:
            f = book / "story" / "roles" / "minor" / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("# x\n", encoding="utf-8")
        paths = _contract.resolve_snapshot_files(str(book))
        minor = [p for p in paths if p.startswith("story/roles/minor/")]
        assert minor == sorted(minor)
        assert len(minor) == len(set(minor))


class TestSnapshotIncludesRoles:
    def test_snapshot_copies_role_files(self, tmp_path):
        """create_snapshot 应把角色卡文件纳入快照目录。"""
        shutil.copytree(os.path.join(FIXTURES_DIR, "standard-book"), str(tmp_path))
        result = create_snapshot(str(tmp_path), chapter=1, dry_run=False, force=True)
        assert result["ok"]
        snap_dir = tmp_path / "story" / "snapshots" / "0001"
        assert (snap_dir / "story" / "roles" / "major" / "陆恒.md").is_file()
        assert "story/roles/major/陆恒.md" in result["included_files"]


class TestRollbackManifestHasRoles:
    def test_rollback_plan_lists_role_files(self, tmp_path):
        """manifest.includedFiles 含角色卡，回滚计划应列出。"""
        shutil.copytree(os.path.join(FIXTURES_DIR, "standard-book"), str(tmp_path))
        create_snapshot(str(tmp_path), chapter=1, dry_run=False, force=True)
        plan = plan_rollback(str(tmp_path), chapter=1)
        assert plan["ok"]
        assert any(p.startswith("story/roles/") for p in plan["restore_files"])
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_snapshot_roles.py -v`
Expected: `AttributeError: module '_contract' has no attribute 'resolve_snapshot_files'`（Task 尚未实现）

- [ ] **Step 3: 实现 `_contract.resolve_snapshot_files`**

在 `scripts/_contract.py` 顶部加 `import glob`，并在 `snapshot_files()` 之后新增：

```python
def resolve_snapshot_files(book_dir: str) -> List[str]:
    """将快照清单展开为书根相对的实际文件路径。

    非通配 pattern 原样返回（存在性由调用方检查并报告缺失）；
    通配 pattern（story/roles/** 等）用 glob 递归展开为存在的文件清单。
    快照写入（snapshot_book）与回滚读取（rollback_book）共用本函数，
    保证两者路径集一致。
    """
    result: List[str] = []
    for pat in snapshot_files():
        if any(ch in pat for ch in "*?["):
            base = os.path.join(book_dir, pat)
            for m in sorted(glob.glob(base, recursive=True)):
                if os.path.isfile(m):
                    rel = os.path.relpath(m, book_dir).replace(os.sep, "/")
                    if rel not in result:
                        result.append(rel)
        else:
            if pat not in result:
                result.append(pat)
    return result
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_snapshot_roles.py -v`
Expected: PASS（三个 TestResolveSnapshotFiles 用例）

- [ ] **Step 5: 更新 `snapshot_book.py` 使用新 helper**

替换 `create_snapshot` 中文件收集段（第 36-45 行）：

```python
    # 收集文件（清单来自 _contract.resolve_snapshot_files(book_dir)，
    # 支持 story/roles/** glob；非通配路径缺失时计入 missing）
    included_files = []
    file_hashes = {}
    missing = []
    for fpath in _contract.resolve_snapshot_files(book_dir):
        src = os.path.join(book_dir, fpath)
        if os.path.isfile(src):
            included_files.append(fpath)
            file_hashes[fpath] = file_sha256(src)
        else:
            missing.append(fpath)
```

- [ ] **Step 6: 更新 `rollback_book.py` 恢复点收集（第 71 行）**

```python
        for fpath in _contract.resolve_snapshot_files(book_dir):
```

- [ ] **Step 7: 运行全部测试确认通过（含角色卡快照用例）**

Run: `python -m pytest tests/test_snapshot_roles.py tests/test_contract.py -v`
Expected: 全部 PASS

- [ ] **Step 8: 更新 `references/file-contract.json`**

把 `snapshotFiles.paths` 数组改为（在末尾追加角色卡路径，保留既有 6 项）：

```json
    "snapshotFiles": {
      "description": "每个快照目录必须包含的运行时文件（书根相对路径）。支持 glob 通配（story/roles/**）。snapshot_book / rollback_book 共用本字段，避免路径解析漂移。",
      "paths": [
        "story/current_state.md",
        "story/pending_hooks.md",
        "story/chapter_summaries.md",
        "story/current_focus.md",
        "story/audit-drift.md",
        "chapters/index.json",
        "story/roles/**"
      ]
    }
```

并把角色卡文件条目 `description` 从 `"角色档案（一个角色一份文件）"` 改为：

```json
      "description": "角色档案（一个角色一份文件）：稳定属性 + 物理/逻辑数据时间线（章节锚定追加式，见 templates.md）"
```

- [ ] **Step 9: 重跑测试 + 提交**

Run: `python -m pytest tests/ -v`
Expected: 全部 PASS

```bash
git add scripts/_contract.py scripts/snapshot_book.py scripts/rollback_book.py references/file-contract.json tests/test_snapshot_roles.py
git commit -m "feat: 快照/回滚支持角色卡 glob 展开（story/roles/**）"
```

---

### Task 2: 更新 `references/templates.md` 角色卡与 book_rules 模板

**Files:**
- Modify: `references/templates.md:113-129`（角色卡模板）
- Modify: `references/templates.md:131-149`（book_rules 模板）
- Modify: `references/templates.md` 目录索引（可选，保持一致）

**Interfaces:**
- Produces: 角色卡新增两个区块的**标准区块名**（`物理数据时间线` / `逻辑数据时间线`）——Task 4 契约文档、Task 6 审计维度、Task 5 workflow 均引用这些区块名。

- [ ] **Step 1: 替换角色卡模板段落**

把 `### roles/major/<name>.md` 小节（第 113-129 行）整体替换为：

````markdown
### roles/major/<name>.md

> 角色档案 = **稳定属性** + **数据时间线**。稳定属性（功能、欲望、恐惧、秘密、言行指纹、长期弧线）只在方向性转向时修改；「物理 / 逻辑数据时间线」为**章节锚定的追加式 Runtime 区块**——每章只新增变化点行、禁止修改旧行。易漂移的"当前关系 / 伤势 / 位置"仍不写入档案，归入 `current_state.md`。

```markdown
# <Name>

## 角色功能 Story Function

## 欲望·恐惧·创伤 Desire / Fear / Wound

## 秘密与信息边界 Secrets And Information Boundary

## 言行指纹 Speech And Behavior Fingerprint

## 成长弧线 Arc

## 物理数据时间线 Physical Data Timeline
> 章节锚定，只记变化点：出现变化才新增一行。首行 = 出场基线。无变化不新增。

| 章 | 身高 | 体重 | 三围（胸/腰/臀） | 体型/外貌快照 | 变化事件 |
| ---: | ---: | ---: | --- | --- | --- |
| 1 | 5尺2寸 | 108斤 | 32/24/34 | 清瘦少年，粗布麻衣，目光沉静 | 出场基线 |
| 24 | 5尺4寸 | 128斤 | 35/27/36 | 筑基重塑后身姿挺拔，气质沉凝 | 突破金丹·肉身重塑 |

## 逻辑数据时间线 Logical Data Timeline
> 维度由 book_rules.md「逻辑数据维度」声明；维度列名必须与声明完全一致。章节锚定，只记变化点；取最后一行的值为当前权威值。

| 章 | 修为境界 | 主修功法 | 神识强度 | 变化事件 |
| ---: | --- | --- | --- | --- |
| 1 | 练气三层 | 《寒心诀》一层 | 常 | 出场基线 |
| 24 | 金丹中期 | 《寒心诀》三层·凝霜成剑 | 初窥识海 | 突破金丹 |
```
````

- [ ] **Step 2: 在 book_rules 模板追加「逻辑数据维度」小节**

在 `### book_rules.md` 模板代码块末尾（`## 年代约束 Era Constraints` 之后）追加：

````markdown
## 逻辑数据维度 Logical Data Dimensions
> 角色卡「逻辑数据时间线」的维度列清单。不同题材声明不同维度：
> 修仙→修为境界/功法/神识；科幻→异能等级/科技权限；都市→身份/资产/人脉…
> 维度列名必须与角色卡表格列完全一致（审计维 39 锚点）。

| dim_id | 维度名 | 单位/取值口径 | 说明 |
| --- | --- | --- | --- |
| dim-001 | 修为境界 | 大境界+小阶段（练气三层/筑基/金丹中期…） | 主修境界 |
| dim-002 | 主修功法 | 功法名+层数 | 当前主修功法 |
| dim-003 | 神识强度 | 常/渐强/初窥识海/化神出窍… | 神识水平 |
```
````

- [ ] **Step 3: 提交**

```bash
git add references/templates.md
git commit -m "docs: 角色卡模板加物理/逻辑数据时间线，book_rules 加逻辑数据维度声明"
```

---

### Task 3: 更新 `references/file-contract.md` 契约文档

**Files:**
- Modify: `references/file-contract.md:98-99`（角色卡职责）
- Modify: `references/file-contract.md:127-140`（Foundation 与 Runtime 边界）
- Modify: `references/file-contract.md:186-220`（快照契约）

**Interfaces:**
- Consumes: Task 2 的区块名（`物理数据时间线` / `逻辑数据时间线`）
- Produces: 角色卡职责、Foundation/Runtime 边界、快照清单三处的权威描述——供 Task 5/6/7 引用。

- [ ] **Step 1: 更新 `roles/**/*.md` 文件职责（第 98-99 行）**

原：
> `roles/**/*.md`
> : 一个角色一份文件。**仅保存稳定属性**：角色功能、欲望、恐惧、秘密、言行指纹、长期弧线。易漂移的"当前关系 / 伤势 / 位置 / 能力状态"不写入档案，统一归入 `current_state.md`（详见 [Foundation 与 Runtime 边界](#foundation-与-runtime-边界)）。

改为：
> `roles/**/*.md`
> : 一个角色一份文件。保存**稳定属性**（角色功能、欲望、恐惧、秘密、言行指纹、长期弧线）+ **数据时间线**（「物理数据时间线」「逻辑数据时间线」，章节锚定的追加式 Runtime 区块，见 `templates.md`）。易漂移的"当前关系 / 伤势 / 位置"仍不写入档案，统一归入 `current_state.md`（详见 [Foundation 与 Runtime 边界](#foundation-与-runtime-边界)）。

- [ ] **Step 2: 更新 Foundation/Runtime 边界说明（第 127-140 行）**

在 Foundation 清单中 `角色档案中的稳定属性` 一处补注，并在边界规则句尾补充时间线规则。将边界规则段替换为：

> **边界规则**：续写时只改 Runtime 文件；Foundation 文件仅在用户明确要求或方向性转向时修改。角色档案是**混合层**——稳定属性按 Foundation 治理（跨章不漂移）；「物理/逻辑数据时间线」按 Runtime 追加式治理（每章只新增变化点行、不改旧行），它与 `current_state.md` 的关系是：时间线存**逐章数值/外观历史**，`current_state.md` 存**当前关系/伤势/位置/目标**。"当前关系 / 伤势 / 位置 / 能力状态"这类即时态仍归入 `current_state.md`，不在档案稳定属性区直接修改。

- [ ] **Step 3: 更新快照契约（第 186-220 行）**

在「每个快照必须包含的文件」清单末尾追加：

> - `story/roles/**`（角色卡数据时间线，支持 glob 通配；展开逻辑见 `_contract.resolve_snapshot_files`）

并把「安全规则」下补充一条：

> - **glob 一致性**：快照写入（`snapshot_book`）与回滚恢复点收集（`rollback_book`）必须共用 `_contract.resolve_snapshot_files()` 的展开逻辑，禁止各自硬编码路径集。

- [ ] **Step 4: 提交**

```bash
git add references/file-contract.md
git commit -m "docs: 角色卡职责/边界/快照契约补数据时间线"
```

---

### Task 4: 更新 `references/workflow-new-book.md` 与 `SKILL.md`

**Files:**
- Modify: `references/workflow-new-book.md:24`（写角色档案步骤）
- Modify: `SKILL.md:17`（Foundation/Runtime 说明）

**Interfaces:**
- Consumes: Task 2 的区块名与基线行概念。
- Produces: 新书流程与主文档对时间线的表述——面向使用 skill 的 LLM，无需测试。

- [ ] **Step 1: 更新 `workflow-new-book.md` 第 24 行**

原：
> 7. **为每个重要角色写一份角色档案**：仅保存稳定属性（功能、欲望、恐惧、秘密、言行指纹、长期弧线），易漂移的"当前状态"归入 `current_state.md`。

改为：
> 7. **为每个重要角色写一份角色档案**：写稳定属性（功能、欲望、恐惧、秘密、言行指纹、长期弧线），并在「物理数据时间线」「逻辑数据时间线」写入**出场基线行**（出场章、当前身高/体重/三围、体型/外貌快照、各逻辑维度当前值）；逻辑维度列名与 `book_rules.md`「逻辑数据维度」声明一致。易漂移的"当前状态"归入 `current_state.md`。

- [ ] **Step 2: 更新 `SKILL.md` 第 17 行**

原：
> - **静态基础与运行时态分开**：Foundation（前提、世界法则、卷章地图、角色卡稳定属性、规则书）只在用户明确要求或方向性转向时修改；Runtime（当前状态、钩子、摘要、焦点、审计漂移、道具账本、空间锚点）每章更新。

改为：
> - **静态基础与运行时态分开**：Foundation（前提、世界法则、卷章地图、角色卡稳定属性、规则书）只在用户明确要求或方向性转向时修改；Runtime（当前状态、钩子、摘要、焦点、审计漂移、道具账本、空间锚点、角色卡物理/逻辑数据时间线）每章更新（时间线为追加式：只加变化点行、不改旧行）。

- [ ] **Step 3: 提交**

```bash
git add references/workflow-new-book.md SKILL.md
git commit -m "docs: 新书流程与主文档补角色卡数据时间线"
```

---

### Task 5: 更新 `references/audit-dimensions.md` 维 4 与维 40

**Files:**
- Modify: `references/audit-dimensions.md:140`（维度边界表·维 4 行）
- Modify: `references/audit-dimensions.md:176`（维度边界表·维 40 行）
- Modify: `references/audit-dimensions.md:268-271`（维 4 判定规则）
- Modify: `references/audit-dimensions.md:531-538`（维 40 判定规则）

**Interfaces:**
- Consumes: Task 2 的区块名。Auditor 据此把时间线作为逐章权威来源。

- [ ] **Step 1: 更新维度边界表**

维 4 行 `depends_on` 由 `角色档案, book_rules` 改为 `角色档案（逻辑数据时间线）, book_rules`；维 40 行 `depends_on` 由 `角色档案` 改为 `角色档案（物理数据时间线）`。

- [ ] **Step 2: 更新维 4 判定规则（第 268-271 行）**

原判定规则句前追加一句：
> 优先对照角色卡「逻辑数据时间线」的维度列（如修为境界/功法/神识）：升级路径必须能在时间线上找到变化点与变化事件，找不到的突然变强/变弱即"战力崩坏"。再对照 `book_rules.md` 的"力量/资源/时间限制"：升级须呼应"心障/外劫"设定，禁止"忽然顿悟"与"一拳秒杀"。

- [ ] **Step 3: 更新维 40 判定规则（第 531-538 行）**

在「外貌特征」条目中把 `以角色档案为准` 改为 `以角色卡「物理数据时间线」的外貌快照列与言行指纹为准`，并追加一句：
> 跨章外貌变化（身高/三围/体型）须能在时间线找到对应变化点与事件（如"筑基重塑肉身"）；无变化点的外貌突变视为漂移。

- [ ] **Step 4: 提交**

```bash
git add references/audit-dimensions.md
git commit -m "docs: 审计维4/40以角色卡数据时间线为逐章权威来源"
```

---

### Task 6: 更新 skeleton 与 fixture

**Files:**
- Modify: `assets/book-skeleton/story/book_rules.md`（加逻辑数据维度声明空模板）
- Modify: `tests/fixtures/standard-book/story/book_rules.md`（加维度声明，供 Task 1 快照测试的 fixture 一致）
- Modify: `tests/fixtures/standard-book/story/roles/major/陆恒.md`（加双时间线基线行，验证模板可落地、不影响 validate）

**Interfaces:**
- Consumes: Task 2 的模板。
- Produces: 新书 skeleton 自动带出维度声明；fixture 角色卡作为「时间线已落地的角色卡」样例。

- [ ] **Step 1: 更新 skeleton `assets/book-skeleton/story/book_rules.md`**

在 `## 年代约束 Era Constraints` 之后追加：

```markdown
## 逻辑数据维度 Logical Data Dimensions
> 角色卡「逻辑数据时间线」的维度列清单。新书写角色卡前先在此声明维度。

| dim_id | 维度名 | 单位/取值口径 | 说明 |
| --- | --- | --- | --- |
| dim-001 |  |  |  |
```

- [ ] **Step 2: 更新 fixture `tests/fixtures/standard-book/story/book_rules.md`**

在 `## 年代约束 Era Constraints` 之后追加：

```markdown
## 逻辑数据维度 Logical Data Dimensions

| dim_id | 维度名 | 单位/取值口径 | 说明 |
| --- | --- | --- | --- |
| dim-001 | 修为境界 | 炼气→筑基→金丹→元婴→化神 | 主修境界 |
| dim-002 | 主修功法 | 功法名+层数 | 当前主修功法 |
```

- [ ] **Step 3: 更新 fixture 角色卡 `tests/fixtures/standard-book/story/roles/major/陆恒.md`**

在文件末尾追加：

```markdown
## 物理数据时间线 Physical Data Timeline

| 章 | 身高 | 体重 | 三围（胸/腰/臀） | 体型/外貌快照 | 变化事件 |
| ---: | ---: | ---: | --- | --- | --- |
| 1 | 5尺2寸 | 108斤 | — | 清瘦少年，粗布麻衣 | 出场基线 |

## 逻辑数据时间线 Logical Data Timeline

| 章 | 修为境界 | 主修功法 | 变化事件 |
| ---: | ---: | --- | --- |
| 1 | 炼气三层 | — | 出场基线 |
```

（三围列用 `—` 说明该角色三围未定义时合法；维度列只声明了 fixture 需要的两列。）

- [ ] **Step 4: 全量测试确认不受影响**

Run: `python -m pytest tests/ -v`
Expected: 全部 PASS（validate_book 的表格列检查仅针对 current_state/pending_hooks/chapter_summaries，不含角色卡）

- [ ] **Step 5: 提交**

```bash
git add assets/book-skeleton/story/book_rules.md tests/fixtures/standard-book/
git commit -m "docs: skeleton 与 fixture 补逻辑数据维度声明与角色卡时间线样例"
```

---

## Self-Review

### 1. Spec coverage

- 角色卡双时间线区块 → Task 2
- book_rules 逻辑数据维度声明 → Task 2 / Task 6（模板 + skeleton + fixture）
- file-contract.md 职责/边界/快照 → Task 3
- file-contract.json snapshotFiles + description → Task 1 Step 8
- workflow-new-book → Task 4
- audit-dimensions 维4/40 → Task 5
- SKILL.md → Task 4
- snapshot_book / rollback_book glob 展开 → Task 1
- 仪表盘兼容（不改 dashboard）→ 无需任务；已核实新区块名不与 `buildGraph`/`MDParser` 正则冲突
- 快照覆盖角色卡（用户要求纳入）→ Task 1 实现 + 测试

### 2. Placeholder scan

无 TBD/TODO；每个 Step 含实际代码或确切文本。fixture 的「三围」列用 `—` 是刻意样例（说明未定义时合法），非占位符。

### 3. Type consistency

- `resolve_snapshot_files(book_dir: str) -> List[str]` 在 Task 1 Step 3 定义，Step 5/6 引用同一签名。
- 区块名 `物理数据时间线` / `逻辑数据时间线` 在 Task 2 定义，Task 3/4/5/6 统一引用，无别名漂移。
- `snapshot_book.create_snapshot`、`rollback_book.plan_rollback` 签名未变，测试按现有签名调用。
