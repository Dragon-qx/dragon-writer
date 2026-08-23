# 账本一致性与审计盲区修复 · 实施计划

> **For agentic workers:** 按任务顺序执行，步骤使用 checkbox（`- [x]`）跟踪。改动落在 skill 源目录 `dragon-writer/`。

**日期：** 2026-08-23
**起因：** 对 `dw-novels/books/sao-zhai-shou-nv`（2 章产出）做全面审计，发现一批本 skill 机制本应拦住但没拦住的问题。本计划把每个问题追溯到机制根因，给出防复发的修复。

**目标：** 让"正文内部矛盾、账本与正文脱节、文件层分叉"三类问题在产出环节被机制性拦截，而不是靠下次人工审计兜底。

**Repo 根目录（本文所有路径相对它）：** `dragon-writer/`

---

## 问题 → 根因 → 修复 总表

| # | 实际问题（sao-zhai 案例） | 根因 | 修复任务 |
| --- | --- | --- | --- |
| 1 | `audit-drift.md`（有内容）与 `audit_drift.md`（空模板）并存 | `file-contract.md` 规范布局树写的是下划线旧名，与同文件兼容命名表自相矛盾 | T1 |
| 2 | 周大美同时存在于 `roles/major/` 与 `roles/minor/`，内容已分叉 | 契约没有角色晋升规则；无机器检查 | T2 |
| 3 | index.json wordCount 记 8000/5000，实际约 11400/6800；第1章超出 6000 目标近一倍 | 落盘不强制跑 `rebuild_index.py`，字数是手写的；validate 不核对 | T3 |
| 4 | fact-002「大学被背叛」标记第1章引入，正文一字未提 | 事实表无证据要求；`check_fact_chapters` 只查起始章非负 | T4 |
| 5 | 玉佩来历：第1章"不记得有" vs 第2章"记得捡到经过" | 审计包不含角色记忆/道具来历类事实的比对规则；道具账本无「来历」字段 | T5 |
| 6 | 年龄三版本：正文 20 岁生日前逃 vs 角色卡 21 岁来取/20 岁后逃/时间线 19 岁逃（卡内自相矛盾）；intent 要求"保留21岁悬念" | 审计包完全排除角色档案，canon 数字无处比对；卡内散述数字无集中锚点 | T6 |
| 7 | 第2章「你一个男的」（角色为女性） | 无性别称谓 lint；角色卡无性别字段 | T7 |
| 8 | 第1→2章睡觉安排断裂（谁睡哪没交代） | 无章间物理状态衔接检查；intent 模板无「前章末状态续接」 | T8 |
| 9 | 衣柜出现在正文但不在空间锚点 | 维38 只查"兼容"不查"登记完备" | T9 |
| 10 | 道具账本玉佩位置「手心/枕头下」vs 正文「抽屉」 | 维39 判定规则不含存放位置；落盘 checklist 无三核对 | T10 |
| 11 | hook-002 已基本揭尽仍 `progressing`；hook-007 老头警告已入正文仍 `last_advanced: 0` | 落盘无 hook 收敛复查步骤 | T11 |
| 12 | chapter-0002 intent 的必须场景/章末画面未产出，无偏离记录 | intent 无偏离记录机制 | T12 |
| 13 | chapter_summaries 第1章写「发现伤痕」（实际第2章才出现） | summaries 模板无"只记本章实际事件"约束 | T13 |
| 14 | book.json：status 仍 `outlining`、updatedAt 停在创建日、skillVersion 1.0.0（实际 3.9.0） | skeleton 硬编码 1.0.0；落盘不更新 book.json；无陈旧检测 | T14 |

---

## Global Constraints

- 向后兼容：既有书（含 sao-zhai）不迁移不阻塞；新检查对旧书产生 warning/error 时，error 需可用 `--strict` 之外的方式降级说明。
- 机器检查只做**确定性判定**（路径存在性、数字核对、引文命中、表格结构）；语义判断留给审计维度判定规则，两者不混写。
- 所有新检查进 `validate_book.py`（统一入口），字数/性别 lint 可复用 `_contract` helper；不新建脚本。
- 文档改动以 `file-contract.json` 为单一事实源，Markdown 文档（`file-contract.md` / `templates.md` / workflow）与其同步，杜绝本次发现的"同文档内自相矛盾"。
- 中文界面文本；新增代码注释用中文，风格与现有脚本一致。

