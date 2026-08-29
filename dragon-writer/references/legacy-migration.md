# 3.x 章节 intent 迁移参考

> 仅在导入或迁移旧项目时读取。新章使用 4.1 JSON intent，不得照此手写。

## chapter-NNNN.intent.md（3.x legacy）

> 以下仅用于读取 / 迁移 3.x 项目。4.1 新章不得照此手写；同名 `.md` 应由 JSON 单向生成。

> **每章都创建**，不仅在方向改变时创建。

```markdown
# Chapter NNNN Intent（第 NNNN 章意图）

## Chapter Transaction（章节事务，必填）
- transaction_state: prepared
- min_chars: <默认取 book.json.chapterMinChars>
- target_chars: <默认取 book.json.chapterTargetChars>
- max_chars: <默认取 book.json.chapterMaxChars>
- previous_chapter_state: <第一章写 none；否则必须 closed>

> 状态只能按 `prepared → drafted → gated → audited → closed` 前进。`closed` 前不得创建下一章 intent / draft；重开修改时退回 `drafted` 并重跑全部受影响门禁。

## Work Packet Manifest（本章工作包来源，必填）
- built_from_files:
- chapter_text_range:
- relevant_state_rows:
- relevant_role_files:
- relevant_hooks:
- unresolved_drift:

> 每章从文件重新生成，不依赖聊天记忆；这是主代理写作包，禁止传给冷读子代理。

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

## Dramatic Unit（本章戏剧单元，必填）
- 核心戏剧问题：
- 开场状态：
- 章尾不可逆改变：
- 章节在此处开始 / 结束的理由：

## Time Architecture（时间架构，必填）
- 章首故事时钟：
- 章末故事时钟：
- 叙事覆盖耗时：
- 场景清单（每场标 scene / summary / ellipsis）：
- 明确跳过的无效时段：
- 跳时后的时间 / 地点 / 状态锚点：

## Knowledge Permissions（信息权限预检，必填）
| 角色 | 章首可知事实 | 本章新获知 | acquisition_mode | acquisition_event_id | 正文证据计划 | 仍不可知 |
| --- | --- | --- | --- | --- | --- | --- |

## Relationship Permissions（关系权限预检，必填）
| 关系对 | 章首阶段 / 边界 | 本章允许的称呼·接触·披露 | 计划变化 | 催化事件 | 双方后效 |
| --- | --- | --- | --- | --- | --- |

## Novelty Delta（跨章新意，必填）
- 近 5–10 章最相似的既有情节：
- 本章不可替代的新信息 / 新代价 / 新选择 / 新关系变化：
- 若使用刻意复现，本次改变其意义的方式：

## 前章末状态续接 Scene Carry-Over（必填）
> 上章末各在场角色的物理位置 / 姿态 / 着装 / 时间点，从上一章结尾与 chapter_summaries 提取。本章开场必须与之一致或有显式的时间 / 场景跳转标记；人物位置不得无交代地互换。

- 上章末时间点：
- 角色 A：位置 / 姿态 / 着装
- 角色 B：位置 / 姿态 / 着装

## 章首 / 章末 Opening / Closing（对照 chapter-craft.md 类型库）
- 开头类型与戏剧功能（可复用类型，不可复用同一功能与动作链）：
- 收尾断章类型与产生的新问题 / 后效：

## Required End-of-Chapter Change（章尾必须出现的改变）
> 写"画面上出现什么"，不写"总结出什么"（如"他攥着碎玉走出殿门，雪落满肩"，而非"他下定了决心"）。

## Required Scene Beats（必要场景节点，必填）
| beat_id | mode | dramatic_function | goal_or_pressure | conflict_or_turn | required_result | time_space_anchor | description_obligation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| beat-01 | scene | <本场为何必须存在> | <人物要什么或承受什么> | <阻力、选择或转折> | <正文必须产生的结果> | <时间 / 地点 / 初始位置> | <动作可读性、情绪外化、氛围压力、关系或信息呈现；纯转场可写“无（转场）”> |

> 只列真正必要的节点。禁止用固定感官数量或景物段配额制造模板化描写；`description_obligation` 必须说明描写承担的叙事职责。

## Draft Evidence Map（草稿证据映射，起草后必填）
| beat_id | paragraph_refs | evidence_quote | status |
| --- | --- | --- | --- |
| beat-01 | P3-P8 | <草稿中可精确命中的短引> | pass |

> 每个 Required Scene Beat 必须恰好有一行；短引须在草稿正文命中，段落引用不能为空。字数达标但节点没有证据仍为 fail。

## Evidence Read（读过的证据）

## 实际偏离 Deviation Log
> 落盘时若实际产出与上面 intent 的 goal / 必须场景 / Required End-of-Chapter Change 不一致，在此追加一行（偏离项 + 原因 + 去向章）；无偏离写"无"。**只追加，不改写 intent 原有内容**（intent 是写前契约）。
```
