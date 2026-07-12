# Dragon Writer

一套工具无关（tool-neutral）的**长篇虚构小说写作工作流**，以 Claude Code 的 Skill 形态交付，也可在 Codex / opencode 中直接使用。

Dragon Writer 把一本长篇小说拆成一份可审计、可回滚、可跨会话续写的"文件圣经"，外加一份给作者自己看的实时进度页（仪表盘）。**全程不靠记忆，靠文件**。

---

## 它能做什么

### 5+1 种工作流模式

| 模式 | 触发时机 | 做什么 |
| --- | --- | --- |
| **A · 新书** | 一句灵感 / 书名 / 题材 | 建目录、一口气产出全部基础文件骨架（意图 / 故事框架 / 卷纲 / 角色 / 规则 / 状态 / 钩子） |
| **B · 续写** | 书已存在，往下写 | 读工作集 → 写章节意图 → 起草 → **双层质量门禁**（7 点驻场初筛 + 37 维连续审计 · 审-改循环） → 落盘（章节 + 摘要 + 状态 + 钩子 + 快照） |
| **C · 导入** | 手里有旧章节，缺状态文件 | 从旧章反推基础文件，回放导入章节，续写 |
| **D · 转向** | "换方向 / 下一章写 X" | 轻量调 `current_focus.md`，不改整份大纲 |
| **E · 改写 / 修复** | 重写某一章 | **三步回滚机械**：恢复快照 → 清后续产物 → 重写 → 再走双层质检 |
| **F · 仪表盘** | 看进度 / 完成度 / 关系 / 读章节 | 确保书文件夹下有模板一份，**双击 HTML 打开**，选一次文件夹后永远自动反映最新文件 |

### 双层质量门禁

写一章不是写完就定稿，而是过两层：

1. **驻场初筛（7 点）**——主角是否按动机行动、有没有人知道不该知道的、资源 / 关系与状态文件是否对齐……直接、快速。
2. **37 维连续审计 + 审-改循环**——按体裁裁剪出本章节要跑的维度清单（仙侠默认 18–22 维），逐维出报告 → 修订 → **回头从第 1 维再过一遍**（防修 A 打坏 B）→ 留痕审计漂移。详见 `dragon-writer/references/audit-dimensions.md`。

### 写作仪表盘（双击即用）

`dashboard.html` 是一份**运行时模板**，不嵌入任何数据。打开后通过 File System Access API 选择书文件夹（首次授权后 IndexedDB 持久化，后续零交互），运行时读源文件实时计算：

- 写作进度（进度环、字数、完成度）
- 设定完成度（故事框架 / 卷纲 / 规则书 / 当前状态，逐维进度条）
- **设定内容全文**（新增独立标签：4 份设定文件可展开阅读）
- 人物关系图（`<canvas>` 力导向图，可拖拽点击 + 角色卡）
- 章节阅读（目录 + Markdown 渲染 + 上一章 / 下一章导航）
- 章节合并导出 TXT（按章节顺序一键拼成单一 `.txt` 文件并下载）
- 审计漂移（已修复 / 已知漂移两节）

### 受保护上下文 vs 可压缩历史

- **基金会**（premise / 世界法则 / 角色卡 / 规则书）→ 尽量不动。
- **运行时态**（当前状态 / 钩子 / 摘要 / 焦点 / 审计漂移）→ 每章更新。
- **权威顺序**（冲突裁决）：用户指令 > 当前焦点 > 意图 + 规则 > 状态 / 角色 / 钩子 > 大纲 > 旧摘要 > 旧章节正文。

---

## 项目结构

```
dragon-writer/
  SKILL.md                         # 主定义：操作规则、各模式流程、质量门禁
  agents/
    openai.yaml                    # 平台 display_name / 默认提示
  references/
    file-contract.md               # 规范布局 + 文件职责 + 权威顺序 + 兼容命名
    templates.md                   # 全部基础文件模板（双语 heading）
    audit-dimensions.md            # 37 维连续审计：判定规则 + 分级 + 体裁裁剪
    workflow.md                    # 5 种写作模式的详细步骤
    dashboard.html                 # 运行时仪表盘模板（零嵌入数据）
books/
  <book-id>/                       # 一本书
    book.json
    dashboard.html                 # 模式 F 注入的模板（仅一份）
    chapters/{index.json, 0001_*.md}
    story/
      author_intent.md / current_focus.md / book_rules.md
      current_state.md / pending_hooks.md / chapter_summaries.md
      audit-drift.md / style_guide.md
      outline/{story_frame.md, volume_map.md}
      roles/{major, minor}/<name>.md
      runtime/{chapter-NNNN.intent.md, *.rewrite.md}
      snapshots/{0..N}/
```

> `roles/major/` 与 `roles/minor/` 兼容中文命名 `主要角色/` 与 `次要角色/`。
> `bags/` 目录之外的 `roles/` 与 `sample-book/` 为示例书。

---

## 如何使用

### 触发 Dragon Writer

在 Claude Code 中说：

- "帮我写一本仙侠新书，叫《霜寒之纪》" → 模式 A
- "继续写《霜寒之纪》的下一章" → 模式 B
- "把这几章旧稿导入进去" → 模式 C
- "下一章要转到陆恒被追杀" → 模式 D
- "重写第 23 章" → 模式 E
- "看看《霜寒之纪》的进度" → 模式 F

### 打开写作仪表盘

```bash
# 进入某一本书，双击 dashboard.html
open books/<book-id>/dashboard.html        # macOS
xdg-open books/<book-id>/dashboard.html    # Linux
start books/<book-id>/dashboard.html       # Windows
```

首次选择书文件夹并授权；以后打开即自动重连（句柄记入 IndexedDB），永远显示最新内容。推荐 Chrome / Edge。

### 前置条件

- 一个读过 `references/file-contract.md` 的 LLM（由 Claude Code 等代理提供）。
- 任意文件读写能力（Claude Code 的 Read/Write/Edit，或 Codex/opencode 的等价工具）。
- 浏览器支持 File System Access API（Chrome / Edge 86+，或 Safari / Firefox 通过 `webkitdirectory` 兼容模式）。

---

## 文档导读

| 想读什么 | 去哪读 |
| --- | --- |
| 整体怎么用、质量门禁、各模式流程 | `dragon-writer/SKILL.md` |
| 每种模式的具体步骤 | `dragon-writer/references/workflow.md` |
| 规范布局 + 文件职责 + 权威顺序 | `dragon-writer/references/file-contract.md` |
| 基础文件模板（新建 / 回填时照抄） | `dragon-writer/references/templates.md` |
| 37 维审计的规则、分级、体裁裁剪 | `dragon-writer/references/audit-dimensions.md` |
| 仪表盘模板 | `dragon-writer/references/dashboard.html` |

---

## 许可证

TODO
