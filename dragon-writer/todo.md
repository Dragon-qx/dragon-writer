# Dragon Writer 优化 TODO

本文档记录当前 skill 的完整改造建议。实施顺序遵循：先修正确性，再重建文件契约，然后重构 skill，最后完善测试与发布。

## 第一批：P0 正确性与发布阻断项

### 1. 统一质量门禁口径

- [x] 将所有“7 点初筛”统一为“9 项驻场初筛”。
- [x] 将所有“37 维”“四十维”“40 维”统一为“41 个候选深化审计维度”。
- [x] 明确标准表述：`9 项驻场初筛 + 41 个候选深化审计维度，按体裁和章节风险裁剪执行`。
- [x] 将“审计发现若未修复必须留痕”定义为执行规则，不计入 9 项初筛。
- [x] 删除 `audit-dimensions.md` 中维度 9、29、34、35、36 的重复定义，改为交叉引用。
- [x] 将审计维度按编号排序，或增加唯一维度索引。
- [x] 同步修改 `SKILL.md`、`references/workflow.md`、`references/audit-dimensions.md` 和 `README.md`。

### 2. 统一仪表盘生成策略

- [x] 删除 `references/workflow.md` 中“每章重新生成 dashboard.html”的指令。
- [x] 统一为：新建或导入书籍时复制一次，已存在时不覆盖。
- [x] 明确每章只更新书源数据，仪表盘运行时读取最新文件。
- [x] 确认 `SKILL.md`、workflow、file contract 和 README 使用相同描述。

### 3. 修复仪表盘首次渲染

- [x] 修复 `Router.current = 'overview'` 与 `switchTab(current)` 提前返回的问题。
- [x] 将 Router 初始 current 改为 `null`，或支持 `switchTab(tab, { force: true })`。
- [x] 确保首次进入时调用当前组件的 `onEnter()`。
- [x] 确保带 `#overview`、`#settings`、`#settings-content`、`#chars`、`#read` 打开时正确激活对应面板。
- [x] 在书籍数据加载完成后强制渲染当前标签。

### 4. 修复刷新和切书后的旧数据

- [x] 为所有组件增加统一 `invalidate()` 生命周期。
- [x] 载入新书前调用 `GraphEngine.destroy()`。
- [x] 载入新书时重置 `Overview._rendered`、`Settings._rendered`、`SettingsContent._rendered`、`Characters._rendered` 和 `Reader._rendered`。
- [x] 重置 Reader 的章节索引、搜索文本、搜索结果、高亮和字体临时状态。
- [x] 重置人物筛选和搜索状态。
- [x] 修复 `Store.reset()`，使其正确通知订阅者或清除订阅。
- [x] 考虑增加 `dataVersion`，组件只缓存相同数据版本的渲染结果。（已通过 invalidateAll() 统一失效机制实现同等效果）
- [x] 刷新完成后重新计算当前标签，而不是继续显示旧 DOM。

### 5. 补回当前焦点及运行时文件加载

- [x] 在 `loadBook()` 中读取 `story/current_focus.md`。
- [x] 将 `current_focus` 加入 `result.files`。
- [x] 确认总览“当前焦点”卡片能够显示真实内容。
- [x] 决定并统一加载以下文件：
  - [ ] `author_intent.md`（暂不加载，无对应 UI 消费者）
  - [x] `current_focus.md`
  - [ ] `pending_hooks.md`（暂不加载，无对应 UI 消费者）
  - [x] `current_state.md`
  - [x] `chapter_summaries.md`
  - [x] `audit-drift.md`
  - [x] `style_guide.md`
- [x] 删除没有任何消费者的无效加载，或完成对应 UI 接入。

### 6. 消除标签访问顺序依赖

- [x] 将 `Store.settings` 初始值从 `{}` 改为 `[]`。
- [x] 将完成度计算提取为 `computeSettingCompletion(files)` 纯函数。
- [x] 让“设定完成度”和“设定内容”独立调用该函数。
- [x] 确保直接进入“设定内容”不会调用不存在的 `.find()`。
- [x] 禁止任何页面依赖用户先访问其他页面。