---

## Task 1（P0）：消灭 audit 文件双名源头 + 别名并存检测

**Files:** `references/file-contract.md`、`scripts/validate_book.py`、`dragon-writer/tests/`

**根因细节：** `file-contract.md` L36 规范布局树写 `story/audit_drift.md`，与 L72 兼容命名表（canonical `story/audit-drift.md`，alias `audit_drift.md`）矛盾。创建书时模型按布局树建了下划线文件，之后按命名表又用连字符文件，产生双源。

- [x] 1.1 修 `file-contract.md` 规范布局树：`audit_drift.md` → `audit-drift.md`。
- [x] 1.2 `validate_book.py` 新增 `check_alias_conflicts`：对 `_contract` 中**所有** canonical/alias 对，若两者同时存在于书目录 → `error`（"规范名与别名并存：<alias> 与 <canonical>，请合并到规范名并删除别名"）。当前 `check_missing_files` 只处理"仅别名存在"的 warning。
- [x] 1.3 pytest：fixture 构造双文件书，断言 error 命中；仅规范名存在 → 通过。

## Task 2（P0）：角色晋升规则 + 同名双卡检测

**Files:** `references/file-contract.md`、`scripts/validate_book.py`、`dragon-writer/tests/`

- [x] 2.1 `file-contract.md`「文件职责」区新增**角色晋升规则**节：
  - minor → major 晋升 = **移动**文件（`minor/<name>.md` → `major/<name>.md`），不是复制；
  - 晋升时在卡内「角色功能」追加一行晋升记录（章号 + 晋升事件）；
  - 旧 minor 卡不留副本；若需保留历史，依赖章末快照（`snapshots/` 已含 `story/roles/**`），不在活跃目录留第二份。
- [x] 2.2 `validate_book.py` 新增 `check_role_name_conflicts`：`roles/major/` 与 `roles/minor/`（含中文别名目录）出现同名文件 → `error`。
- [x] 2.3 pytest：双卡 fixture → error；仅 major → 通过。

## Task 3（P0）：字数真值核对，禁止手写 wordCount

**Files:** `references/workflow-continue.md`、`references/file-contract.md`（事务流程）、`scripts/validate_book.py`、`dragon-writer/tests/`

**根因细节：** `rebuild_index.py` L43 的字数算法正确，但落盘事务不强制调用，index 数值由模型手写。同时无人对照 `book.json.chapterWordCount` 目标。

- [x] 3.1 `workflow-continue.md` 步骤 8 与 `file-contract.md`「章节落盘事务流程」步骤 5 明确写入：**落盘时禁止手写 wordCount，必须运行 `python scripts/rebuild_index.py <book-dir>`**，随后运行 `python scripts/validate_book.py <book-dir>`，两者任一 FAIL 则事务失败。
- [x] 3.2 `validate_book.py` 新增 `check_word_count_consistency`：
  - 用与 `rebuild_index.py` 完全相同的正则（抽到 `_contract` 或公共 helper，避免两处漂移）重算每章字数，与 index `wordCount` 偏差 > 5% → `error`；
  - 与 `book.json.chapterWordCount` 偏差 > 40%（双向）→ `warning`（附实际值，供作者决策放行或裁剪）。
- [x] 3.3 pytest：wordCount 偏差 fixture → error；超目标 40% → warning。

## Task 4（P0）：事实表证据链——引文必须能在来源章命中

**Files:** `references/templates.md`、`references/file-contract.md`、`scripts/validate_book.py`、`dragon-writer/tests/`

**根因细节：** fact-002 来自角色卡背景，被写成"第1章引入、确证"。事实表 schema 没有"正文证据"概念，`check_fact_chapters` 只查起始章 ≥ 0。

- [x] 4.1 `templates.md` + `file-contract.md` 事实表 schema 新增列 `evidence`（原文短引，≤30 字，来自 `introduced_chapter` 对应章节正文）。
- [x] 4.2 `validate_book.py` 扩展 `check_fact_chapters`：
  - 逐行解析 evidence（兼容无该列的旧表 → warning 提示升级）；
  - 引文去掉标点/空白后，在 `chapters/<introduced_chapter>` 正文（同样归一化）中查找：命中 → 通过；**不命中 → `error`**；evidence 为空 → `warning`。
  - 归一化规则：去除所有非 `[一-鿿A-Za-z0-9]` 字符，再子串匹配。fact-002 这类捏造事实将因找不到任何可命中的引文而暴露。
