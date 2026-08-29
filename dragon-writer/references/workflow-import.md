# 模式 C：导入现有章节并续写

## 触发时机

手里有旧章节，但状态文件很弱或缺失。

## 步骤

1. **按文件顺序、标题、或用户给出的拆分规则把源文本拆成有序章节**。
2. **创建或选定目标书**。
3. **从已有证据而非凭空想象构建基础文件**：
   - 用早期章节推断前提与基调
   - 用晚期章节推断当前续写起点
   - 用中段锚点推断弧线演化
   - 用标题目录推断整体结构
4. **按模式 A 写基础文件**（详见 `references/workflow-new-book.md`）。
5. **把导入章节回放到运行时文件**：
   - 保存章节文件
   - 追加含 story_time / elapsed / dramatic_change / novelty_fingerprint 的摘要
   - 从正文证据重建事件时间轴；无法确定的时间写相对锚点或 unknown，不擅自补日期
   - 按角色分别重建信息获知链：事实成立证据与每名 knower 的获知证据分开，找不到路径时保持 unknown
   - 重建关系许可账本：首次相遇、既往历史、称呼 / 接触 / 披露边界、每次跃迁催化和双方不对称状态均须有正文依据
   - 提取当前状态与活跃钩子，并为近章建立情节指纹以检测重复
   - 推断风格指南
   - 在 `book.json` 明确后续章节的 `chapterMinChars` / `chapterTargetChars` / `chapterMaxChars`，并将 `chapterLengthGateFromChapter` 设为“最后一个导入章 + 1”；历史原稿可以保留原长度，之后新写章节必须过硬门禁
   - 创建 `story/import-manifest.json`：逐章记录 chapter、相对路径与实际 SHA-256，并确保 `firstChapter..lastChapter` 每章恰好一条。验证器只有在清单完整、哈希未变且 `chapterLengthGateFromChapter == lastChapter + 1` 时才承认历史长度豁免
   - 运行 `python scripts/migrate_3_13_to_4_0.py <book-dir>` 建立 `legacy_closed` 历史事务。它不倒填不存在的写作计划、Evidence Map 或审计结果；旧资料不足时保留 Markdown 并要求后续人工建立新章 JSON intent
6. **从第一个未写章节起按模式 B 续写**（详见 `references/workflow-continue.md`）。

## 相关文档

- 模式 A（创建新书）：`references/workflow-new-book.md`
- 模式 B（续写）：`references/workflow-continue.md`
- 文件职责与兼容命名：`references/file-contract.md`
- 基础文件模板：`references/templates.md`
