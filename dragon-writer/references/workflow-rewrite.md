# 模式 E：改写 / 修复

## 触发时机

重写某一章。

## 安全规则（禁止隐式删除）

1. **首先生成受影响文件和章节清单**。
2. **用户确认前将候选稿写入 `story/runtime/rewrites/<rewrite-id>/`**，不删除正文、不修改权威状态。
3. **明确"分支"是 Git 分支还是文件级候选稿**：本契约中"分支"仅指 Git 分支，文件级候选稿统一称 `runtime rewrite candidate`。
4. **真正删除前创建恢复点**（快照）。
5. **删除后报告范围**、是否可恢复及恢复位置。
6. **单写手串行**：候选稿、正文修改、后续章适配和 Runtime 更新全部由主代理完成；禁止子代理并行改不同章节或生成替代版本。子代理只可在候选稿冻结后做无背景冷读。

## 步骤

1. **识别回滚点**：用户指定重写到第 N 章。
2. **三步回滚机械**（仅在用户 N 之后没有章节，或用户**明确同意删后续**时启用真实删除）：
   - **恢复快照**：把 `story/snapshots/<NNNN-1>/` 的状态文件恢复到工作区。
   - **清后续产物**：删除第 N 章之后的**所有**运行时产物——`chapters/NNNN_*.md`（N 之后）、`chapters/index.json` 中 N 之后的条目、`chapter_summaries.md` 中 N 之后的行、`current_state.md` / `pending_hooks.md` 中 N 章之后的改动。
   - **重建快照**：从 N-1 章状态重新起草第 N 章，完成后新建快照 `snapshots/<NNNN>/`。
3. **绝不擅自删章**：只在 N 之后无章节、或用户明确同意时才启用真实删除。否则走"候选稿"路径——把新稿存到 `runtime/rewrites/<rewrite-id>/` 让用户对比取舍。
4. **对齐**：已封板章在采纳候选稿前运行 `python scripts/chapter_txn.py <book-dir> --chapter <N> reopen`；旧门禁 / 审计 manifest 会可恢复地标为 superseded。小改动也必须重锁草稿哈希并重跑受影响门禁；大改动重新生成 `chapter-NNNN.intent.json`。涉及多章时按章号串行处理，一章重新 `closed` 后才进入下一章。
5. **过三道质量门禁**：重写稿必须走 SKILL.md 的机械门禁、主代理知情连续性审计和纯正文冷读，重点复核硬字数、场景证据、信息获知链、关系许可、故事时钟与跨章语义重复。冷读子代理只拿候选正文，不拿原稿差异说明、修改意图或项目状态。
6. **留痕**：把回滚点、删除范围、重写差异写入 `story/audit-drift.md` 的"已修复"节。

## 相关文档

- 重写流程安全规则：`references/file-contract.md`
- 快照契约：`references/file-contract.md`
- 章首 / 章末技法（起草前必读）：`references/chapter-craft.md`
- 知情审计与无背景冷读：`references/audit-dimensions.md`
- rewrite manifest 模板：`references/templates.md`
