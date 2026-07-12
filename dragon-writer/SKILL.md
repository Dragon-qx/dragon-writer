---
name: dragon-writer
description: 长篇虚构小说写作工作流（兼容 opencode / Claude Code / Codex）：用大纲、设定、角色、规则、钩子、状态文件创建新书；读取已有大纲/设定/章节库续写；在保持连贯性、作者意图、当前焦点与持久故事态的前提下，规划、起草、审计、修订、落盘各章节。
---

# Dragon Writer

Dragon Writer 是一份工具无关的长篇虚构小说写作工作流。当用户需要创建一本书、续写一章、重建或阅读大纲/设定文件、导入已有章节、调整故事方向、修订某一章，或在多个会话间维护持久的故事圣经 / 状态时使用本 skill。

## 操作规则

- **文件优先**：把既有的大纲、设定、角色、规则、章节、状态文件视为权威，一切从文件出发。
- **不覆写 canon**：除非用户明确要求改写，否不改写作者已成文的内容；拿不准时追加带日期的备注，而非直接重写。
- **静态基础与运行时态分开**：
  - 静态基础（Foundation）：前提、世界法则、卷章地图、角色卡、规则书。
  - 运行时态（Runtime）：当前状态、活跃钩子、章节摘要、焦点、审计漂移、最新章节产物。
- **受保护上下文始终可见**：作者意图、当前焦点、硬状态事实、角色事实、规则书、活跃钩子、用户的直接指令。
- **只压缩低优先级的历史**：较早的章节正文、过时的摘要、情绪 / 标题轨迹、背景说明。
- **使用时间—事实账本**：续写时以 `current_state.md` 的"章节感知事实表"作为"某角色在第 N 章时知道什么"的硬边界。角色不可引用 **起始章 > 当前章** 的事实；角色忘记已习得的事实需显式说明；新出现的事实须在事实表新增行；已推翻的事实标"已推翻-参见第 N 章"。
- **治理钩子账本**：维护 `pending_hooks.md` 的 13 列账本——停滞用 `stale (距=N)`、受阻用 `blocked on hook-X (阻=N)` 字面标记。同族钩子（同主题 + 同回收对象）准入时合并到既有 hook 而非新增行；章末把已兑现 / 已推翻的 hook 显式标 `resolved`。诊断标记（stale / blocked / promoted / depends_on）供审计维 6 直接引用。
- **报告具体创建或变更了哪些文件**：不要声称某个章节或某本书"已经存在"，除非文件真的被写入了。

## 从这里开始

1. **识别模式**：
   - 续写已有书：存在大纲 / 设定 / 章节 / 状态文件。
   - 创建新书：用户给了一句灵感、书名、题材，或要求写一本新小说。
   - 导入 / 续写：用户手里有旧章节，但状态文件很弱或缺失。
   - 转向 / 修订：用户要求换方向、改写、修补，或从特定位置续写。
   - 查看进度 / 仪表盘：用户要求看进度、打开仪表盘、看设定完成度、人物关系或读章节（模式 F）。
2. 动任何文件之前先读 `references/file-contract.md`。
3. 根据所选模式读 `references/workflow.md`。
4. 新书或基础文件缺失时读 `references/templates.md`。

## 续写流程（模式 B）

1. 清点项目文件。找 `books/` / `story/` / `chapters/` / `outline/` / `roles/` / `story_bible.md` / `volume_outline.md` / `book_rules.md` / `author_intent.md` / `current_focus.md`。
2. 从连续章节文件和 / 或 `chapters/index.json` 确定最新落硬盘章节——不要只信一份陈旧的状态文件。
3. 读工作集：
   - `story/author_intent.md`
   - `story/current_focus.md`
   - `story/outline/story_frame.md` 或 `story/story_bible.md`
   - `story/outline/volume_map.md` 或 `story/volume_outline.md`
   - 相关 `story/roles/**/*.md`
   - `story/book_rules.md`
   - `story/current_state.md`
   - `story/pending_hooks.md`
   - `story/chapter_summaries.md` 最近几行
   - 最近 1–3 章结尾
4. 需求改变焦点或方向前，先创建或更新 `story/runtime/chapter-NNNN.intent.md` 章节意图。
5. 从选定的上下文起草，而不是把整个项目都堆进来。
6. **双层质量门禁**：
   - 第一层驻场初筛（7 点）→ 不过则改 → 过则进第二层。
   - 第二层 37 维连续审计 + 审-改循环（见 Chapter Quality Gate 第二层）。体裁裁剪 → 逐维报告 → 修订 → 回头重过 → 留痕 `audit-drift.md`。
   - 两轮全过 → 落盘：写 `chapter-NNNN.intent.md`、`chapters/NNNN_<title>.md`、更新 `chapters/index.json`、写 `chapter_summaries.md` 行（含 **章节 delta**：本章改变了哪些事实 / 推了哪些伏笔 / 关系状态——见 templates.md"章节 delta"）、更新 `current_state.md`（事实表 + 关系）、更新 `pending_hooks.md`（按诊断列治理规则）、新建快照 `snapshots/<NNNN>/`。
   - **不要重写仪表盘**——它运行时自会读取最新文件。
7. **事实验证**：落盘前回查 `current_state.md` 事实表——角色是否引用了 起始章 > 当前章 的事实？新出现的事实是否在事实表新增行？已推翻的事实是否标"已推翻-参见第 N 章"？