### 7. 修复兼容模式路径匹配

- [x] 选择目录后从 `webkitRelativePath` 确定唯一根目录前缀。
- [x] 去掉根目录前缀后，使用标准化相对路径精确匹配文件。
- [x] 禁止使用任意 `endsWith('/book.json')` 作为权威文件匹配方式。
- [x] 角色文件只匹配根目录下的 `story/roles/`。
- [x] 章节文件只匹配根目录下的 `chapters/`。
- [x] 排除 `snapshots/`、`runtime/`、rewrite 和备份目录。
- [x] handle 模式直接进入 `story/roles`，不要递归扫描整本书。
- [x] 防止快照或备份中的同名文件被当成当前权威文件。

### 8. 补全旧文件名映射

- [x] 建立唯一的集中式 `FILE_CONTRACT` 或等价配置。
- [x] 为每种文件定义 canonical path 和 aliases。
- [x] 补齐故事框架别名：`story_bible.md`、`setting.md`、`world.md`。
- [x] 补齐情节地图别名：`volume_outline.md`、`outline.md`、`plot.md`。
- [x] 补齐角色别名：`character_matrix.md`、`characters.md`。
- [x] 补齐规则别名：`rules.md`、`writing_rules.md`。
- [x] 补齐作者方向别名：`author.md`、`intent.md`。
- [x] 补齐焦点别名：`focus.md`、`next.md`。
- [x] 补齐状态别名：`state.md`、`truth.md`。
- [x] 补齐钩子别名：`hooks.md`、`foreshadowing.md`。
- [x] 补齐摘要别名：`summaries.md`。
- [x] 让文档、脚本和仪表盘读取同一份映射，避免多处重复维护。

### 9. 修复 Markdown 链接安全

- [x] 对链接属性值转义 `&`、`<`、`>`、`"` 和 `'`。
- [x] 去除 URL 的控制字符和前导空白后再检查协议。
- [x] 只允许 `http:`、`https:`、`mailto:`、`#` 和明确允许的相对路径。
- [x] 禁止 `javascript:`、`data:`、`vbscript:` 和 `file:`。
- [x] 为外部链接增加 `rel="noopener noreferrer"`。
- [x] 添加 CSP，至少限制 `connect-src 'none'`、`object-src 'none'` 和 `base-uri 'none'`。
- [x] 所有 Markdown 内容统一通过一个安全渲染出口。
- [ ] 增加 Markdown 属性注入、协议绕过和控制字符测试。

### 10. 修复章节搜索

- [x] 不再用 `indexOf()` 为每个重复匹配确定位置。
- [x] 依据渲染后的 `<mark>` 序号维护当前搜索项。
- [x] 搜索只操作文本节点，避免字符串替换破坏 HTML 标签和属性。
- [x] 切换章节时清空旧搜索结果和高亮。
- [x] 输入新搜索词后自动滚动到第一个命中。
- [x] 上一项和下一项按匹配索引循环。
- [ ] 增加同词多次出现、大小写混合和 Markdown 标记内搜索测试。

### 11. 修复章节排序

- [x] 使用 `localeCompare(..., { numeric: true })`。
- [x] 优先按解析后的章节号排序。
- [x] 覆盖 `1_x.md`、`2_x.md`、`10_x.md` 等非补零旧文件。
- [x] 对无法解析章号的文件给出明确排序和告警规则。

### 12. 修复 GraphEngine 生命周期

- [x] 保存 resize handler 引用。
- [x] 在 `destroy()` 中移除 window resize 监听器。
- [x] 重新初始化前先调用 `destroy()`。
- [x] 未实现缩放时不要拦截 wheel 事件。
- [x] 若保留“画布可平移”的文档描述，则真正实现画布平移。
- [x] 若不实现平移，则删除 README 中的相关承诺。
- [x] 主题切换后调用 GraphEngine redraw。
- [x] 为角色数量较多的项目限制模拟时长或优化 O(n²) 斥力计算。

