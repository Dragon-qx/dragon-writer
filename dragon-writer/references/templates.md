# Dragon Writer 模板

创建新书或回填缺失文件时使用这些模板。用户提供的事实要原样保留，不魔改。

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
  "createdAt": "<ISO timestamp>",
  "updatedAt": "<ISO timestamp>"
}
```

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

```markdown
# <Name>

## 角色功能 Story Function

## 欲望·恐惧·创伤 Desire / Fear / Wound

## 当前状态 Current State

## 人物关系 Relationships

## 秘密与信息边界 Secrets And Information Boundary

## 言行指纹 Speech And Behavior Fingerprint

## 成长弧线 Arc
```

## book_rules.md

```markdown
# Book Rules

## POV 与叙事距离 POV And Narrative Distance

## 题材规则 Genre Rules

## 硬定局锁 Hard Canon Locks

## 力量 / 资源 / 时间限制 Power / Resource / Time Limits

## 禁手 Forbidden Moves

## 风格约束 Style Constraints
```

## pending_hooks.md

> 13 列账本。`status` 列直接供审计维 6（伏笔检查）按字面标记升级，
> 停滞 / 受阻标记是 Auditor 写报告的直接证据——请保留字面 token。

```markdown
# Pending Hooks

| hook_id | start_chapter | type | status | last_advanced_chapter | expected_payoff | payoff_timing | depends_on | core_hook | promoted | pays_off_in_arc | half_life | notes |
| --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- | ---: | --- |
| hook-001 | 0 | premise | open | 0 |  |  |  | yes | yes | 主线·第一卷 | 10 | Initial book promise. |
```

列含义：
- **status**：`open` / `progressing` / `deferred` / `resolved` + 诊断标记。停滞用 `stale (距=N)`、受阻用 `blocked on hook-X (阻=N)`（N 由 LLM 根据最近一次推进章节之差推算，字面值供 Auditor 引用）。
- **promoted**（true/false）：是否从架构师种子升级为主线承重伏笔。仅 promoted=true 的 stale/blocked 才允许升到 critical。
- **pays_off_in_arc**：计划在哪个弧线/卷回收（供审计维 6 判断结构）。
- **depends_on**：上游 hook_id。受阻诊断依据；若上游未解决则本 hook 应为 `blocked`。
- **half_life**（半衰期）：超过 N 章未推进时触发 info 级提醒。

**钩子治理规则**（续写时遵守）：
- 准入/合并：新钩子若与既有 hook"同主题 + 同回收对象"→ 合并到既有 hook，不新增行。
- 收敛：章末应将"已兑现/已推翻"的 hook 显式标 `resolved`，禁止让完成态的 hook 长期挂 `open`。

## current_state.md

```markdown
# Current State

## 进度 Progress
- Current chapter: 0

## 地点与时间 Location And Time

## 主角 Protagonist
- status:
- goal:
- constraints:

## 人物关系 Relationships

## 已知事实 Known Truths（章节感知事实）

> 以本表为"某角色在第 N 章时知道什么、不知道什么"的硬边界。
> 续写时：角色不可引用 **起始章 > 当前章** 的事实；角色忘记已习得的事实需做显式说明。

| 事实 | 人物 | 起始章 | 来源章 | 状态 |
| --- | --- | ---: | ---: | --- |
| 主角出身 | 主角 | 1 | 1（序章交代） | 当前为真 |

## 资源 / 伤势 / 库存 Resources / Injuries / Inventory

> 粗粒度资源 / 伤势 / 总状态，细粒度道具清单见下方「道具账本」。

## 道具账本 Prop Ledger（跨章道具追踪硬账本）

> 审计维 39（道具追踪）的判定基础。随身物件、弹药、消耗品、贵重品逐件登记——数量与存在的变化必须由显式事件驱动（获得/失去/消耗/赠予/被夺/典当/碎裂），**不可无痕 ±1**。
> 每章落盘时：把本章内所有"获得 / 消耗 / 丢失 / 赠予"事件对应到账本行；清零或新增行须注明事件。

| prop_id | 名称 | 类别 | 数量 | 容量单位 | 归属角色 | 存放位置 | 状态 | 最近变化章 | 最近变化事件 | 备注 |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| prop-001 | 回春丹 | 丹药 | 3 | 枚 | 主角 | 储物袋乙格 | 完好 | 12 | 购买（散修集市） | 疗伤用，每枚止血清创 |
| prop-002 | 青锋剑 | 法器 | 1 | 柄 | 主角 | 背上剑鞘 | 完好 | 3 | 获赠（师尊） | 下品法器 |
| prop-003 | 下品灵石 | 货币 | 300 | 枚 | 主角 | 储物袋甲格 | — | 14 | 购买功法消耗 50 | — |

