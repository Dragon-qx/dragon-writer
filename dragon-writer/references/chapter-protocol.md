# 章节提交协议 4.1

本文件只定义高风险不变量。字段形状以 `schemas/` 为准，跨文件语义以 `scripts/check_chapter_draft.py`、`chapter_txn.py` 和 `validate_book.py` 的实际校验为准；其他文档不得复制另一套字段定义。

## 权威与派生

- 权威：`book.json`、状态账本、`intent.json`、`transaction.json`、唯一正式正文。
- 机械证据：gate、overlap、audit、cold-source 与 snapshot manifest；都必须绑定输入哈希。
- 派生：intent Markdown、工作包、dashboard。派生文件不能反向成为事实源。

## 状态机

`prepared → drafted → gated → audited → closed`。每个命令先验证章号、事件链、当前状态和既有外部绑定，最后才替换事务文件。失败不得推进状态。

- `prepare`：只允许最大既有章的下一章；重验上一章完整封板。
- `mark-drafted`：锁定唯一主代理草稿。
- `gate`：绑定 intent、书级字数契约、草稿、机械报告和近章重复报告。
- `record-audit`：知情报告绑定当前 gate；冷读报告还必须绑定显式稿源 manifest。
- `close`：正式稿必须与已审计草稿字节一致，并绑定状态账本、索引和 closed 快照。
- `reopen`：存在后续章节或事务时拒绝；先使用回滚计划级联归档。

事件哈希用于发现不一致，不是身份签名。不得把可重新计算的 SHA-256 描述为真实性或权限证明。

## 4.1 叙事引用

- 时间：有序 `segments` 区分 scene、summary、ellipsis、transition；压缩与跳时必须说明理由。
- 信息：角色使用 `factId` 前必须在该角色的开场持有或本章获知集合中；作者、读者或 POV 知情不自动授权角色知情。
- 关系：多人互动节点引用 `pairId`，许可明确双方、开场阶段、允许行为、计划变化和催化事件。
- 重复：`noveltyFingerprint` 记录目标、阻碍、行动链、转折、结果、情绪落点和新增信息；机械近似与知情语义审计任一 blocking 都不得封板。
- Evidence：短引必须含实际文字、命中绑定草稿的限定段落；`—`、空白和纯标点不是证据。

## 上下文与代理

正文、修订和 Runtime 始终由主代理逐章串行完成。上下文过长时停止生成，用 `build_work_packet.py` 从磁盘重建当前章包。子代理只在 gate 和知情审计通过后获得纯正文冷读包；一个包、一个全新审计员、只报告不修改。

## 快照、回滚和导入

- `prewrite-NNNN` 是写入前恢复点；`NNNN` 是封板使用的 closed 快照；recovery 快照必须有完整 manifest。
- 回滚默认只输出计划。执行时先建 recovery，再把后续正式稿和 Runtime 移入 `story/rollback-archive/`，恢复后运行全书验证。
- 历史 `closed` 文本不构成信任。只有与索引、唯一正式稿、import manifest 路径和哈希一致的连续历史章可标记为 `imported_closed`。