## 第二批：重建文件契约和持久状态

### 13. 分离静态基础与动态状态

- [x] 角色档案只保存稳定属性：功能、欲望、恐惧、秘密、言行指纹和长期弧线。
- [x] 将当前关系、伤势、位置、能力状态迁入 `current_state.md`。
- [x] 删除角色档案中的易漂移”当前状态”，或明确将角色档案纳入快照。
- [x] 在 file contract 中明确 Foundation 与 Runtime 的边界。

### 14. 调整权威顺序

- [x] 将作者不可妥协项和规则书硬定局锁置于短期 `current_focus.md` 之前。
- [x] 建议权威顺序：用户明确指令 → 硬锁/不可妥协项 → 当前焦点 → 当前状态/角色事实/钩子 → 故事框架/卷纲 → 摘要 → 旧章节。
- [x] 用户明确改 canon 时记录原值、新值、原因和生效章。
- [x] canon 变更时更新相关状态并创建快照。
- [x] 拿不准时记录冲突或询问，不要向 canon 文件随意追加模糊备注。

### 15. 定义完整快照契约

- [x] 快照目录统一使用四位编号：`0000`、`0001`。
- [x] 每个快照增加 `manifest.json`。
- [x] 明确快照至少包含：
  - [x] `current_state.md`
  - [x] `pending_hooks.md`
  - [x] `chapter_summaries.md`
  - [x] `current_focus.md`
  - [x] `audit-drift.md`
  - [x] `chapters/index.json`
- [x] manifest 记录 snapshotVersion、chapter、createdAt、includedFiles、文件哈希、skillVersion 和 schemaVersion。
- [x] 禁止静默覆盖已有快照。
- [x] 为缺失或哈希不匹配的快照提供恢复提示。

### 16. 将章节落盘改成事务式流程

- [x] 每章先在 `runtime/` 生成章节意图和草稿。
- [x] 审计、修订和账本校验完成前不写入正式章节目录。
- [x] 写正式文件前创建旧状态快照。
- [x] 按确定顺序写正文、index、摘要、状态和钩子。
- [x] 全部写入后运行一致性验证。
- [x] 完成后创建章末快照。
- [x] 任一步失败时保留草稿，并报告失败文件与恢复方式。
- [x] 避免章节正文成功但 state/hooks/index 只更新一部分。

### 17. 重写流程禁止隐式删除

- [x] 模式 E 首先生成受影响文件和章节清单。
- [x] 用户确认前将候选稿写入 `story/runtime/rewrites/<rewrite-id>/`。
- [x] 用户确认前不删除正文、不修改权威状态。
- [x] 明确”分支”是 Git 分支还是文件级候选稿，禁止含糊使用。
- [x] 真正删除前创建恢复点。
- [x] 删除后报告范围、是否可恢复及恢复位置。

### 18. 增加 schema 版本

- [x] 在 `book.json` 中增加 `schemaVersion`。
- [x] 在 `book.json` 中增加 `skillVersion`。
- [x] 为 `book.json` 定义 JSON Schema。
- [x] 为 `chapters/index.json` 定义 JSON Schema。
- [x] 为快照 manifest 定义 JSON Schema。
- [x] 为可选 chapter context 定义 JSON Schema。
- [x] 定义 schema 升级和旧项目迁移规则。

### 19. 改造事实表

- [x] 为每个事实增加稳定 `fact_id`。
- [x] 分离事实真伪与角色是否知道。
- [x] 建议字段：statement、subject、truth_status、introduced_chapter、invalidated_chapter、source_chapter、knower、known_from_chapter、confidence、notes。
- [x] 一个角色一条认知记录，避免多人混写在同一单元格。
- [x] 被推翻的事实保留历史记录，不删除或覆盖。
- [x] 新事实必须记录来源章。
- [x] 缺少证据时写 `unknown`，不得自动补成 canon。

### 20. 改造钩子账本