- [x] 4.3 审计维度联动：`audit-dimensions.md` 维 9（信息越界）判定规则追加一句：**"审计包内每条已知事实必须携带 evidence 引文；子代理发现正文与事实表 statement 冲突时按 critical 上报"**。
- [x] 4.4 pytest：捏造 fact（引文不存在）→ error；合法 fact → 通过。

## Task 5（P0）：道具「来历」字段 + 来历跨章单调性

**Files:** `references/templates.md`、`references/file-contract.md`、`references/audit-dimensions.md`、`scripts/validate_book.py`

**根因细节：** 玉佩在第1章是"来历不明"（fact-007 + 正文"不记得"），第2章变成"记得捡到经过"（fact-014）。道具账本只有 `previous_owner`（记的还是"床底灰尘中"），无来历叙事字段，冲突无处显形；事实表两条并存且 fact-007 未标 invalidated。

- [x] 5.1 道具账本 schema 新增列 `origin`（来历一句话，如"来历未知——主角不记得持有"）。治理规则：**origin 变化 = canon 变更**，须走"记录原值、新值、原因、生效章"流程，且对应旧事实必须标 `invalidated_chapter`。
- [x] 5.2 `validate_book.py` 新增 `check_fact_invalidation`：同一 `subject` 下，若章 N 新增事实与既有未失效事实存在同 `prop_id` 引用且 origin 字段变更，未同步 invalidate 旧事实 → `warning`（机器只做结构性提示，语义裁决留给审计）。
- [x] 5.3 `audit-dimensions.md` 维 39（道具追踪）判定规则追加：**"来历一致性：角色对同一道具获得过程的记忆/陈述跨章必须单调——'不记得/第一次见'与'记得获得经过'并存 = critical FAIL；同时核对账本 origin 字段"**。
- [x] 5.4 `templates.md` 维 39 对应的审计包裁剪说明：涉及既知道具时，审计包的"道具状态"必须含 `origin` 与最近两章的变化事件。

## Task 6（P0）：canon 数字锚点表——角色卡与正文的数字比对通道

**Files:** `references/templates.md`、`references/file-contract.md`、`references/audit-dimensions.md`、`references/workflow-continue.md`（审计包定义）

**根因细节：** 审计包设计上**完全排除角色档案**（防写作指引污染冷读），这本身合理；但角色卡里的硬数字（年龄、日期、身高、数量）是 canon 事实而非写作指引，审计因此永远看不到「卡说 21 岁、正文写 20 岁」。且苏小小卡内部散文区就有三个互斥年龄版本——卡内数字本身无集中锚点。

- [x] 6.1 角色卡模板新增区块 **「canon 数字锚点 Number Anchors」**（Foundation 稳定属性，紧随「角色功能」）：

  ```markdown
  ## canon 数字锚点 Number Anchors

  | anchor_id | 事项 | 值 | 生效章 | 依据 |
  | --- | --- | --- | ---: | --- |
  | anchor-001 | 当前年龄 | 20 | 1 | 正文自述 |
  | anchor-002 | 逃离家时年龄 | 19（20岁生日前几天） | 2 | 正文自述 |
  ```

  治理规则：**卡内散文区与正文中涉及该角色的硬数字，必须与锚点表一致**；锚点变更 = canon 变更流程。
- [x] 6.2 `workflow-continue.md` 7.1 审计包的「连续性事实」新增一个子节 **「canon 数字锚点（仅数字，不含写作指引）」**：从本章出场角色的角色卡锚点表裁剪，只给 anchor_id + 事项 + 值。明确注释：这与"审计包不含角色档案"不冲突——排除的是欲望/弧线/技法指引，数字锚点是可判定事实。
- [x] 6.3 `audit-dimensions.md` 维 3（设定冲突）判定规则追加：**"正文中角色相关数字（年龄/日期/尺寸/数量）与 canon 数字锚点表冲突 = critical FAIL；卡内散文与锚点表自相矛盾（创建/编辑卡时的自查项）= 上游错误，落 audit-drift"**。维 4 已声明"以角色卡数据时间线为逐章权威来源"，本条把权威来源真正送进审计视野。
- [x] 6.4 `validate_book.py` 新增 `check_number_anchor_selfconflict`（轻量）：同一角色卡锚点表内同一事项多行且值不同、且无生效章衔接 → `warning`。
- [x] 6.5 新书 / 转向流程（`workflow-new-book.md`、`workflow-redirect.md`）补一句：角色卡落盘前自查"锚点表 vs 卡内散文数字"一致。
- [x] 6.6 pytest：锚点表内部冲突 fixture → warning。

