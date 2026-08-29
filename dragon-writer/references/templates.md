# Dragon Writer 模板

创建新书或回填缺失文件时使用这些模板。用户提供的事实要原样保留，不魔改。

## 目录

- [book.json](#bookjson)
- [author_intent.md](#author_intentmd)
- [current_focus.md](#current_focusmd)
- [outline/story_frame.md](#outlinestory_framemd)
- [outline/volume_map.md](#outlinevolume_mapmd)
- [roles/major/<name>.md](#rolesmajornamemd)
- [book_rules.md](#book_rulesmd)
- [pending_hooks.md](#pending_hooksmd)
- [current_state.md](#current_statemd)
- [chapter_summaries.md](#chapter_summariesmd)
- [chapters/index.json](#chaptersindexjson)
- [audit-drift.md](#audit-driftmd)
- [style_guide.md](#style_guidemd)
- [fanfic_canon.md](#fanfic_canonmd)
- [parent_canon.md](#parent_canonmd)
- [emotional_arcs.md](#emotional_arcsmd)
- [chapter-NNNN.intent.json](#chapter-nnnnintentjson)
- [快照 manifest](#快照-manifest)
- [rewrite manifest](#rewrite-manifest)
- [章节 delta](#章节-delta)

---

## book.json

```json
{
  "id": "<book-id>",
  "title": "<title>",
  "language": "zh",
  "genre": "<genre>",
  "status": "outlining",
  "targetChapters": 200,
  "chapterWordCount": 3000,
  "chapterMinChars": 3000,
  "chapterTargetChars": 3300,
  "chapterMaxChars": 4500,
  "chapterLengthGateFromChapter": 1,
  "createdAt": "<ISO timestamp>",
  "updatedAt": "<ISO timestamp>",
  "schemaVersion": "1.0.0",
  "skillVersion": "<由 init_book.py 盖章，勿手写>"
}
```

> `chapterMinChars` 是不可低于的交付线，`chapterTargetChars` 是规划值，`chapterMaxChars` 是软上限；统一按去空白字符统计。`chapterLengthGateFromChapter` 默认 1；导入旧稿时可设为“最后一个导入章 + 1”，只豁免历史原稿，不豁免后续新章。旧书没有新字段时，`chapterWordCount` 同时作为下限与目标。`skillVersion` 由 `scripts/init_book.py` 从 `_meta.json` 读取盖章，**禁止手写**；续写每章落盘时同步 `status`（outlining → drafting）与 `updatedAt`。

## author_intent.md

```markdown
# Author Intent

## 核心承诺 Core Promise

## 长期方向 Long-Horizon Direction

## 不可妥协项 Non-Negotiables

## 读者体验 Reader Experience
```

## current_focus.md

```markdown
# Current Focus

## 当前焦点 Active Focus

## 局部覆写 Local Override

## 必须避开 Must Avoid

## 接下来 1-3 章 Next 1-3 Chapters
```

## outline/story_frame.md

```markdown
# Story Frame

## 主题与基调 Theme And Tonal Ground

## 前台故事 / 背景故事 Foreground Story / Background Story

## 核心冲突与对手 Core Conflict And Opposition

## 世界法则与质感 World Laws And Texture

## 终局目标 Endgame Objective
```

终局目标须可外部验证，不能只是空泛的"变得更强"或"复仇"。

## outline/volume_map.md

```markdown
# Volume Map

## 弧线结构 Arc Structure

## 情感曲线 Emotional Curve

## 钩子种子与回报图 Hook Seed And Payoff Map

## 人物弧线运动 Character Arc Movement

## 节奏原则 Pacing Principles
```

导入续写的场景：应先写"已完成章节回顾"，再写"续写地图"。

## roles/major/<name>.md

> 角色档案 = **稳定属性** + **数据时间线**。稳定属性（功能、欲望、恐惧、秘密、言行指纹、长期弧线）只在方向性转向时修改；「物理 / 逻辑数据时间线」为**章节锚定的追加式 Runtime 区块**——每章只新增变化点行、禁止修改旧行。易漂移的"当前关系 / 伤势 / 位置"仍不写入档案，归入 `current_state.md`。

```markdown
# <Name>

## 基本信息 Basic Info
- 性别：男 / 女

## canon 数字锚点 Number Anchors
> 角色硬数字（年龄 / 日期 / 尺寸 / 数量）的集中权威表。卡内散文区与正文中涉及该角色的硬数字**必须与锚点表一致**；锚点变更 = canon 变更（记录原值、新值、原因、生效章）。审计维 3 以本表为正文数字比对的依据；validate_book 检查表内自相矛盾。

| anchor_id | 事项 | 值 | 生效章 | 依据 |
| --- | --- | --- | ---: | --- |
| anchor-001 | 当前年龄 | 17 | 1 | 正文自述 |
| anchor-002 | 身高 | 5尺2寸 | 1 | 出场基线 |

## 角色功能 Story Function

## 欲望·恐惧·创伤 Desire / Fear / Wound

## 秘密与信息边界 Secrets And Information Boundary

## 言行指纹 Speech And Behavior Fingerprint

## 社交边界指纹 Social Boundary Fingerprint
> 只写稳定倾向：建立信任的速度与条件、陌生 / 熟悉时的称呼差异、允许身体接触与秘密披露的条件、如何表达亲近或拒绝。当前对某人的关系状态不写这里，写 `current_state.md`「关系许可账本」。

## 成长弧线 Arc

## 物理数据时间线 Physical Data Timeline
> 章节锚定，只记变化点：出现变化才新增一行。首行 = 出场基线。无变化不新增。
> 维度列由 book_rules.md「物理数据维度」声明，列名必须与声明完全一致——题材决定声明哪些列：都市/恋爱/成人 声明「三围」，仙侠/古风 通常不声明三围，只声明身高/体重/体型外貌快照。**不声明的列不要出现在表格里**。

| 章 | 身高 | 体重 | 体型/外貌快照 | 变化事件 |
| ---: | ---: | --- | --- | --- |
| 1 | 5尺2寸 | 108斤 | 清瘦少年，粗布麻衣，目光沉静 | 出场基线 |
| 24 | 5尺4寸 | 128斤 | 筑基重塑后身姿挺拔，气质沉凝 | 突破金丹·肉身重塑 |

## 逻辑数据时间线 Logical Data Timeline
> 维度由 book_rules.md「逻辑数据维度」声明；维度列名必须与声明完全一致。章节锚定，只记变化点；取最后一行的值为当前权威值。

| 章 | 修为境界 | 主修功法 | 神识强度 | 变化事件 |
| ---: | --- | --- | --- | --- |
| 1 | 练气三层 | 《寒心诀》一层 | 常 | 出场基线 |
| 24 | 金丹中期 | 《寒心诀》三层·凝霜成剑 | 初窥识海 | 突破金丹 |
```

## book_rules.md

```markdown
# Book Rules

## POV 与叙事距离 POV And Narrative Distance

## 题材规则 Genre Rules
> 记录作品选择使用的类型承诺、叙事惯例与可选技法，不是允许 / 禁止创作的题材清单。混合、实验或未分类作品可写「自定义」，skill 不据此缩窄内容范围。

## 硬定局锁 Hard Canon Locks

## 力量 / 资源 / 时间限制 Power / Resource / Time Limits

## 禁手 Forbidden Moves

## 风格约束 Style Constraints

## 年代约束 Era Constraints

## 物理数据维度 Physical Data Dimensions
> 角色卡「物理数据时间线」的列清单（「章」「变化事件」两列固定，其余列由此声明）。
> 不同题材声明不同维度：仙侠/古风→身高/体重/体型外貌快照；都市/恋爱/成人→身高/三围/体型外貌快照；
> 科幻→身高/体重/改造等级…
> 维度列名必须与角色卡表格列完全一致；**不声明的列（如仙侠题材的三围）不要出现在角色卡表格里**。

| dim_id | 维度名 | 单位/取值口径 | 说明 |
| --- | --- | --- | --- |
| phy-001 | 身高 | 尺寸（尺/寸）或 cm | 当前身高 |
| phy-002 | 体重 | 斤 或 kg | 当前体重 |
| phy-003 | 体型/外貌快照 | 一句话 | 体型与外貌描述 |

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

## pending_hooks.md

> 13+ 列账本。`lifecycle_status` 与 `health_status` 直接供审计维 6（伏笔检查）按字面标记升级，停滞 / 受阻标记是 Auditor 写报告的直接证据——请保留字面 token。

```markdown
# Pending Hooks

| hook_id | start_chapter | type | lifecycle_status | health_status | last_advanced_chapter | expected_payoff | payoff_timing | depends_on | blocked_on | chapters_since_advance | core_hook | promoted | pays_off_in_arc | half_life | merged_from | notes |
| --- | ---: | --- | --- | --- | ---: | --- | --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |
| hook-001 | 0 | premise | open | healthy | 0 |  |  |  |  | 0 | yes | yes | 主线·第一卷 | 10 |  | Initial book promise. |
```

列含义：
- **lifecycle_status**：`open` / `progressing` / `deferred` / `resolved` / `rejected`。
- **health_status**：`healthy` / `stale` / `blocked`。
- **status 诊断标记**：停滞用 `stale (距=N)`、受阻用 `blocked on hook-X (阻=N)`（N 由 LLM 根据最近一次推进章节之差推算，字面值供 Auditor 引用）。
- **promoted**（true/false）：是否从架构师种子升级为主线承重伏笔。仅 promoted=true 的 stale/blocked 才允许升到 critical。
- **pays_off_in_arc**：计划在哪个弧线/卷回收（供审计维 6 判断结构）。
- **depends_on**：上游 hook ID（仅保存 hook ID）。
- **blocked_on**：受阻对象（独立字段）。
- **chapters_since_advance**：自上次推进以来经过的章节数（独立字段）。
- **half_life**（半衰期）：超过 N 章未推进时触发 info 级提醒。stale 阈值由 half_life 确定性计算。
- **merged_from**：合并钩子时记录来源 hook ID。

**钩子治理规则**（续写时遵守）：
- 准入/合并：新钩子若与既有 hook"同主题 + 同回收对象"→ 合并到既有 hook，不新增行，记录 `merged_from`。
- 收敛：章末应将"已兑现/已推翻"的 hook 显式标 `resolved` / `rejected`，禁止让完成态的 hook 长期挂 `open`。
- resolved 钩子保留，不删除。

## current_state.md

```markdown
# Current State

## 进度 Progress
- Current chapter: 0

## 地点与时间 Location And Time

## 事件时间轴 Event Timeline（追加式故事时钟）

> 记录正文实际发生的事件及耗时，不把“计划在下一章发生”的内容提前写入。章节号不是时间单位：一章可持续数分钟或跨越多年，同一分钟也可跨章。

| event_id | chapter | sequence | start_time | end_time | elapsed | location | participants | preconditions | event | outcome | presentation |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evt-001 | 1 | 1 | 第 1 日·申时 | 第 1 日·酉初 | 约一时辰 | 甲字七号舍 | 主角、林逸 | 主角刚入门 | 两人初次交谈并约定次日合练 | 达成一次合练约定，尚未建立私人信任 | scene |

**治理规则**：
- `sequence` 表示同章内顺序；并发事件可使用相同 sequence 并在 notes / event 中说明。
- `presentation` 使用 `scene / summary / ellipsis`：场景化、概述、留白跳过。
- 中长跳时后的第一个场景尽快给出时间、地点、人物状态三类锚点；无效等待 / 通勤 / 例行日程优先 summary 或 ellipsis。
- 新事件的 preconditions 必须已经发生；旅行耗时、伤势恢复、训练进展等不能超出 `book_rules.md` 已建规则。

## 主角 Protagonist
- status:
- goal:
- constraints:

## 人物关系 Relationships

> 给仪表盘看的当前关系摘要。权威证据与行为权限见下方「关系许可账本」。

## 关系许可账本 Relationship Permission Ledger

> 维 27 的硬边界。一对角色一行，关系可以不对称；若 A 对 B 与 B 对 A 的信任 / 称呼 / 接触许可不同，在 `asymmetry` 明写。初识角色可以快速靠近，但每次跃迁都必须有催化事件和正文证据。

| pair_id | A | B | first_met_chapter | prior_history | current_stage | trust_basis | allowed_familiarity | private_knowledge_shared | address_touch_boundary | last_change_chapter | catalyst_event_id | evidence | asymmetry |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| rel-001 | 主角 | 林逸 | 1 | 无 | 有一次合练约定的相识者 | 林逸以食物示好；主角接受一次合练邀请 | 可直呼姓名、谈公开的修炼目标；不可替对方做主或默认托命 | 无 | 无亲昵称呼；无主动身体接触 | 1 | evt-001 | “明日寅时，一起练一趟？” | 林逸更外向，主角仍保留戒心 |

**治理规则**：
- `current_stage` 是事实摘要，不是自动生成台词的标签；正文权限以 `allowed_familiarity`、`private_knowledge_shared` 与 `address_touch_boundary` 为准。
- 共享一次危机、一次谈心或强烈吸引可以造成大幅跃迁，但须记录双方当场选择、催化事件与后效；禁止用旁白直接补出“像认识多年”。
- 关系每次变化更新本行并保留事件依据；若需完整历史，可在 notes 或独立追加式关系事件表记录，不抹掉旧证据。
- 关系亲密不自动授予信息权限；秘密披露还须同步写入「章节感知事实表」。

## 已知事实 Known Truths（章节感知事实）

> 以本表为"某角色在第 N 章时知道什么、不知道什么，以及如何知道"的硬边界。
> 续写时：角色不可引用 `known_from_chapter > 当前章` 的事实；同场出现不等于共享全部信息；角色忘记已习得的事实需有失忆、欺骗、误解等显式说明。

| fact_id | statement | subject | truth_status | introduced_chapter | invalidated_chapter | source_chapter | knower | known_from_chapter | confidence | evidence | acquisition_mode | acquisition_event_id | acquisition_evidence | notes |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- | --- | --- | --- | --- |
| fact-001 | 主角出身 | 主角 | 当前为真 | 1 | — | 1 | 主角 | 1 | 确证 | “我从河西来” | self_knowledge | evt-001 | “我从河西来” | 第一人称自述 |

## 资源 / 伤势 / 库存 Resources / Injuries / Inventory

> 粗粒度资源 / 伤势 / 总状态，细粒度道具清单见下方「道具账本」。

## 道具账本 Prop Ledger（跨章道具追踪硬账本）

> 审计维 39（道具追踪）的判定基础。随身物件、弹药、消耗品、贵重品逐件登记——数量与存在的变化必须由显式事件驱动（获得/失去/消耗/赠予/被夺/典当/碎裂），**不可无痕 ±1**。
> 每章落盘时：把本章内所有"获得 / 消耗 / 丢失 / 赠予"事件对应到账本行；清零或新增行须注明事件。

| prop_id | 名称 | 类别 | 数量 | 容量单位 | 归属角色 | 存放位置 | 状态 | acquired_chapter | disposed_chapter | previous_owner | origin | event_id | 最近变化章 | 最近变化事件 | 备注 |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- |
| prop-001 | 回春丹 | 丹药 | 3 | 枚 | 主角 | 储物袋乙格 | active | 12 | — | — | 散修集市购得 | evt-012 | 12 | 购买（散修集市） | 疗伤用，每枚止血清创 |
| prop-002 | 青锋剑 | 法器 | 1 | 柄 | 主角 | 背上剑鞘 | active | 3 | — | — | 师尊所赠 | evt-003 | 3 | 获赠（师尊） | 下品法器 |
| prop-003 | 下品灵石 | 货币 | 300 | 枚 | 主角 | 储物袋甲格 | active | 1 | — | — | 入门时宗门发放 | evt-001 | 14 | 购买功法消耗 50 | — |

**列含义**：prop_id（项目唯一 ID）、名称（**全文统一名**，维 39 名字一致性的硬性锚点）、类别（丹药 / 法器 / 符箓 / 货币 / 信物 / 衣物 / 杂物…）、数量（整数，非负）、容量单位（枚 / 株 / 锭 / 斛…）、归属角色、存放位置（储物袋甲格 / 袖中 / 背上剑鞘 / 洞府石床…）、状态（active / consumed / destroyed / lost / transferred / pawned）、acquired_chapter（获得章）、disposed_chapter（处置章）、previous_owner（前主）、origin（来历一句话，如"散修集市购得"/"来历未知——主角不记得持有"）、event_id（数量变化必须关联显式事件）、最近变化章、最近变化事件（谁在哪一章做了什么导致本行变化）、备注。

**治理规则**：
- 新道具入章 → 准入：本行新增，最近变化章 = 本章，事件 = 来源；origin 必填。
- 道具状态/数量变化 → 修改本行，不可另起同名行（防"名字漂移"）。
- **存放位置变化** → 同步改本行存放位置字段（本章正文末尾该道具实际位置即账本值）。
- **origin 变化 = canon 变更** → 记录原值、新值、原因、生效章，并把 current_state 事实表中对应旧事实标 `invalidated_chapter`（防"不记得有这块玉佩"与"记得捡到经过"并存）。
- 道具消失（碎裂 / 被夺 / 赠出 / 典当 / 耗尽）→ 数量归 0 或状态改为 consumed/destroyed/lost，事件必填。禁止删除账本行。
- 消耗品（丹药 / 符箓 / 灵石）每用一次减一次——禁止"昨天吃两枚今天还有三枚"。

## 空间锚点 Spatial Anchors（场景内固定布局）

> 审计维 38（空间一致性）的判定基础。每个反复出现的场景在本表登记一次固定布局，后续同场景跨章描写均以此为准；**物件位置变化必须有显式事件**（拆建、战损、重新布置）。
> 新场景首次出现时建立锚点；首次返回时对账。

| scene_id | canonical_name | aliases | coordinate_reference | 方位 / 格局 | 出入口 | 关键物件位置 | valid_from_chapter | valid_until_chapter | last_change_event | 建立章 | 最近更新章 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| scene-001 | 青云门外门弟子舍（甲字七号） | 甲字七号 | — | 坐北朝南，一明一暗；明间起居、暗间卧榻 | 南向双扇门，门外青石甬道 | 东墙木案（灯盏居北）、西墙兵器架、北墙通暗间小门 | 3 | — | — | 3 | — | — |
| scene-002 | 藏经阁三层 | — | — | 八角形中厅，八面经橱按八卦方位排列 | 仅西南角木梯通往二层 | 中厅八角石台（镇阁阵眼）、离位禁制封印铜简若干 | 7 | — | — | 7 | 21 | 战损：震位经橱倒塌 |

**列含义**：scene_id（稳定唯一 ID）、canonical_name（**文内统一名**，不可同地异名）、aliases（别名清单）、coordinate_reference（坐标参考，可选）、方位 / 格局（朝向 + 几进 / 几间 / 形状）、出入口（方位 + 形式）、关键物件位置（方位词 + 物件 + 相对坐标）、valid_from_chapter（生效章）、valid_until_chapter（失效章）、last_change_event（最近变更事件）、建立章、最近更新章（拆建 / 战损 / 布置变化时填）、备注。

**空间一致性治理规则**：
- **首次出场**：描写完成时即建锚点；本场景相邻段落方位不能互斥。
- **跨章复访**：对照锚点 —— 固定物件方位不能变化；变化必须有一行"最近更新"。
- **移动合法化**：角色从 A 位置到 B 位置，描写中必须经过中间空间路径，不可瞬移（门廊 → 庭院 → 正厅）。
- **视角合法化**：限制视角下角色看不见其位置不可能看见的内容（隔墙背面 / 遮挡物后）。
- **视角变换 / 缩景**：大远景可改变绝对方位参考，但须在描写中明示（"从山脊回望"）。
- **战损 / 改建 / 重布置**：保留旧版本（在 `valid_until_chapter` 标注失效章，新建一条锚点），不直接抹除历史。

## 当前冲突 Current Conflict
```

列含义（事实表）：**fact_id**（稳定唯一 ID）；**statement**（一句可验证的陈述）；**subject**（事实主体）；**truth_status**（当前为真 / 已推翻-参见第 N 章 / 仅主角知情 / 多角色共有）；**introduced_chapter**（该事实首次进入文本的章节）；**invalidated_chapter**（该事实被推翻的章节）；**source_chapter**（证明事实成立的来源章）；**knower**（认知主体，一个角色一条认知记录）；**known_from_chapter**（该角色首次获知此事实的章节）；**confidence**（确证 / 推测 / unknown）；**evidence**（证明事实成立的来源章原文短引）；**acquisition_mode**（亲历 / 被告知 / 阅读 / 查证 / 推断 / 能力传输 / self_knowledge 等）；**acquisition_event_id**（对应事件时间轴）；**acquisition_evidence**（证明该 knower 获知的 `known_from_chapter` 原文短引）；**notes**（备注）。缺少获知证据时写 unknown，不得自动补成 canon。该表是审计维 9 与维 29 的判定基础。

## chapter_summaries.md

```markdown
# Chapter Summaries

| chapter | title | characters | events | state_changes | hook_activity | mood | chapter_type | story_time | elapsed | dramatic_change | knowledge_delta | relationship_delta | novelty_fingerprint |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

> **events 只允许记录本章正文实际发生的事件**——"计划在下一章才出现"的内容禁止提前写入本行或事实表（如"发现伤痕"若发生在第 N 章，不得写进第 N-1 章摘要）。事实表 evidence 机制从机器侧兜底同类问题（引文必须在来源章命中）。
> `novelty_fingerprint` 用紧凑格式记录 `POV / 戏剧问题 / 目标 / 阻碍 / 行动链 / 新信息 / 关系变化 / 结果或代价 / 开收尾功能`，供维 42 对照近 5–10 章。不要只写“推进剧情”。

## chapters/index.json

```json
{
  "chapters": [
    {
      "number": 1,
      "file": "0001_开篇.md",
      "title": "开篇",
      "status": "drafting",
      "wordCount": 3200,
      "createdAt": "<ISO>",
      "updatedAt": "<ISO>"
    }
  ]
}
```

## audit-drift.md

> 记录每轮审计的发现与处置。模式 B 每章、模式 E 改写后必更新。
> 仪表盘会读取本文件的"已知漂移"节渲染。

```markdown
# Audit Drift

## 已修复

### 第 N 章 · <章标题>
- **<维度名（编号）>**：<问题一句> → <修复动作>
- ...

## 已知漂移（已知问题 + 原因 + 计划）

### 第 N 章 · <章标题>
- **<维度名（编号）>**：<问题一句>
  - 原因：<为何暂未修：篇幅 / 留伏笔 / 与作者意图冲突…>
  - 计划：<何时 / 如何修，或为何决定保留>
- ...
```

**审计日志压缩规则**：
- `audit-drift.md` 只保留未解决问题、实际修复和会影响未来章节的决策。
- 不记录所有 pass。
- 每卷结束后将已修复历史压缩成卷级摘要。
- 未解决 critical/warning 漂移保持完整。

## style_guide.md

```markdown
# Style Guide

## 语言风格 Language Style
- 古白夹杂 / 白话 / 半文半白

## AI 标志语 / 套路清单（负面示例 + 改写）
> 以下词/句式是 AI 生成痕迹的高频标志。每 3000 字超过 1 次即触发审计 warning，同一章累计 ≥3 次升级为 blocking 必须修。

- **副词类**：仿佛 / 不禁 / 宛如 / 竟然 / 忽然 / 猛地 / 似乎 / 微微 / 缓缓 / 悄然 / 不由得 / 不由自主
- **套路表情/动作**：嘴角微勾 / 眸光一沉 / 眸光一冷 / 深吸一口气 / 眼中闪过 / 眼底浮现 / 眉梢微挑 / 轻轻叹了口气
- **句式类**：
  - 避免：他感到…… / 改写：直接写感受或动作（"他攥紧拳头"而非"他感到愤怒"）
  - 避免：他不禁…… / 改写：去掉"不禁"，直接写行为
  - 避免：这一刻，他明白了…… / 改写：以动作/画面收尾，而非总结性话语
  - 避免：他的心中…… / 改写：用具体感受替代抽象描述
- **转折滥用**：然而 / 但是 / 不过 在同一章内出现 >5 次 → 需替换为更多样的过渡方式
- **每段开头**：避免连续 3 段以上以"他/她"开头 → 交替使用场景描写、对话、内心独白开头
- **收尾模式**：避免连续 3 章以同类收尾（如均以"心中想道" / 均以总结性话语）→ 以动作/画面收尾

## 章首承接与章末断章（详见 chapter-craft.md）
> 本节是负面速查；完整技法库（开头类型库、断章技法库、体裁适配、续接 / 跳切策略）见 `references/chapter-craft.md`，起草前必读。
- **章首三行入戏**：前三行落在正在发生的事上。禁手：「经过昨夜的事……」「回想起……」「此刻的他，心情复杂」等回顾式承接；回顾前情 ≤2 句且必须夹带新信息
- **章末断章**：切在能量上升沿（危机切断 / 反转末句 / 半信息揭示 / 决定未执行 / 新变量闯入 / 静默余韵）。禁手：总结本章（「但这个发现足以让他睡一个好觉」）、金句升华（「命运的齿轮开始转动」）、宣布计划（「他要做的，就是……」）、情绪命名（「心中涌起一股暖流」）
- **元数据不入正文**：钩子推进、审计结论只进 `chapter_summaries.md` / `pending_hooks.md`，不写成正文末尾的斜体附注
- **功能变奏**：允许复用开头 / 收尾类型，但不得连续复用同一人物动作、信息功能、情绪效果与结果；类型清单见 chapter-craft.md

## 句式节奏
- 长短段交替：描写段可长（80-150 字），动作/对话段宜短（20-60 字）
- 避免连续 3 段以上同长度段落（段落长度标准差 < 平均长度的 15% → 审计 fail）
- 避免连续 3 段以上同句式开头

## 体裁爽点类型 Satisfaction Types
- 升级流：境界突破、越阶挑战、打脸

## 视角与叙事距离 POV And Narrative Distance
- 第三人称限制视角

## Voice Fingerprint（本章语气指纹）
- 本章情绪基调：
- 节奏要求（紧凑/舒缓/紧张）：
- 特殊文风约定：
```

## fanfic_canon.md

> 同人模式专用。无此文件则同人专属维度（34–37）不激活。

```markdown
# Fic Canon

## 原作信息 Parent Work
- 作品名：
- 作者：
- 分歧点（Point of Divergence）：

## 角色档案 Character Canons
### <角色名>
- 性格底色：
- 语癖 / 说话风格：
- 关键关系：

## 世界规则 World Rules
- 地理：
- 力量体系：
- 阵营关系：

## 关键事件时间线 Canon Event Timeline
| 事件 | 原作章节 | 时间点 |
| --- | --- | --- |
```

## parent_canon.md

> 番外模式专用。记录正典约束。

```markdown
# Parent Canon

## 正典事件约束 Canon Event Constraints
| 事件 | 发生章节 | 约束 |
| --- | --- | --- |

## 信息边界表 Information Boundary
| 信息 | 揭示章节 | 可用角色 |
| --- | --- | --- |
```

## emotional_arcs.md

> 审计维 25（弧线平坦）的判定基础。无此文件时由 current_state + 角色档案近似替代。

```markdown
# Emotional Arcs

## <主要角色名>
| 章节 | 情绪压力形态 | 触发事件 |
| --- | --- | --- |
| 1 | 好奇 | 入门 |
| 5 | 挫败 | 首次失败 |
```

## chapter-NNNN.intent.json

> 4.1 权威章节契约。字段由 `schemas/chapter-intent.schema.json` 定义；示例中的证据必须在草稿完成后替换为真实段落、短引和当前草稿 SHA-256。不要用占位内容运行门禁。

```json
{
  "schemaVersion": "4.1",
  "chapter": 12,
  "dramaticQuestion": "主角是否在暴露身份前拿到证词",
  "pov": "第三人称限制视角：主角",
  "plannedTargetChars": 3300,
  "timeArchitecture": {
    "start": "雨夜三更，县衙后门",
    "end": "约一刻钟后，档案房内",
    "elapsed": "约一刻钟",
    "cutReason": "证词到手但身份暴露，新的行动压力形成",
    "segments": [{
      "segmentId": "time-01", "mode": "scene", "order": 10,
      "start": "雨夜三更，县衙后门", "end": "约一刻钟后，档案房内",
      "location": "县衙后门至档案房", "purpose": "完成身份与证词之间的交换"
    }]
  },
  "knowledgeDeltas": ["主角通过亲读证词获知押运日期"],
  "relationshipDeltas": ["主角与守门人由试探转为短暂交易"],
  "knowledgePermissions": [
    {
      "character": "主角",
      "characterId": "char-protagonist",
      "knownFactIds": ["fact-testimony-location"],
      "knownAtStart": ["证词藏在档案房"],
      "acquiredThisChapter": [
        {
          "fact": "押运日期是初七",
          "factId": "fact-escort-date",
          "acquisitionMode": "亲读证词",
          "eventId": "evt-012-03",
          "evidencePlan": "主角展开证词并逐字确认日期"
        }
      ],
      "stillUnknown": ["押运路线已被临时更改"]
    }
  ],
  "relationshipPermissions": [
    {
      "pairId": "主角|守门人",
      "participants": ["char-protagonist", "char-guard"],
      "stageAtStart": "互相试探的初识",
      "allowedFamiliarity": ["公事称呼", "条件交易", "不触碰", "不托付私密往事"],
      "plannedChange": "形成一次性互利关系",
      "catalystEventId": "evt-012-02",
      "aftermath": "双方都掌握对方的一项把柄，仍不建立旧识式默契"
    }
  ],
  "noveltyDelta": "不是再次潜入取物，而是以身份代价换取可验证证词",
  "noveltyFingerprint": {
    "goal": "取得证词", "obstacle": "守门人认出旧伤",
    "actionChain": ["试探", "交换把柄", "进入档案房"],
    "turn": "隐匿身份变成交易筹码", "outcome": "证词可得但身份部分暴露",
    "emotionalEndpoint": "短暂合作而非信任", "newInformation": ["fact-escort-date"]
  },
  "sceneBeats": [
    {
      "beatId": "beat-01",
      "mode": "scene",
      "dramaticFunction": "迫使主角在证词与隐匿身份之间选择",
      "goalOrPressure": "在巡夜换岗前进入档案房",
      "conflictOrTurn": "守门人认出主角旧伤特征",
      "requiredResult": "主角以暴露部分身份为代价进入",
      "timeSpaceAnchor": "雨夜三更，县衙后门至门内",
      "descriptionObligation": "用遮雨位置、视线与递证动作表现空间压力和交易边界",
      "participants": ["char-protagonist", "char-guard"],
      "timeSegmentId": "time-01",
      "knowledgeUses": [{"characterId": "char-protagonist", "factId": "fact-testimony-location"}],
      "relationshipRefs": ["主角|守门人"]
    }
  ],
  "evidence": [
    {
      "beatId": "beat-01",
      "paragraphStart": 4,
      "paragraphEnd": 9,
      "quote": "他把染血的袖口翻给守门人看",
      "draftSha256": "sha256:<当前草稿真实哈希>",
      "status": "pass"
    }
  ]
}
```

生成只读视图：

```bash
python scripts/render_intent.py story/runtime/chapter-0012.intent.json story/runtime/chapter-0012.intent.md
```

事务状态不写在 intent；使用 `scripts/chapter_txn.py` 管理 `chapter-NNNN.transaction.json`。正文、知情审计和冷读报告仍用 Markdown。

> 3.x Markdown intent 已移至 `references/legacy-migration.md`；正常新书与续写不加载旧模板。

## 快照 manifest

快照 manifest 不手写，也不在本文复制第二套字段模板。使用
`scripts/snapshot_book.py` 生成；当前格式、快照角色与封板条件以
`references/chapter-protocol.md`、`references/file-contract.json` 和脚本校验为准。

## rewrite manifest

> 存放在 `story/runtime/rewrites/<rewrite-id>/manifest.json`。

```json
{
  "rewriteId": "rewrite-0023",
  "sourceChapter": 23,
  "affectedChapters": [23, 24, 25],
  "candidateFiles": [
    "runtime/rewrites/rewrite-0023/chapter-0023.md"
  ],
  "createdAt": "<ISO 8601>",
  "status": "pending",
  "description": "重写第 23 章，保留后续比较"
}
```

## 章节 delta（本章改变了什么）

> 续写每章落盘前必写。这不是独立的文件——把它写进 `chapter_summaries.md`
> 对应行的 `state_changes` 列，以及 `current_state.md` 事实表的"状态"更新。

回答以下三问（写到草稿中，最终收束到 state_changes 列）：
- **事实改变**：本章有哪些事实从"未知"→"已知"、从"假"→"真"？（更新 current_state.md 事实表行）
- **伏笔推进**：哪些 hook 从 open→progressing、progressing→resolved？（更新 pending_hooks.md）
- **关系状态**：关系从 X 变 Y、资源从 A 变 B、冲突从 P 变 Q？（更新 current_state.md Relationships / Resources / Conflict）

**hook 账本双向核对**（落盘自查项）：正文有的钩子推进，账本必须记（advance / resolve + last_advanced_chapter）；账本标了 advanced 的，正文必须真的出现对应事件。禁止"正文揭露了真相、hook 仍挂 progressing"或"hook 标了 advanced、正文没这回事"。

写 `current_state.md` 时，优先写当前事实、少翻旧账。写 `chapter_summaries.md` 时，历史记录保持紧凑。