- [x] 将生命周期与健康状态分离。
- [x] `lifecycle_status` 使用 open/progressing/deferred/resolved/rejected。
- [x] `health_status` 使用 healthy/stale/blocked。
- [x] 增加 `blocked_on` 和 `chapters_since_advance` 独立字段。
- [x] 布尔字段统一使用 true/false，不混用 yes/no。
- [x] `depends_on` 只保存 hook ID。
- [x] 合并钩子时记录 `merged_from`。
- [x] resolved 钩子保留，不删除。
- [x] stale 阈值由 half_life 确定性计算。

### 21. 改造道具账本

- [x] 禁止道具消失后删除账本行。
- [x] 增加 active/consumed/destroyed/lost/transferred/pawned 状态。
- [x] 增加 acquired_chapter 和 disposed_chapter。
- [x] 增加 previous_owner 和 event_id。
- [x] 数量变化必须关联显式事件。
- [x] 考虑增加只追加的道具事件表，当前账本只保存最新汇总。

### 22. 改造空间锚点

- [x] 增加 scene_id 和 canonical_name。
- [x] 增加 aliases。
- [x] 增加 coordinate_reference。
- [x] 增加 valid_from_chapter 和 valid_until_chapter。
- [x] 增加 last_change_event。
- [x] 战损、改建或重布置时保留旧版本，不直接抹除历史。
- [x] 审计报告引用具体 scene ID 和版本。

### 23. 定义章节 index 条目

- [x] 为 `chapters/index.json` 定义 number、file、title、status、wordCount、createdAt 和 updatedAt。
- [x] 明确章节正文文件是权威来源，index 可重建。
- [x] index 与文件冲突时按明确规则裁决。
- [x] 增加自动重建 index 的脚本。

### 24. 处理 Markdown 表格转义

- [x] 定义单元格中 `|` 的转义方式。
- [x] 定义单元格换行方式。
- [x] 读取器与写入器使用同一套规则。
- [x] 或将机器账本迁移至 JSON/JSONL，Markdown 仅保留人类摘要。

### 25. 补齐正式模板

- [x] 增加 `style_guide.md` 模板。
- [x] 增加 `fanfic_canon.md` 模板。
- [x] 增加 `parent_canon.md` 模板。
- [x] 增加 `emotional_arcs.md` 模板。
- [x] 增加项目敏感内容/措辞约束模板。
- [x] 增加 `chapter-NNNN.intent.md` 正式模板。
- [x] 增加快照 manifest 模板。
- [x] 增加完整 `chapters/index.json` 模板。
- [x] 增加 rewrite manifest 模板。

### 26. 删除或定义幽灵文件

- [x] 决定 `chapter-NNNN.context.json` 是否正式支持。
- [x] 决定 `chapter-NNNN.rule-stack.md` 是否正式支持。
- [x] 决定 `chapter-NNNN.trace.md` 是否正式支持。
- [x] 若支持，补齐用途、创建时机、模板和必需性。
- [x] 若不支持，从规范布局中删除。

### 27. 统一术语和编号

- [x] 统一使用 `chapter intent`，不再混用 `chapter_memo`。
- [x] 统一使用”41 个候选审计维度”。
- [x] 统一使用 `runtime rewrite candidate`，不将文件候选稿笼统称为分支。
- [x] 统一 canonical path 和 alias path 的定义。
- [x] 章节、快照和 runtime 文件统一四位补零编号。

## 第三批：重构审计体系

### 28. 使用四态审计结果

- [x] 将审计结果改为 pass/fail/not_applicable/unknown。
- [x] 缺少输入证据时必须是 unknown。
- [x] 体裁不适用时使用 not_applicable。
- [x] 禁止因为文件缺失而判 pass。
- [x] 每个 fail 必须附原文证据、影响和最小修复建议。

### 29. 改为风险驱动审计

- [x] 每章固定运行 9 项硬检查。
- [x] 每章运行体裁无关 critical 项。
- [x] 根据章节标签激活空间、战斗、道具、感情、同人和时代等维度。
- [x] 每卷末、高潮、重大转向或用户要求时运行完整 41 维。
- [x] 修订后重跑受影响维度及其依赖闭包，而非无条件重跑全部维度。
- [x] 为本章审计清单记录激活原因和跳过原因。

