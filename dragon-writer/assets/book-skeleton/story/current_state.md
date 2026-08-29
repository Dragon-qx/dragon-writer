# Current State

## 进度 Progress
- Current chapter: 2

## 地点与时间 Location And Time

青云门，外门，早春。当前故事时钟：入门第八日·申时。

## 事件时间轴 Event Timeline

| event_id | chapter | sequence | start_time | end_time | elapsed | location | participants | preconditions | event | outcome | presentation |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| time-001 | 1 | 1 | 入门第 1 日·申时 | 入门第 1 日·酉初 | 约一时辰 | 甲字七号舍 | 陆恒、林逸 | 陆恒刚入住 | 两人初次交谈，约定次日寅时合练 | 建立一次性练剑约定，尚未深交 | scene |
| time-002 | 2 | 1 | 入门第 2 日·寅时 | 入门第 8 日·卯时 | 七日内数次 | 后山练剑坪 | 陆恒、林逸 | time-001 的合练约定 | 两人连续数日合练，交流限于招式与外门公开消息 | 形成固定练剑搭档，但未共享私事 | summary |
| time-003 | 2 | 2 | 入门第 8 日·未末 | 入门第 8 日·申时 | 约半时辰 | 藏经阁三层 | 陆恒、苏霜 | 陆恒寻找剑诀 | 两人初次交谈，苏霜把玉坠暂留经橱 | 陆恒接受一次临时照看，没有建立私人信任 | scene |

## 主角 Protagonist
- status: 炼气三层，入门第八日
- goal: 在外门大比中脱颖而出
- constraints: 资源有限，仅有 300 下品灵石

## 人物关系 Relationships

| 角色 | 与主角关系 | 状态 |
| --- | --- | --- |
| 林逸 | 邻舍、固定练剑搭档 | 相识七日，能谈公开修炼话题，尚未交心 |
| 苏霜 | 内门弟子、一次事务性接触 | 第 2 章藏经阁初见，只互报姓名与身份 |

## 关系许可账本 Relationship Permission Ledger

| pair_id | A | B | first_met_chapter | prior_history | current_stage | trust_basis | allowed_familiarity | private_knowledge_shared | address_touch_boundary | last_change_chapter | catalyst_event_id | evidence | asymmetry |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| rel-001 | 陆恒 | 林逸 | 1 | 无 | 相识七日的练剑搭档 | 林逸以食物示好；七日数次守约合练 | 可直呼姓名、交换公开修炼消息、相约合练；不可替对方做主、默认托命或谈创伤秘密 | 无 | 无亲昵称呼；无主动身体接触 | 2 | time-002 | 他们说得最多的是招式与大比 | 林逸主动热络，陆恒仍保留戒心 |
| rel-002 | 陆恒 | 苏霜 | 2 | 无 | 初识、一次临时托物 | 仅互报姓名与身份；苏霜进行低风险试探 | 使用正式称呼、讨论眼前事务；不可私人调侃、身体接触、代替决策或读懂隐秘心思 | 无 | 保持礼貌距离 | 2 | time-003 | 苏霜，内门 | 苏霜掌握互动节奏，陆恒不确定她的意图 |

## 已知事实 Known Truths（章节感知事实）

> 以本表为"某角色在第 N 章时知道什么、不知道什么"的硬边界。
> `evidence` 证明事实本身；`acquisition_evidence` 证明该 knower 如何在 known_from_chapter 获知。validate_book 会分别核验。

| fact_id | statement | subject | truth_status | introduced_chapter | invalidated_chapter | source_chapter | knower | known_from_chapter | confidence | evidence | acquisition_mode | acquisition_event_id | acquisition_evidence | notes |
| --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| fact-001 | 陆恒入门首日入住外门甲字七号舍 | 陆恒 | 当前为真 | 1 | — | 1 | 陆恒 | 1 | 确证 | 陆恒站在甲字七号舍前 | 亲历 | time-001 | 陆恒站在甲字七号舍前 | 第1章正文 |
| fact-002 | 林逸是甲字八号的外门弟子 | 林逸 | 当前为真 | 1 | — | 1 | 陆恒 | 1 | 确证 | 在下林逸，住甲字八号 | 被告知 | time-001 | 在下林逸，住甲字八号 | 第1章正文 |
| fact-003 | 苏霜是内门弟子 | 苏霜 | 当前为真 | 2 | — | 2 | 陆恒 | 2 | 确证 | 苏霜，内门 | 被告知 | time-003 | 苏霜，内门 | 第2章正文 |
| fact-004 | 陆恒是外门弟子 | 陆恒 | 当前为真 | 2 | — | 2 | 苏霜 | 2 | 确证 | 在下陆恒，外门弟子 | 被告知 | time-003 | 在下陆恒，外门弟子 | 第2章正文 |

## 资源 / 伤势 / 库存 Resources / Injuries / Inventory

- 下品灵石：300 枚
- 回春丹：3 枚

## 道具账本 Prop Ledger

> 审计维 39 的判定基础。origin（来历）为道具获得过程的权威记录；origin 变化 = canon 变更，须同步失效旧事实。

| prop_id | 名称 | 类别 | 数量 | 容量单位 | 归属角色 | 存放位置 | 状态 | acquired_chapter | disposed_chapter | previous_owner | origin | event_id | 最近变化章 | 最近变化事件 | 备注 |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | --- |
| prop-001 | 回春丹 | 丹药 | 3 | 枚 | 主角 | 储物袋乙格 | active | 1 | — | — | 入门发放 | evt-001 | 1 | 入门发放 | 疗伤用 |
| prop-002 | 入门令牌 | 信物 | 1 | 枚 | 主角 | 怀中 | active | 0 | — | 老猎户 | 临行前由村中老猎户所赠 | evt-000 | 1 | 入门时出示 | 木质，边缘磨亮 |
| prop-003 | 下品灵石 | 货币 | 300 | 枚 | 主角 | 储物袋甲格 | active | 1 | — | — | 入门发放 | evt-001 | 1 | 入门发放 | — |

## 空间锚点 Spatial Anchors

> 审计维 38 的判定基础。正文被交互的固定物件必须能在锚点中找到（登记完备性）。

| scene_id | canonical_name | aliases | coordinate_reference | 方位 / 格局 | 出入口 | 关键物件位置 | valid_from_chapter | valid_until_chapter | last_change_event | 建立章 | 最近更新章 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| scene-001 | 青云门外门弟子舍（甲字七号） | 甲字七号 | — | 坐北朝南，一明一暗；明间起居、暗间卧榻 | 南向双扇门 | 东墙木案、西墙兵器架、暗间单人床 | 1 | — | — | 1 | — | — |
| scene-002 | 藏经阁三层 | — | — | 八角形中厅，八面经橱按八卦方位排列 | 仅西南角木梯 | 中厅八角石台（阵眼）、离位经橱 | 2 | — | — | 2 | — | — |

## 当前冲突 Current Conflict

外门大比即将开始，陆恒需要快速提升实力。