**列含义**：prop_id（项目唯一 ID）、名称（**全文统一名**，维 39 名字一致性的硬性锚点）、类别（丹药 / 法器 / 符箓 / 货币 / 信物 / 衣物 / 杂物…）、数量（整数）、容量单位（枚 / 株 / 锭 / 斛…）、归属角色、存放位置（储物袋甲格 / 袖中 / 背上剑鞘 / 洞府石床…）、状态（完好 / 封印 / 半充 / 损毁 / 耗尽…）、最近变化章、最近变化事件（谁在哪一章做了什么导致本行变化）、备注。

**治理规则**：
- 新道具入章 → 准入：本行新增，最近变化章 = 本章，事件 = 来源。
- 道具状态/数量变化 → 修改本行，不可另起同名行（防"名字漂移"）。
- 道具消失（碎裂 / 被夺 / 赠出 / 典当 / 耗尽） → 数量归 0 或删行，事件必填。
- 消耗品（丹药 / 符箓 / 灵石）每用一次减一次——禁止"昨天吃两枚今天还有三枚"。

## 空间锚点 Spatial Anchors（场景内固定布局）

> 审计维 38（空间一致性）的判定基础。每个反复出现的场景在本表登记一次固定布局，后续同场景跨章描写均以此为准；**物件位置变化必须有显式事件**（拆建、战损、重新布置）。
> 新场景首次出现时建立锚点；首次返回时对账。

| anchor_id | 场景名词 | 方位 / 格局 | 出入口 | 关键物件位置 | 建立章 | 最近更新章 | 备注 |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| sa-001 | 青云门外门弟子舍（甲字七号） | 坐北朝南，一明一暗；明间起居、暗间卧榻 | 南向双扇门，门外青石甬道 | 东墙木案（灯盏居北）、西墙兵器架、北墙通暗间小门 | 3 | — | — |
| sa-002 | 藏经阁三层 | 八角形中厅，八面经橱按八卦方位排列 | 仅西南角木梯通往二层 | 中厅八角石台（镇阁阵眼）、离位禁制封印铜简若干 | 7 | 21（战损：震位经橱倒塌） | — |

**列含义**：anchor_id、场景名词（**文内统一名**，不可同地异名）、方位 / 格局（朝向 + 几进 / 几间 / 形状）、出入口（方位 + 形式）、关键物件位置（方位词 + 物件 + 相对坐标）、建立章、最近更新章（拆建 / 战损 / 布置变化时填）、备注。

**空间一致性治理规则**：
- **首次出场**：描写完成时即建锚点；本场景相邻段落方位不能互斥。
- **跨章复访**：对照锚点 —— 固定物件方位不能变化；变化必须有一行"最近更新"。
- **移动合法化**：角色从 A 位置到 B 位置，描写中必须经过中间空间路径，不可瞬移（门廊 → 庭院 → 正厅）。
- **视角合法化**：限制视角下角色看不见其位置不可能看见的内容（隔墙背面 / 遮挡物后）。
- **视角变换 / 缩景**：大远景可改变绝对方位参考，但须在描写中明示（"从山脊回望"）。

## 当前冲突 Current Conflict
```

列含义：**事实**（一句可验证的陈述）；**人物**（认知主体）；**起始章**（该角色首次获知此事实的章节，= validFrom）；**来源章**（信息最初出现的章节）；**状态**（当前为真 / 已推翻-参见第 N 章 / 仅主角知情 / 多角色共有）。该表是审计维 9（信息越界）与维 29（未来信息泄露）的判定基础。

## chapter_summaries.md

```markdown
# Chapter Summaries

| chapter | title | characters | events | state_changes | hook_activity | mood | chapter_type |
| ---: | --- | --- | --- | --- | --- | --- | --- |
```

## chapters/index.json

```json
[]
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

## 章节 delta（本章改变了什么）

> 续写每章落盘前必写。这不是独立的文件——把它写进 `chapter_summaries.md`
> 对应行的 `state_changes` 列，以及 `current_state.md` 事实表的"状态"更新。

回答以下三问（写到草稿中，最终收束到 state_changes 列）：
- **事实改变**：本章有哪些事实从"未知"→"已知"、从"假"→"真"？（更新 current_state.md 事实表行）
- **伏笔推进**：哪些 hook 从 open→progressing、progressing→resolved？（更新 pending_hooks.md）
- **关系状态**：关系从 X 变 Y、资源从 A 变 B、冲突从 P 变 Q？（更新 current_state.md Relationships / Resources / Conflict）