## Task 7（P1）：性别称谓 lint

**Files:** `references/templates.md`（角色卡模板）、`scripts/validate_book.py`、`dragon-writer/tests/`

**根因细节：** 第2章台词「你一个男的」指向女性角色，三轮审计未抓。属确定性可查的低级串行错误。

- [x] 7.1 角色卡模板（物理数据时间线之外）新增稳定属性字段 `性别`；skeleton 示例同步。
- [x] 7.2 `validate_book.py` 新增 `check_gender_address`（只报 `warning`，避免误伤）：
  - 扫描 `roles/**` 建立名字→性别表；
  - 对每章正文按句切分，正则 `(名字)([^。！？]{0,8})(一个|这个|那个)?(男的|男人|先生|哥们)` 或反向 `(男角色名)…(女的|姑娘|小姐)` → warning（附句号定位）。
  - 误报控制：只匹配引号外叙述 + 台词中直接以该名字为主语的句式；宁可漏报不误报阻断。
- [x] 7.3 pytest：「你一个男的」样句 fixture → warning 命中。

## Task 8（P1）：章间衔接——前章末状态续接

**Files:** `references/chapter-craft.md`、`references/templates.md`（intent 模板）、`SKILL.md`（初筛清单）

- [x] 8.1 intent 模板新增必填字段 **「前章末状态续接 Scene Carry-Over」**：上章末各在场角色的物理位置、姿态、着装、时间点（一行一个角色，从上一章结尾与 `chapter_summaries` 提取）。
- [x] 8.2 `SKILL.md` 驻场初筛从 9 点扩为 **10 点**，新增：**「★ 章间衔接：本章开场与上一章末尾的物理状态（谁在哪、什么姿势、穿什么、什么时间）显式衔接或有明确的时间/场景跳转标记；人物位置不得无交代地互换」**（sao-zhai 的"谁睡了床"断裂即此项 FAIL）。
- [x] 8.3 `chapter-craft.md` 章首三行入戏规则追加一句：若开场紧接上章，前三行内须出现至少一个上章末状态锚点（位置/物件/身体姿态任一）。

## Task 9（P1）：空间登记完备性

**Files:** `references/audit-dimensions.md`（维 38）、`references/workflow-continue.md`（落盘清单）

- [x] 9.1 维 38（空间一致性）判定规则追加：**"登记完备性：正文被人物交互的固定物件（家具、固定装置）必须能在该场景空间锚点的『方位/格局』或『关键物件位置』列找到；找不到 = FAIL（未登记空间元素），修复 = 正文改或锚点补登，二选一"**。
- [x] 9.2 `workflow-continue.md` 步骤 8 落盘清单在「current_state.md」后括注细化：**新增固定物件 / 布局变化 → 空间锚点登记（新列或新锚点行，遵循 valid_until 失效规则）**。

## Task 10（P1）：道具账本三核对 + 存放位置一致性

**Files:** `references/audit-dimensions.md`（维 39）、`references/workflow-continue.md`

- [x] 10.1 维 39 判定规则追加：**"存放位置字段必须与本章正文末尾该道具的实际位置一致，否则 FAIL"**（玉佩「手心/枕头下」vs「抽屉」即此项）。
- [x] 10.2 落盘 checklist 显式写明道具账本**三核对**：数量、状态、存放位置——三项逐一对着正文末态核对，不允许只改数量。

## Task 11（P1）：hook 生命周期收敛复查

**Files:** `references/workflow-continue.md`、`references/templates.md`（chapter delta）

