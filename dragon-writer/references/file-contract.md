# Dragon Writer 文件契约

请始终遵循这些约定。若已有项目使用不同命名，请把这些名字映射到对应的角色，而不是重命名一切。

## 规范布局

```text
books/<book-id>/
  book.json
  dashboard.html
  chapters/
    index.json
    0001_<title>.md
  story/
    author_intent.md
    current_focus.md
    book_rules.md
    current_state.md
    pending_hooks.md
    chapter_summaries.md
    style_guide.md
    audit_drift.md
    outline/
      story_frame.md
      volume_map.md
    roles/
      major/<name>.md
      minor/<name>.md
    runtime/
      chapter-0001.intent.md
      chapter-0001.context.json
      chapter-0001.rule-stack.md
      chapter-0001.trace.md
    snapshots/
      0/
      1/
```

中文项目可使用 `主要角色/` 与 `次要角色/` 代替 `major/` 与 `minor/`。保留既有文件夹名。

## 兼容命名

优先读新文件，但旧文件存在时也要读：

| 角色 | 首选 | 旧名 / 别名 |
| --- | --- | --- |
| 故事基础 | `story/outline/story_frame.md` | `story/story_bible.md`, `setting.md`, `world.md` |
| 情节地图 | `story/outline/volume_map.md` | `story/volume_outline.md`, `outline.md`, `plot.md` |
| 角色 | `story/roles/**/*.md` | `story/character_matrix.md`, `characters.md` |
| 规则书 | `story/book_rules.md` | `rules.md`, `writing_rules.md` |
| 作者方向 | `story/author_intent.md` | `author.md`, `intent.md` |
| 近期焦点 | `story/current_focus.md` | `focus.md`, `next.md` |
| 当前状态 | `story/current_state.md` | `state.md`, `truth.md` |
| 钩子 | `story/pending_hooks.md` | `hooks.md`, `foreshadowing.md` |
| 摘要 | `story/chapter_summaries.md` | `summaries.md` |

## 文件职责

`book.json`
: 仅元数据：id、title、language、genre、status、targetChapters、chapterWordCount、created/updated 时间戳。

`dashboard.html`
: 自包含的进度视图模板，由 skill 在创建 / 导入书时注入书文件夹（模式 A / 模式 C 各注入一次，之后不再重写）。通过 File System Access API（或 `webkitdirectory` 回退）在运行时读取书源文件，实时计算并渲染：写作进度、设定完成度、设定内容全文、人物关系图、审计漂移、章节阅读。不嵌入任何数据，永远反映最新文件。绝不修改任何书文件。

`author_intent.md`
: 长期创作方向。受保护上下文，不可压缩丢失。

`current_focus.md`
: 最近 1–3 章的优先事项。转向时用它来调整，而不是偷偷重写整份大纲。

`outline/story_frame.md`
: 静态基础：主题、基调、核心冲突、前台 / 背景故事、世界法则、质感、终局目标。不要在这里抄完整的人物弧线——指向角色档案即可。

`outline/volume_map.md`
: 弧线与章节地图。新书可以是卷级，导入续写可以是章节级。末尾附上节奏原则。

`roles/**/*.md`
: 一个角色一份文件：角色功能、欲望、恐惧、关系网、当前状态、秘密、言行指纹、成长弧线。

`book_rules.md`
: 可执行的规则：POV、禁手、体裁约束、力量 / 资源限制、命名规则、风格约束、硬定局锁。

`pending_hooks.md`
: 待回收的伏笔与铺陈（13 列账本）：id、start_chapter、type、status、last_advanced_chapter、expected_payoff、payoff_timing、depends_on、core_hook、promoted、pays_off_in_arc、half_life、notes。status 列供审计维 6 直接读取。

`current_state.md`
: 最新权威故事态：地点、时间、主角目标 / 约束、已知事实（章节感知事实表）、关系、伤势 / 资源、未消解的冲突。

`chapter_summaries.md`
: 每章一行耐久记录：title、characters、events、state_changes（含章节 delta：本章改变了哪些事实 / 推了哪些伏笔 / 关系状态变化——见 templates.md"章节 delta"）、hook_activity、mood、chapter_type。

`audit-drift.md`
: 审计漂移账本——Auditor 逐维审计的处置记录。分两节：**已修复**（章 + 维度 + 问题 + 修复动作）与**已知漂移**（章 + 维度 + 问题 + 原因 + 计划）。仪表盘的"审计漂移"小节直接渲染本文件。模式 B 每章、模式 E 改写后必更新。

`runtime/chapter-NNNN.intent.md`
: 给下一章的人类可读契约：goal、outline node、must keep、must avoid、style emphasis、hook agenda、recent evidence。

`runtime/chapter-NNNN.context.json`
: 可选的机器可读上下文。仅在平台适合结构化上下文时使用，否则 Markdown 上下文文件即可。

`snapshots/<n>/`
: 每章落盘后复制状态文件，让改写可以安全回滚。

## 权威顺序

文件冲突时，按以下优先级裁决：

1. 用户本次任务的直接指令。
2. 仅针对下一章的 `current_focus.md`。
3. `author_intent.md` 与 `book_rules.md`。
4. `current_state.md`、角色档案、`pending_hooks.md`。
5. `outline/story_frame.md` 与 `outline/volume_map.md`。
6. `chapter_summaries.md`。
7. 更早的章节正文。

Do not resolve major contradictions silently. Record the conflict in the chapter intent or ask the user if it changes canon.
