# Dragon Writer 工作流

## 模式 A：创建新书

1. 确定项目根目录与书 id。默认使用 `books/<slug>/`，除非用户给出不同路径。
2. 按 `templates.md` 创建目录结构。
3. 写 `book.json`：书名、语言、题材、状态 `outlining`、目标章数、目标单章字数。
4. 根据用户灵感写 `author_intent.md`，保留用户的任何确切要求。
5. 写 `story_frame.md` 为有密度的散文，而非干清单：
   - 主题与基调
   - 前台故事 / 背景故事
   - 核心冲突与对手
   - 世界法则与感官质地
   - 具体的终局目标（须可外部验证，不能只是"变得更强"或"复仇"）
6. 写 `volume_map.md`：
   - 弧线 / 卷结构与情感曲线
   - 钩子种子 / 回报承诺图
   - 按目标篇幅安排章节节拍或弧线节拍
   - 节奏原则
7. 为每个重要角色写一份角色档案。
8. 写 `book_rules.md` / `pending_hooks.md` / `current_state.md`，以及一张空的 `chapter_summaries.md`。
9. 保存 `story/snapshots/0/` 作为第 0 章快照。
10. 若用户要求立刻写正文，以模式 B 推进第一章。

## Mode B: Continue Existing Book

1. Locate the active book. If multiple books exist and the user did not name one, list candidates and ask.
2. Resolve next chapter number from contiguous chapter files and `chapters/index.json`.
3. Read protected context:
   - author intent
   - current focus
   - story frame / story bible
   - volume map / outline
   - book rules
   - current state
   - relevant role files
   - active hooks
4. Read compressible context:
   - recent chapter summaries
   - recent chapter endings
   - older summaries or volume summaries
   - audit drift
5. Create `runtime/chapter-NNNN.intent.md` with:
   - chapter goal
   - outline node
   - current task
   - reader expectation
   - hooks to advance, resolve, or keep buried
   - must keep / must avoid
   - required end-of-chapter change
6. Draft the chapter.
7. **双层质量门禁**：
   - 第一层：驻场初筛（SKILL.md 7 点）。不过→改；过→进第二层。
   - 第二层：37 维连续审计 + 审-改循环（`references/audit-dimensions.md`）：体裁裁剪 → Auditor 逐维出报告 → Reviser 修订 → 回头从第 1 维重过 → 分级落地（critical 必过、warning 修或留漂移记录、info 仅记录）→ 3 轮上限 → 留痕 `story/audit-drift.md`。
   - 两轮全过 → 进第 8 步落盘。
8. Persist:
   - `chapters/NNNN_<title>.md`
   - `chapters/index.json`
   - `chapter_summaries.md` 行（含**章节 delta**——本章改变了哪些事实/推了哪些伏笔/关系状态从 X 变 Y，见 templates.md"章节 delta"）
   - `current_state.md`（章节感知事实表 + Relationships + Resources + Conflict）
   - `pending_hooks.md`（按 13 列诊断列治理规则：stale/blocked 字面标记、merged/resolved 收敛）
   - 新建快照 `snapshots/<NNNN>/`
   - regenerate `books/<book-id>/dashboard.html` (Mode F 第 1–3 步)，让嵌入快照保持最新

## 模式 C：导入现有章节并续写

1. 按文件顺序、标题、或用户给出的拆分规则把源文本拆成有序章节。
2. 创建或选定目标书。
3. 从已有证据而非凭空想象构建基础文件：
   - 用早期章节推断前提与基调
   - 用晚期章节推断当前续写起点
   - 用中段锚点推断弧线演化
   - 用标题目录推断整体结构
4. 按模式 A 写基础文件。
5. 把导入章节回放到运行时文件：
   - 保存章节文件
   - 追加摘要
   - 提取当前状态与活跃钩子
   - 推断风格指南
6. 从第一个未写章节起按模式 B 续写。

## 模式 D：转向 / 调整方向

当用户说"把焦点拉回来"、"暂停这条支线"、"下一章要写……"、或"换个方向"时使用。

1. 默认不重写整个基础。
2. 为局部 1–3 章转向更新 `current_focus.md`。
3. 只为长期性的方向认同变化更新 `author_intent.md`。
4. 生成一份全新的章节意图。
5. 若新需求与 canon 矛盾，先记录矛盾并向用户确认，再改既有事实。

## 模式 E：改写 / 修复

