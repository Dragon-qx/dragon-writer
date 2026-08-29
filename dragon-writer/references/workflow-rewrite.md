# 模式 E：改写 / 修复

## 触发时机

重写某一章。

## 安全规则（禁止隐式丢失）

1. **首先生成受影响文件和章节清单**。
2. **用户确认前将候选稿写入 `story/runtime/rewrites/<rewrite-id>/`**，不删除正文、不修改权威状态。
3. **明确"分支"是 Git 分支还是文件级候选稿**：本契约中"分支"仅指 Git 分支，文件级候选稿统一称 `runtime rewrite candidate`。
4. **采纳改写前创建恢复点**（快照）；后续产物只归档，不直接删除。
5. **执行后报告影响范围**、归档位置与 recovery snapshot。
6. **单写手串行**：候选稿、正文修改、后续章适配和 Runtime 更新全部由主代理完成；禁止子代理并行改不同章节或生成替代版本。子代理只可在候选稿冻结后做无背景冷读。

## 步骤

1. **识别回滚点**：用户指定重写到第 N 章。
2. **先计划再回滚**：运行 `rollback_book.py <book-dir> --chapter <N-1>` 查看恢复文件和后续产物；用户确认采纳重写后加 `--execute`。执行时自动创建 recovery snapshot，并把后续正式稿和 Runtime 移入 `story/rollback-archive/`，不直接删除。
3. **未确认时只做候选稿**：把新稿存到 `runtime/rewrites/<rewrite-id>/` 供对比，不修改权威正文或状态。
4. **对齐**：若 N 是最新且没有后续章节 / 事务，可直接运行 `chapter_txn.py ... reopen`；旧门禁、审计和原 closed 快照会可恢复地标为 superseded。若步骤 2 已回滚到 N-1，则第 N 章事务已在 rollback archive 中，不再运行 reopen，而是重新 `prepare`。小改动也必须重锁草稿哈希并重跑受影响门禁；大改动重新生成 `chapter-NNNN.intent.json`。涉及多章时按章号串行处理，一章重新 `closed` 后才进入下一章。
5. **过三道质量门禁**：重写稿必须走 SKILL.md 的机械门禁、主代理知情连续性审计和纯正文冷读，重点复核硬字数、场景证据、信息获知链、关系许可、故事时钟与跨章语义重复。冷读子代理只拿候选正文，不拿原稿差异说明、修改意图或项目状态。
6. **留痕**：把回滚点、删除范围、重写差异写入 `story/audit-drift.md` 的"已修复"节。

## 相关文档

- 重写流程安全规则：`references/file-contract.md`
- 快照契约：`references/file-contract.md`
- 章首 / 章末技法（起草前必读）：`references/chapter-craft.md`
- 知情审计与无背景冷读：`references/audit-dimensions.md`
- rewrite manifest 模板：`references/templates.md`
