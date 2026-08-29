# Chapter 0001 Intent（第 1 章意图）

## Chapter Transaction（章节事务，必填）
- transaction_state: closed
- min_chars: 1000
- target_chars: 1500
- max_chars: 2500
- previous_chapter_state: none

## Work Packet Manifest（本章工作包来源，必填）
- built_from_files: author_intent.md; current_focus.md; current_state.md; volume_map.md; 陆恒.md; 林逸.md
- chapter_text_range: 无（全书第一章）
- relevant_state_rows: 第 0 章基线、甲字七号舍空间锚点
- relevant_role_files: 陆恒.md; 林逸.md
- relevant_hooks: hook-001
- unresolved_drift: 无

## Goal（目标）

主角陆恒入门青云门，建立外门生活基线，结识室友林逸，确立"外门大比"目标。

## Outline Node（大纲节点）

第一卷·入门 → 第 1 章：入门

## Current Task（当前任务）

~1500 字章节（对照 book.json.chapterWordCount）。结构：入山门 → 入住甲字七号舍 → 结识林逸 → 确立大比目标。

## Reader Is Waiting For（读者在等啥）

- 主角是什么人、为什么来青云门
- 外门的生存环境

## Hooks（钩子）

- advance（要推进的）：hook-001（入门承诺）
- resolve（要收掉的）：无
- defer（要继续捂着的）：主角体内封印的剑灵

## Must Keep（必须保住）

- 第三人称限制视角，聚焦陆恒
- 主角不杀无辜的设定底
- 五感描写

## Must Avoid（必须避开）

- 不要让主角获得无代价的力量提升
- 不要一次性倒完剑灵背景
- 不要以总结 / 金句 / 宣布计划收尾

## Style Emphasis（风格强调）

- 语言：古白夹杂，对话偏白话
- 节奏：入山（舒缓）→ 陌生人试探（日常张力）→ 接受一次有限合作

## Dramatic Unit（本章戏剧单元，必填）

- 核心戏剧问题：陆恒是否接受陌生邻舍林逸的示好与合练邀请？
- 开场状态：陆恒刚获得住处，仍把自己视为孤身一人。
- 章尾不可逆改变：他接受了一次有明确时间的合练约定，但没有越级成为挚友。
- 章节在此处开始 / 结束的理由：从第一次进入住处开始，在约定尚未执行时切断。

## Time Architecture（时间架构，必填）

- 章首故事时钟：入门第 1 日·申时
- 章末故事时钟：入门第 1 日·酉初
- 叙事覆盖耗时：约一时辰，不覆盖完整一天
- 场景清单：进入住处（scene）→ 与林逸试探性交谈（scene）→ 大比规则与合练约定（scene）
- 明确跳过的无效时段：此前三日赶路只用一句背景交代；晚饭后的洗漱睡眠不写
- 跳时后的时间 / 地点 / 状态锚点：无章内跳时

## Knowledge Permissions（信息权限预检，必填）

| 角色 | 章首可知事实 | 本章新获知 | acquisition_mode | acquisition_event_id | 正文证据计划 | 仍不可知 |
| --- | --- | --- | --- | --- | --- | --- |
| 陆恒 | 自己的来历、入门身份 | 林逸住甲字八号；外门大比公开规则 | 被告知 | time-001 | 林逸自报住处并解释大比 | 林逸的家族旧事与真实动机 |
| 林逸 | 隔壁新来了一名弟子 | 陆恒姓名、住甲字七号 | 被告知 / 观察 | time-001 | 陆恒自报姓名；人在舍内 | 陆恒的家乡创伤与剑灵秘密 |

## Relationship Permissions（关系权限预检，必填）

| 关系对 | 章首阶段 / 边界 | 本章允许的称呼·接触·披露 | 计划变化 | 催化事件 | 双方后效 |
| --- | --- | --- | --- | --- | --- |
| 陆恒×林逸 | 陌生人 | 直呼姓名、分享食物与公开消息；无亲昵称呼、身体接触或秘密披露 | 陌生人→一次合练约定 | 林逸示好，陆恒有限接受 | 林逸继续外向；陆恒先观察其是否守约 |

## Novelty Delta（跨章新意，必填）

- 近 5–10 章最相似的既有情节：无（全书第一章）
- 本章不可替代的新信息 / 新代价 / 新选择 / 新关系变化：建立外门生活基线、大比规则和第一项有限合作。
- 若使用刻意复现，本次改变其意义的方式：无。

## 前章末状态续接 Scene Carry-Over（必填）

- 上章末时间点：无（第 1 章，全书开场）
- 角色 A（陆恒）：无前史状态，首次出场

## 章首 / 章末 Opening / Closing（对照 chapter-craft.md 类型库）

- 开头类型：动作切入（陆恒站在甲字七号舍前）
- 收尾断章类型与后效：决定未执行（陆恒接受明日寅时合练，但要先看林逸是否守约）

## Required End-of-Chapter Change（章尾必须出现的改变）

画面上：林逸站在门槛外提醒“寅时别赖床”，陆恒决定先观察他是否守约。

## Required Scene Beats（必要场景节点，必填）
| beat_id | mode | dramatic_function | goal_or_pressure | conflict_or_turn | required_result | time_space_anchor | description_obligation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| beat-01 | scene | 建立外门生活基线 | 陆恒需要确认新住处是否安全 | 从陌生山门进入私人空间 | 陆恒安顿在甲字七号舍 | 入门第 1 日申时 / 甲字七号舍 | 用物件与身体感觉呈现贫寒但可落脚的空间 |
| beat-02 | scene | 建立有限合作而非突兀友情 | 林逸示好，陆恒保持戒备 | 食物与大比消息促成试探 | 双方约定仅试一次寅时合练 | 酉初 / 屋内至门槛 | 以停顿、距离和有限回应表现关系边界 |

## Draft Evidence Map（草稿证据映射，起草后必填）
| beat_id | paragraph_refs | evidence_quote | status |
| --- | --- | --- | --- |
| beat-01 | P1-P8 | 床板硬得硌人，他却觉得踏实 | pass |
| beat-02 | P9-P35 | 那不是交心，也还算不上朋友 | pass |

## Evidence Read（读过的证据）

- author_intent.md
- current_focus.md
- current_state.md（第 0 章基线）
- 陆恒.md / 林逸.md
- chapter-craft.md

## 实际偏离 Deviation Log

- 无（落盘后与意图一致）