### 30. 结构化体裁矩阵

- [x] 不再在单个 Markdown 单元格中混写 `38(critical)`。
- [x] 将 enabled、severity 和 activation reason 分为独立字段。
- [x] 使用 YAML/JSON 或确定性脚本生成章节审计清单。
- [x] 为未知 genre 定义默认审计策略。

### 31. 修复维度边界冲突

- [x] 为每个维度定义 owns。
- [x] 为每个维度定义 excludes。
- [x] 为每个维度定义 depends_on。
- [x] 为每个维度定义 severity escalation。
- [x] 解决”未学剑却一剑封喉”同时归维 4 和维 41的问题。
- [x] 检查其余维度是否存在重复职责。

### 32. 明确敏感内容检查来源

- [x] 规定敏感内容/措辞约束来源于用户或项目文件。
- [x] 文件缺失时输出 unknown/not_configured。
- [x] 区分平台安全规则与作者项目约束。
- [x] 禁止模型自行发明敏感词表。
- [x] 禁止把题材内容本身错误判为违规。

### 33. 控制审计日志体积

- [x] `audit-drift.md` 只保留未解决问题、实际修复和会影响未来章节的决策。
- [x] 不记录所有 pass。
- [x] 每卷结束后将已修复历史压缩成卷级摘要。
- [x] 未解决 critical/warning 漂移保持完整。
- [x] 为审计日志制定压缩但不丢失活跃问题的规则。

## 第四批：精简和拆分 Skill

### 34. 将 `SKILL.md` 改为路由器

- [x] 保留触发范围、核心不可违反规则、模式识别和 reference 路由。
- [x] 保留总体落盘与安全规则。
- [x] 移出完整 9 项检查正文。
- [x] 移出仪表盘详细功能说明。
- [x] 移出 A/B 流程重复内容。
- [x] 移出 41 维审计细节。
- [x] 将 `SKILL.md` 控制在约 70–100 行。
- [x] 将正文改为命令式/不定式表达。
- [x] 修复”否不改写”为”否则不改写”。
- [x] 明确每章都创建章节意图，不仅在方向改变时创建。

### 35. 按模式拆分 workflow

- [x] 新建 `references/workflow-new-book.md`。
- [x] 新建 `references/workflow-continue.md`。
- [x] 新建 `references/workflow-import.md`。
- [x] 新建 `references/workflow-redirect.md`。
- [x] 新建 `references/workflow-rewrite.md`。
- [x] 新建 `references/workflow-dashboard.md`。
- [x] `SKILL.md` 明确不同模式只读取对应 reference。
- [x] 删除原 workflow 中重复流程。

### 36. 为长 reference 增加目录和检索提示

- [x] 为 workflow 增加目录。
- [x] 为 templates 增加目录。
- [x] 为 file contract 增加目录。
- [x] 为 audit dimensions 增加目录。
- [x] 在 `SKILL.md` 中提供按维度编号和章节标题检索的提示。
- [x] 避免 references 之间深层嵌套跳转。

## 第五批：资源和目录结构

### 37. 将输出资源移入 `assets/`

- [x] 将 `references/dashboard.html` 移到 `assets/dashboard.html`。
- [x] 将真实书籍模板移到 `assets/book-skeleton/`。
- [x] 直接复制模板文件，不让模型从 Markdown 代码块重新拼装。
- [x] 更新 SKILL、workflow 和 README 中的资源路径。

### 38. 重构目标目录

- [x] 将仓库整理为以下结构：

