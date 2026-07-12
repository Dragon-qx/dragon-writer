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