## 新书流程（模式 A）

1. 只问那些无法安全推断的关键项：语言、书名、题材、目标篇幅 / 章数、一句话前提。若用户给的足够，直接推进。
2. 按 `references/templates.md` 创建项目目录结构。
3. 写第一章前先产出基础文件：
   - `story/author_intent.md`
   - `story/current_focus.md`
   - `story/outline/story_frame.md`
   - `story/outline/volume_map.md`
   - `story/roles/<层级>/<姓名>.md`
   - `story/book_rules.md`
   - `story/pending_hooks.md`
   - `story/current_state.md`
   - `story/chapter_summaries.md`
4. 用户若要求立刻写正文，也须在基础文件就绪、且开篇章节意图明确后，再写第一章。

## 章节质量门禁

分两层执行。**初筛**即本节 7 点——不过直接改写；**深化**即第 37 维审计（`references/audit-dimensions.md`）——与初筛共同构成"初筛 + 深化"双保险，不是二选一。

### 第一层：驻场初筛（7 点，每章必过）

在定稿前快速过一遍：

- 本章节是否推进了至少一个具体压力、关系、线索、目标或钩子。
- 主角的行为是否符合既定的动机与当前约束。
- 没有角色知道他们不可能知道的事实（对照 `current_state.md` 的"章节感知事实表"，角色不可引用 **起始章 > 当前章** 的事实）。
- 资源、伤势、地点、时间、库存、关系状态与承诺是否与状态文件一致。
- 结尾让局面发生了真正的变化，而非只是烘托气氛或重复前文。
- 文风是否符合既定的语言、体裁、视角、基调与篇幅目标。
- 审计发现若未当场修复，必须落记录。

初筛通过 → 进入第二层；初筛没过 → 直接修订后重新初筛。

### 第二层：37 维连续审计 + 审-改循环

按 `references/audit-dimensions.md` 执行。

1. **体裁裁剪**：按 `book.json.genre` 查 audit-dimensions 末尾的"体裁裁剪速查表"，得本章要跑维度清单。critical 与 warning 必须过；info 可视篇幅跳过。结构单纯的日常向短篇（<3000 字/章）可只跑 7–10 个核心维。
2. **Auditor**：逐维出报告——每条给 `pass / fail` + 证据 + 建议。
3. **Reviser**：对没过维度逐条修订；修订完**回头从第 1 维再过一遍**（禁止只过"刚才没过的那条"，防修 A 打坏 B）。
4. **分级落地**：critical 必须修到 pass；warning 必须修或在 `audit-drift.md` 留"已知漂移 + 原因 + 计划"；info 仅记录。
5. **上限**：连跑 3 轮仍过不了的 warning，允许在 `audit-drift.md` 留"已知漂移"记录后强制收工（防死循环）。
6. **留痕**：每轮审计的发现与处置写入 `story/audit-drift.md`（见 templates.md 的 audit-drift 模板，分"已修复 / 已知漂移"两节）。

## 模式 F：查看进度 / 写作仪表盘

当用户要求看进度、打开仪表盘、查看设定完成度、人物关系或在仪表盘内阅读章节时使用。仪表盘是一份**自包含的 HTML 模板**（`references/dashboard.html`），通过 **File System Access API**（或 `webkitdirectory` 回退）在运行时读取书源文件并实时计算渲染。它**不嵌入任何数据**，永远反映最新文件，因此只需生成一次、无需每章重写。

### 使用步骤

1. 定位当前书（若有多本且未指定，让用户选）。
2. 确认 `books/<book-id>/dashboard.html` **存在**：
   - 若不存在，把模板 `dragon-writer/references/dashboard.html` 复制到书文件夹（仅此一次）。
   - 若已存在，**不要覆盖**——模板是通用的，数据在运行时读取。
3. 告诉用户：**直接双击 `dashboard.html` 即可打开仪表盘**，第一次选择书文件夹授权后自动重连（IndexedDB 持久化句柄），后续零交互。建议 Chrome / Edge。

### 仪表盘工作原理（给用户的说明）

- 第一次打开会弹出文件夹选择框，选中本书根目录并授权。
- 授权后仪表盘读取 `book.json` / `chapters/*.md` / `story/*.md`，实时计算：写作进度、设定完成度、设定内容全文、人物关系图、审计漂移、章节阅读。
- 句柄记入 IndexedDB；下次打开自动重连（权限失效才需再选一次）。
- 浏览器不支持 File System Access API 时，提供"兼容模式选择"（`<input webkitdirectory>`）。
- 所有数据均在本地读取，绝不上传；仪表盘不修改任何书文件。

### 何时调用模式 F

- **按需**：用户要求看进度 / 仪表盘 / 完成度 / 人物关系 / 读章节时。
- **新建 / 导入时**（模式 A / 模式 C）：确保书文件夹下有一份仪表盘模板（缺失则注入一次）。
- **不要每章重写仪表盘**——它运行时自会读取最新文件，无需重新生成。

不要声称"给用户看了仪表盘"报告仪表盘路径与打开方式即可。

## 平台说明

本 skill 刻意保持工具无关：在 Codex 中使用其自带的 shell / 文件编辑工具；在 Claude Code 中按需要使用 Read / Write / Edit / Task 工具；在 opencode 中使用等价的文件与命令工具。整个工作流依赖的是文件契约，而非某一款具体 CLI。
