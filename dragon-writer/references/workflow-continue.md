# 模式 B：续写已有书

## 不变量

- 规划、正文、修订、状态更新都由主代理逐章串行完成。禁止子代理写正文、补片段、改段落、提前写后章或维护 Runtime。
- 子代理只在当前草稿冻结、机械门禁与主代理知情审计均通过后做一次无背景冷读；使用空上下文，不附一审报告，不修改文件。
- 状态机为 `prepared → drafted → gated → audited → closed`。只有 `closed` 后才能准备下一章；修改已封板章必须显式 `reopen`。
- 上下文过长时停止生成，从磁盘重建当前章工作包；不得并行分章，也不得用聊天记忆替代文件证据。

## 逐章事务

### 1. 前置锁与准备

先确定唯一书籍与下一章号，再运行：

```bash
python scripts/check_chapter_draft.py <book-dir> --chapter <NNNN> --preflight
python scripts/chapter_txn.py <book-dir> --chapter <NNNN> prepare
```

`prepare` 会重验上一章完整封板及其外部哈希，并确认当前章恰好是最后一章之后的下一章。旧项目先运行 `python scripts/migrate_3_13_to_4_0.py <book-dir>` 查看计划，再由用户确认后加 `--execute`；只有 import manifest 精确绑定的正式稿会成为 `imported_closed`。

### 2. 建立结构化意图

创建 `story/runtime/chapter-NNNN.intent.json`，使用 `schemaVersion: 4.1`。时间必须拆为有序 segments；场景节点必须引用参与角色、时间段、使用的 fact ID 和关系 pair ID；跨章新意填写结构化 `noveltyFingerprint`。起草后补 Evidence Map。

不要手写同名 Markdown。生成只读视图：

```bash
python scripts/render_intent.py <book-dir>/story/runtime/chapter-NNNN.intent.json <book-dir>/story/runtime/chapter-NNNN.intent.md
```

`book.json.chapterMinChars` 是书级硬下限，intent 只能提高规划目标，不能降低下限。场景节点只列真正必要的戏剧工作；`descriptionObligation` 写清描写承担的行动可读性、情绪外化、氛围压力、关系变化或信息呈现职责，不设固定感官数量。

### 3. 重建有边界的主代理工作包

intent 写入磁盘后运行 `python scripts/build_work_packet.py <book-dir> --chapter <NNNN>`。脚本从 intent、书级契约、最近正式章、摘要、焦点、钩子、相关状态和角色卡重建带源哈希的有限工作包。

工作包只供主代理使用。对话已堆积多章全文、多个报告，或主代理不能逐项复述当前章硬约束时，立即从这些文件重新取数后再继续。intent 或任一来源改变后必须重建，不沿用旧包。

### 4. 主代理独立起草并冻结

只写 `story/runtime/chapter-NNNN.draft.md`。按戏剧变化选择场景，不按早晨到夜晚覆盖一天；无有效变化的时段用 summary / ellipsis，跳时后重新锚定时间、地点、人物位置和状态。每个角色的言行分别核对获知路径与关系许可；同场、亲近、作者知道或读者知道均不自动授权。

草稿完成后运行：

```bash
python scripts/chapter_txn.py <book-dir> --chapter <NNNN> mark-drafted
```

该动作锁定草稿哈希。之后任何正文修改都会使既有证据和门禁失效；先运行 `chapter_txn.py ... reopen`，它会把旧门禁 / 审计 manifest 可恢复地改名为 `superseded-*`，再重新走 `mark-drafted`、证据和门禁。

### 5. 填写证据并过机械门禁

按空行确定性编号 `P1..Pn`。每个 `sceneBeats[].beatId` 必须恰好有一个 `evidence[]`，包含当前草稿 SHA-256、合法段落起止、该范围内精确命中的短引和 `status: pass`。证据不能跨段冒领，多个节点不得无理由复用同一短引。

更新 JSON 后重新生成 Markdown 视图，再运行：