- [x] 11.1 落盘步骤 8 在 `pending_hooks.md` 后括注：**钩子收敛复查——对本章 summary 的 events 逐项自问 advance / resolve / defer；notes 中出现"揭露 / 兑现 / 真相"字样的 hook 必须重新评估 lifecycle_status（揭尽 → resolved 或收窄为新子 hook，禁止已揭尽仍挂 progressing）；正文推进了某 hook 内容的，`last_advanced_chapter` 与 `chapters_since_advance` 必须同步**（hook-002 未收敛、hook-007 已入正文未推进均为本项 FAIL）。
- [x] 11.2 章节 delta 模板补充一行固定自查项：「hook 账本与本章 events 双向核对（正文有的账本必须有、账本 advanced 的正文必须真有）」。

## Task 12（P1）：intent 偏离记录

**Files:** `references/templates.md`（intent 模板）、`references/workflow-continue.md`、`references/file-contract.md`（intent 职责）

- [x] 12.1 intent 模板新增尾部区块 **「实际偏离 Deviation Log」**：落盘时若实际产出与 intent 的 goal / 必须场景 / required end-of-chapter change 不一致，追加一行（偏离项 + 原因 + 去向章），无偏离则写"无"。禁止改写 intent 原有内容（intent 是写前契约，偏离只追加）。
- [x] 12.2 `file-contract.md` `runtime/chapter-NNNN.intent.md` 职责描述同步追加该区块说明；`workflow-continue.md` 步骤 8 落盘清单加入「intent 偏离记录」。

## Task 13（P2）：chapter_summaries 只记本章实际事件

**Files:** `references/templates.md`（chapter_summaries 模板）

- [x] 13.1 模板 events 列规则追加：**"events 只允许记录本章正文实际发生的事件；'计划中下章出现'的内容禁止提前写入"**（sao-zhai 第1章 summary 写「发现伤痕」、fact-005 记「旧伤痕」，实际第2章才出现，均违反本条）。事实表 evidence 机制（T4）从机器侧兜底同类问题。

## Task 14（P2）：book.json 生命周期字段

**Files:** `dragon-writer/assets/book-skeleton/book.json`、`scripts/init_book.py`、`scripts/validate_book.py`、`references/workflow-continue.md`、`dragon-writer/tests/`

**根因细节：** skeleton 的 `skillVersion` 硬编码 `"1.0.0"`；`init_book.py` 有 stamp 逻辑（读 `_meta.json`）但该书显然未经 init_book 落盘（或 `_meta.json` 缺失回退）。落盘事务的"按序写入"清单里没有 `book.json`。

- [x] 14.1 skeleton `book.json` 的 `skillVersion` 改为空串占位 + 注释指向 init_book stamp；确认 init_book 在 `_meta.json` 缺失时 warning 而非静默写 1.0.0。
- [x] 14.2 `workflow-continue.md` 步骤 8「按序写入」清单追加 `book.json`（status → drafting / updatedAt → 本次时间；skillVersion 在大版本升级时随 canon 变更流程更新）。
- [x] 14.3 `validate_book.py` 扩展 `check_book_json`：
  - `chapters/index.json` 存在 status=completed 的章节而 `book.json.status == "outlining"` → `warning`；
  - `book.json.updatedAt` 早于任一章节 `updatedAt` → `warning`；
  - `skillVersion` 与 `_contract.skill_version()` 非空且不一致 → `info`。
- [x] 14.4 pytest：status 陈旧 fixture → warning。

---

## 实施顺序与验证

1. **P0 文档源头修复**（T1.1、T2.1、T5.1、T6.1、T13、T14.1）：先消灭契约自相矛盾，否则下游检查建立在错误契约上。
2. **P0 机器检查**（T1.2、T2.2、T3.2、T4.2、T5.2、T6.4）：`validate_book.py` 一次性扩展，测试先行。
3. **P0 审计通道**（T4.3、T5.3、T6.2、T6.3）：把 canon 数字锚点与事实 evidence 送进审计包。
4. **P1**（T7–T12）、**P2**（T13 收尾、T14）。
5. **端到端回归**：对 sao-zhai 现状跑新版 `validate_book.py`，预期命中至少：audit 双文件 error、周大美双卡 error、wordCount 双 error、fact-002 证据不命中 error、性别称谓 warning、status 陈旧 warning——作为修复有效性的验收清单（该书本身的正文修复不在本计划范围）。
