# 模式 B：续写已有书

## 触发时机

书已存在，往下写。

## 步骤

1. **定位当前书**：若有多本且未指定，列出候选并询问。
2. **确定下一章章号**：从连续章节文件和 `chapters/index.json` 确定最新落硬盘章节——不要只信一份陈旧的状态文件。
3. **读受保护上下文**：
   - `author_intent.md`（含不可妥协项）
   - `current_focus.md`
   - `story_frame.md` / `story_bible.md`
   - `volume_map.md` / `outline.md`
   - `book_rules.md`
   - `current_state.md`（事实表 + 道具账本 + 空间锚点）
   - 相关角色档案
   - `pending_hooks.md`（活跃钩子）
4. **读可压缩上下文**：
   - 最近几章摘要
   - 最近 1–3 章结尾
   - `audit-drift.md`
5. **创建 `runtime/chapter-NNNN.intent.md`**（每章都创建）：
   - chapter goal
   - outline node
   - current task
   - reader expectation
   - hooks to advance / resolve / keep buried
   - must keep / must avoid
   - required end-of-chapter change
6. **起草**：从选定的上下文起草，而不是把整个项目都堆进来。
7. **双层质量门禁**（详见 SKILL.md + `references/audit-dimensions.md`）：
   - 第一层：驻场初筛（9 点）。不过→改；过→进第二层。
   - 第二层：41 个候选深化审计维度连续审计 + 审-改循环。体裁裁剪 → Auditor 逐维出报告 → Reviser 修订 → 回头从第 1 维重过 → 分级落地 → 3 轮上限 → 留痕 `audit-drift.md`。
   - 两轮全过 → 进第 8 步落盘。
8. **事务式落盘**（详见 `references/file-contract.md` 的"章节落盘事务流程"）：
   - 按序写入：`chapters/NNNN_<title>.md` → `chapters/index.json` → `chapter_summaries.md` 行（含**章节 delta**）→ `current_state.md`（事实表 + 关系 + 道具账本 + 空间锚点）→ `pending_hooks.md`
   - 全部写入后运行一致性验证
   - 完成后创建章末快照 `snapshots/<NNNN>/`（含 `manifest.json`）
   - **不要重写仪表盘**——它运行时自会读取最新文件

## 相关文档

- 文件职责与权威顺序：`references/file-contract.md`
- 章节落盘事务流程：`references/file-contract.md`
- 章节 delta 模板：`references/templates.md`
- 双层质量门禁：`references/audit-dimensions.md`