```bash
python scripts/chapter_txn.py <book-dir> --chapter <NNNN> gate
```

脚本检查 schema、事务链、书级字符下限、时间/事实/关系引用、节点证据，并自动生成与绑定近 10 章重复报告。任一失败不得进入审计。

### 6. 主代理知情审计

主代理使用完整项目文件检查：故事时钟与章节切分、空间移动、信息获知链、关系权限、道具/伤势/服装/数字、钩子与 canon、章际承接、近 5–10 章情节和文本重复。报告写入书目录内的 Markdown，例如 `story/runtime/chapter-NNNN.informed-audit.md`。

发现正文问题后必须修改草稿，并从 `mark-drafted`、Evidence Map 与 `gate` 重新开始。通过后登记：

```bash
python scripts/chapter_txn.py <book-dir> --chapter <NNNN> record-audit --kind informed --report story/runtime/chapter-NNNN.informed-audit.md --status pass
```

### 7. 全新子代理纯正文冷读

冷读稿源必须显式指定，禁止“优先草稿”式猜测：

```bash
# 单章：只读当前冻结草稿
python scripts/build_cold_read_packet.py <book-dir> --draft <NNNN> --manifest story/runtime/chapter-NNNN.cold-source.json

# 章际：上一章必须是正式稿，当前章必须是冻结草稿
python scripts/build_cold_read_packet.py <book-dir> --final <上一章> --draft <NNNN> --manifest story/runtime/chapter-NNNN.cold-source.json
```

只把脚本标准输出交给一个空上下文审计子代理。包内不得出现题材、大纲、意图、人物卡、时间线、状态、信息链、关系账本、钩子、字数、疑点、预期修法、旧报告或主代理解释。提示只要求严重度、正文位置与短引、读者影响、修复方向；证据不足写 `unknown`。子代理只报告，不续写、不改写、不更新文件。

冷读报告写回书目录后登记：

```bash
python scripts/chapter_txn.py <book-dir> --chapter <NNNN> record-audit --kind cold --report story/runtime/chapter-NNNN.cold-audit.md --packet-manifest story/runtime/chapter-NNNN.cold-source.json --status pass
```

两类审计都为 pass 后事务才进入 `audited`。冷读发现需要改正文时，由主代理修改并重新执行步骤 4–7；二审用另一个空上下文审计员，只给修改后的纯正文，不附一审报告。

### 8. 落盘、验证与封板

1. 创建写入前恢复点：`python scripts/snapshot_book.py <book-dir> --chapter <NNNN> --type prewrite`。
2. 将已审计草稿按字节复制到唯一的 `chapters/NNNN_标题.md`。
3. 更新摘要、故事时钟、事实获知链、关系许可、道具、钩子、焦点和 `book.json.updatedAt`；不得把下一章计划提前写成已发生事实。
4. 运行 `python scripts/rebuild_index.py <book-dir>`，不得手填计数。
5. 运行 `python scripts/validate_book.py <book-dir>`；重复报告已经在 gate 中自动生成并绑定。
6. 创建章末快照：`python scripts/snapshot_book.py <book-dir> --chapter <NNNN> --type closed`。
7. 运行 `python scripts/chapter_txn.py <book-dir> --chapter <NNNN> close`。

`close` 会重验草稿、正式稿、门禁报告、两份审计报告及其哈希，并执行全书验证；任一文件在登记后改变都拒绝封板。连续写作中途不询问合并审核，只在本轮最后一章 `closed` 后询问一次。

## 验收

- 实际去空白字符数达到书级硬下限，所有必要描写职责均有当前草稿证据；没有占位字段。
- 角色知识与关系行为都有独立、可定位的获得/变化依据；没有作者信息泄漏或初识即旧识。
- 章节边界服务戏剧单位，不是日程切片；近章不存在同构事件换措辞重演。
- 冷读稿源 manifest 明确区分 final / draft，包内没有隐藏上下文。
- 事务为 `closed` 且哈希链、全书验证与章末快照均有效。