```text
dragon-writer/
  SKILL.md
  agents/
    openai.yaml
  references/
    file-contract.md
    workflow-new-book.md
    workflow-continue.md
    workflow-import.md
    workflow-redirect.md
    workflow-rewrite.md
    workflow-dashboard.md
    audit-dimensions.md
  assets/
    dashboard.html
    book-skeleton/
      book.json
      chapters/index.json
      story/...
  scripts/
    init_book.py
    validate_book.py
    rebuild_index.py
    snapshot_book.py
    rollback_book.py
    select_audit.py
  tests/
    fixtures/
    test_contract.py
    test_dashboard.*
```

- [x] README 仅保留在源码仓库，发布 skill 包时排除。

## 第六批：确定性脚本

### 39. 增加 `init_book`

- [x] 生成 slug。
- [x] 创建目录。
- [x] 复制书籍骨架。
- [x] 写入时间戳和 schemaVersion。
- [x] 注入 dashboard。
- [x] 创建初始快照。
- [x] 避免覆盖已有书籍目录。

### 40. 增加 `validate_book`

- [x] 检查缺失文件。
- [x] 检查 JSON 合法性和 schema。
- [x] 检查章节编号连续性。
- [x] 检查 index 与文件一致性。
- [x] 检查 Markdown 表格列数。
- [x] 检查事实起始章是否合法。
- [x] 检查 hook 依赖是否存在。
- [x] 检查道具数量是否为非负整数。
- [x] 检查快照 manifest 和哈希。
- [x] 输出可读诊断和机器可读结果。

### 41. 增加 `rebuild_index`

- [x] 从章节文件确定性重建 index。
- [x] 支持非补零旧章节名。
- [x] 检测重复章号和无效文件名。
- [x] 支持 dry-run 和差异输出。

### 42. 增加快照和回滚脚本

- [x] `snapshot_book` 默认支持 dry-run。
- [x] `rollback_book` 默认只输出影响范围。
- [x] 验证所有目标路径都位于当前书根目录。
- [x] 禁止覆盖已有快照。
- [x] 回滚前创建恢复点。
- [x] 删除动作必须通过显式参数开启。
- [x] 支持验证快照哈希。

### 43. 增加 `select_audit`

- [x] 输入 genre、chapter tags、fanfic mode、chapter length 和 risk flags。
- [x] 输出激活维度、severity、激活原因、缺失输入和跳过原因。
- [x] 未知题材使用安全默认清单。
- [x] 尽量只依赖 Python 标准库，降低跨平台依赖。

## 第七批：仪表盘完善

### 44. 清理未完成和死亡代码

- [x] 删除或完整实现 `recentBooks`。
- [x] 删除或完整实现 `loadingIndicator`。
- [x] 删除或使用 `Store.on/off`。
- [x] 删除或使用 `tabLoading`。
- [x] 删除或正确使用 `parseAsync`。
- [x] 删除未使用的 Utils 方法。（检查确认所有方法均被使用）
- [x] 将错误的 `Router.switch()` 调用改为真实 API。
- [x] 减少静态面板和动态模板中的重复 ID/重复结构。

### 45. 完善加载反馈

- [x] loading 状态变化时显示和隐藏 spinner。
- [x] 加载时禁用重复选择按钮。
- [x] 显示当前读取阶段。
- [x] 出错时保留落地页、错误信息和重试入口。
- [x] 加载失败时不要把失败 handle 设为当前 handle。
- [x] JSON 解析错误应报告具体文件和原因。

### 46. 改善兼容模式刷新

- [x] 当前会话保存兼容模式选择的 `File[]`。
- [x] 点击刷新时重新读取现有 File 对象。
- [x] 只有切换目录时重新弹出选择框。
- [x] 文档说明页面重开后兼容模式需要重新选择目录。

### 47. 同步文档与实际 UI

- [x] 统一设定文件数量：当前代码含 style guide 时为 5 份，不应仍写 4 份。
- [x] 文档补充当前焦点和字数趋势。
- [x] 删除或实现“画布可平移”。
- [x] 将“后续零交互”改为权限有效时自动重连。
- [x] 删除或实现最近书籍列表。
- [x] 以真实功能清单作为 README 和 skill 描述的唯一来源。

### 48. 增加可访问性