1. **识别回滚点**：用户指定重写到第 N 章。
2. **三步回滚机械**（仅在用户 N 之后没有章节，或用户**明确同意删后续**时启用真实删除）：
   - **恢复快照**：把 `story/snapshots/<N-1>/` 的状态文件恢复到工作区（`current_state.md` / `pending_hooks.md` / `chapter_summaries.md` 回到 N-1 结束时快照）。
   - **清后续产物**：删除第 N 章之后的**所有**运行时产物——`chapters/NNNN_*.md`（N 之后）、`chapters/index.json` 中 N 之后的条目、`chapter_summaries.md` 中 N 之后的行、`current_state.md` / `pending_hooks.md` 中 N 章之后的改动。
   - **重建快照**：从 N-1 章状态重新起草第 N 章，完成后新建快照 `snapshots/<N>/`。
3. **绝不擅自删章**：只在 N 之后无章节、或用户明确同意时才启用真实删除。否则走"在新分支上重写、保留旧章"路径——把新稿存到 `runtime/chapter-NNNN.rewrite.md` 让用户对比取舍。
4. **对齐**：小改动（行文级）直接编辑章节后同步 summaries / state / hooks，仍过双层质检。大改动（结构级）重新生成 chapter intent 并从恢复态起草。
5. **过双层质量门禁**：重写稿必须走 SKILL.md 双层质检（7 点初筛 + 37 维审-改循环），不因为是重写而豁免。
6. **留痕**：把回滚点、删除范围、重写差异写入 `story/audit-drift.md` 的"已修复"节。

## 模式 F：查看进度 / 写作仪表盘

当用户要求看进度、打开仪表盘、查看设定完成度、人物关系或在仪表盘内阅读章节时使用。仪表盘是一份**自包含的 HTML 模板**（`references/dashboard.html`），通过 **File System Access API**（或 `webkitdirectory` 回退）在运行时读取书源文件并实时计算渲染。它**不嵌入任何数据**，永远反映最新文件，因此只需生成一次、无需每章重写。

### 使用步骤

1. 定位当前书（若有多本且未指定，让用户选）。
2. 确认 `books/<book-id>/dashboard.html` **存在**：
   - 若不存在，把模板 `dragon-writer/references/dashboard.html` 复制到书文件夹（仅此一次）。
   - 若已存在，**不要覆盖**——模板是通用的，数据在运行时读取。
3. 告诉用户：**直接双击 `dashboard.html` 即可打开仪表盘**，第一次选择书文件夹授权后自动重连（IndexedDB 持久化句柄），后续零交互。建议 Chrome / Edge。

### 工作原理

- 第一次打开弹出文件夹选择框，选中本书根目录并授权。
- 授权后仪表盘读取 `book.json` / `chapters/*.md` / `story/*.md`，实时计算：写作进度、设定完成度、设定内容全文、人物关系图、审计漂移、章节阅读。
- 句柄记入 IndexedDB；下次打开自动重连（权限失效才需再选一次）。
- 浏览器不支持 File System Access API 时，提供"兼容模式选择"。
- 所有数据均在本地读取，绝不上传；仪表盘不修改任何书文件。

### 何时调用

- **按需**：用户要求看进度 / 仪表盘 / 完成度 / 人物关系 / 章节读。
- **新建 / 导入时**（模式 A / 模式 C）：确保书文件夹下有一份仪表盘模板（缺失则注入一次）。
- **不要每章重写仪表盘**——它运行时自会读取最新文件，无需重新生成。

报告仪表盘路径与打开方式即可，不要声称"给用户看了仪表盘"。

## 章节意图模板

```markdown
# Chapter NNNN Intent（第 NNNN 章意图）

## Goal（目标）

## Outline Node（大纲节点）

## Current Task（当前任务）

## Reader Is Waiting For（读者在等啥）

## Hooks（钩子）
- advance（要推进的）：
- resolve（要收掉的）：
- defer（要继续捂着的）：

## Must Keep（必须保住）

## Must Avoid（必须避开）

## Style Emphasis（风格强调）

## Required End-of-Chapter Change（章尾必须出现的改变）

## Evidence Read（读过的证据）
```

## 落盘模板

每章落盘时更新：

```markdown
## Chapter NNNN Summary（第 NNNN 章摘要）
- Title（标题）：
- Characters（出场人物）：
- Events（事件）：
- State changes（状态变化）：
- Hook activity（钩子动态）：
- Mood / chapter type（心境 / 章节类型）：
- New open questions（新产生的悬念）：
```

写 `current_state.md` 时，优先写当前事实、少翻旧账。写 `chapter_summaries.md` 时，历史记录保持紧凑。