- [x] tab 增加 id 和 aria-controls。
- [x] panel 增加 aria-labelledby。
- [x] 支持左右方向键切换标签。
- [x] 当前 tab 设置正确 tabindex。
- [x] canvas 提供文字版关系替代内容。
- [x] 主题按钮增加动态 aria-label。
- [x] 搜索结果增加 aria-live。
- [x] 图表不只依赖颜色区分角色层级。
- [x] 尊重 prefers-reduced-motion。

### 49. 改善大书性能

- [x] 章节读取和解析按需执行。
- [x] Reader 只渲染当前章节。
- [x] 设定全文首次进入标签时再解析。
- [x] 大型角色图限制模拟时长。
- [x] 字数趋势在章节过多时聚合采样。
- [x] 避免异步 Markdown 解析重复 split 全文。
- [x] 确保 Markdown 代码块、列表和表格不在分块边界损坏。

### 50. 改善 TXT 导出

- [x] 清理导出文件名中的非法字符。（已实现：`replace(/[\/\\:*?"<>|]/g, '_')`）
- [x] 明确使用 UTF-8。（Blob type 为 `text/plain;charset=utf-8`）
- [x] 保留章节标题和合理空行。
- [x] 可选导出纯正文并去除 Markdown 标记。
- [x] 大书导出避免一次性构造超大字符串。

## 第八批：触发描述和元数据

### 51. 改写 frontmatter description

- [x] 覆盖创建、导入、续写、转向、改写、回滚和仪表盘。
- [x] 明确这是文件化、跨会话、持久状态的长篇小说工作流。
- [x] 明确不用于一次性短文生成或普通文案润色。
- [x] 将 opencode/Claude Code/Codex 平台兼容说明移到正文，减少触发元数据噪声。
- [x] 可参考以下描述：

> 面向文件化、跨会话长篇虚构项目的创建、导入、续写、转向、章节改写与安全回滚工作流；维护作者意图、大纲、角色、事实、钩子、道具、空间状态、章节摘要和进度仪表盘。用于需要持久故事状态与连续性审计的小说项目；不用于一次性短文生成或仅做普通文案润色的任务。

### 52. 修复 `agents/openai.yaml`

- [x] 将 short_description 控制在 25–64 字符。
- [x] 确保 default_prompt 明确包含 `$dragon-writer`。
- [x] 可使用：`Create, continue, audit, and recover file-backed novels.`
- [x] 可使用默认提示：`Use $dragon-writer to inspect my file-backed novel and continue it from its latest validated state.`
- [x] description 精确且误触发可控时保留 `allow_implicit_invocation: true`。
- [x] 若仍容易误触发，暂时设为 false。

## 第九批：README、图片和编码

### 53. 修复 README

- [x] 删除末尾 TODO。
- [x] 修复不存在的 `references/dashboard.png` 链接。
- [x] 更新真实功能列表。
- [x] 修正审计维数和初筛数量。
- [x] 修正自动重连描述。
- [x] 更新项目结构图。
- [x] 增加许可证说明或链接。
- [x] 发布 skill 包时排除 README。

### 54. 清理图片

- [x] 删除 `tab-overview.png` / `tb-overview.png` 中的一份。
- [x] 删除 `tab-read.png` / `tb-read.png` 中的一份。
- [x] 删除 `tab-settings.png` / `tb-settings.png` 中的一份。
- [x] 删除 `tab-settings-content.png` / `tb-settings-content.png` 中的一份。
- [x] 将测试截图移到 `tests/artifacts/`，或从发布包排除。
- [x] 统一截图命名规范。

### 55. 固定编码和换行

- [x] 增加 `.editorconfig`，设置 UTF-8、LF 和文件末尾换行。
- [x] 增加 `.gitattributes`，统一文本换行策略。
- [x] 确认 Windows PowerShell、Codex、Claude Code 和 opencode 都能正确读取中文。
- [x] CI 检查 UTF-8 和尾部换行。

## 第十批：验证与测试

### 56. Skill 静态验证

- [x] 在 CI 安装 PyYAML。
- [x] 运行官方 `quick_validate.py`。
- [x] 检查 frontmatter 只包含 name 和 description。
- [x] 检查 skill 目录名与 name 一致。
- [x] 检查 openai.yaml 字符数约束。
- [x] 检查 Markdown 本地链接。
- [x] 检查引用的契约文件是否存在。
- [x] 检查审计维度编号唯一。
- [x] 检查是否遗留 TODO。
- [x] 检查发布包不含 README、重复图片和测试产物。

### 57. 文件契约测试 fixture

- [x] 标准新书。
- [x] 使用全部旧别名的旧书。
- [x] 缺少状态文件的导入书。
- [x] index 陈旧但章节文件正确的书。
- [x] 章节编号不连续的书。
- [x] 包含多本书的项目。
- [x] 含快照和 rewrite 文件的书。
- [x] 文件名含中文、空格和特殊字符的书。
- [x] 单元格包含 `|` 和换行的账本。
- [x] 同人、番外、现代、仙侠等不同体裁。

### 58. 仪表盘单元测试

- [x] 测试路径标准化和精确匹配。
- [x] 测试完整 alias 映射。
- [x] 测试章节排序。
- [x] 测试 Markdown 安全渲染。
- [x] 测试设定完成度计算。
- [x] 测试事实和角色解析。
- [x] 测试重复搜索命中。
- [x] 测试字数统计。
- [x] 测试 current_focus 加载。
- [x] 测试切书和刷新后的组件失效。

### 59. 仪表盘浏览器测试

- [x] 首次打开。
- [x] 直接访问每个 URL hash。
- [x] 从总览直接进入设定内容。
- [x] 刷新当前书。
- [x] 连续切换两本不同书。
- [x] webkitdirectory 兼容模式。
- [x] 权限失效后的恢复。
- [x] 深色、浅色和自动主题。
- [x] 大章节和大量章节。
- [x] 无角色、单角色和重复角色名。
- [x] TXT 导出。
- [x] Markdown 注入样例。
- [x] 纯键盘和无障碍导航。
- [x] 开发时允许模块化，最终构建为自包含单文件 HTML。

### 60. Skill 前向测试

- [x] 测试”创建一本新仙侠小说”。
- [x] 测试”继续写下一章”。
- [x] 测试”导入 20 章旧稿并续写”。
- [x] 测试”从第 23 章重写但保留后续比较”。
- [x] 测试”下一章临时切换反派视角”。
- [x] 测试”打开人物关系和写作进度”。
- [x] 测试”旧项目文件名不符合新规范，但不要重命名”。
- [x] 测试”状态文件与最后一章冲突，只诊断不修改”。
- [x] 检查是否只加载必要 reference。
- [x] 检查是否避免擅自改 canon 或删除文件。
- [x] 检查是否正确处理 unknown。
- [x] 检查是否只有真实写入后才报告完成。
- [x] 检查跨章事实、钩子、道具和空间状态是否持续一致。

## 最终验收标准

- [x] 文档中只存在一套质量门禁和审计口径。
- [x] 新旧文件名映射可靠且只有一个权威来源。
- [x] 新建、续写、导入、转向和重写均有明确且可恢复的事务流程。
- [x] 任何破坏性回滚都先预览影响范围并创建恢复点。
- [x] 缺少证据时审计使用 unknown，不会假装 pass。
- [x] 快照可验证、不可静默覆盖、能够恢复。
- [x] 仪表盘首次加载、刷新和切书均显示最新数据。
- [x] 仪表盘不会从快照或备份中误读权威文件。
- [x] 仪表盘 Markdown 渲染无法执行注入代码或上传书籍数据。
- [x] 设定内容页不依赖访问顺序。
- [x] 重复章节搜索可正确定位每个匹配项。
- [x] skill 采用渐进式加载，不为无关模式加载大型 reference。
- [x] 发布包不包含 README、重复图片、测试截图或无关文件。
- [x] 官方 skill 校验、契约测试、单元测试和浏览器测试全部通过。
