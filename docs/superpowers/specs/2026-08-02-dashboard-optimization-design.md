# Dragon Writer 仪表盘激进重构设计

## 概述

Dragon Writer 写作仪表盘是一个**单文件 HTML**（双击即用），通过 File System Access API 读取书文件夹，实时渲染写作进度、设定完成度、人物关系与章节阅读。本次重构在保持"零依赖、单文件、双击即用"的核心约束下，对内部架构进行全面重写，并大幅提升性能、UX 和可维护性。

## 约束

- **单 HTML 文件**：不能有构建工具、npm 依赖、外部资源（除浏览器原生 API 外）
- **零服务器**：通过 `file://` 协议直接打开，不能依赖 HTTP 服务
- **所有数据在本地**：不上传任何数据到服务器
- **兼容 Chrome/Edge 86+**（File System Access API），webkitdirectory 模式回退兼容 Safari/Firefox

## 架构

### 当前架构（单体）

```
~760 行单体文件
├── CSS (内联，全局选择器)
├── HTML (5 个面板，无组件边界)
└── JS (全局函数，无模块边界)
    ├── MD 解析器 (同步)
    ├── 文件读取 (handle/entries 双路径)
    ├── 数据解析 (正则混杂)
    ├── 渲染 (全部一次性渲染)
    └── 图引擎 (内联，循环永不停止)
```

### 重构后架构（模块化 IIFE）

```
├── CSS (CSS 变量系统 + 作用域化样式)
├── HTML (语义化标签 + ARIA 属性)
└── JS (IIFE 模块，命名空间)
    ├── Store          — 中央状态管理
    ├── FileReader     — 文件读取层
    ├── MDParser       — Markdown 解析（异步分片）
    ├── GraphEngine    — 力导向图引擎（收敛检测 + 暂停/恢复）
    ├── Components     — 各标签页组件
    │   ├── Overview   — 总览
    │   ├── Settings   — 设定完成度
    │   ├── SettingsContent — 设定原文
    │   ├── Characters — 人物关系 + 列表
    │   └── Reader     — 章节阅读
    ├── Router         — 标签路由 + 懒加载
    └── Utils          — 主题/格式化/工具函数
```

## 模块设计

### 1. Store — 中央状态管理

单一数据源，所有组件通过 Store 读取和订阅状态变更。

```js
const Store = {
  state: {
    book: null,          // book.json 解析结果
    chapters: [],        // 章节列表 [{num, title, text, name}]
    roles: [],           // 角色列表 [{tier, name, text}]
    files: {},           // 设定文件原文
    settings: {},        // 设定完成度计算结果
    graph: { nodes: [], edges: [] },
    loading: false,      // 全局加载状态
    tabLoading: {        // 各标签页独立加载状态
      overview: false,
      settings: false,
      'settings-content': false,
      chars: false,
      read: false,
    },
    error: null,         // 全局错误
  },
  listeners: new Map(),  // 组件名 → Set<callback>
  
  on(component, fn),     // 订阅
  off(component, fn),    // 取消订阅
  set(path, val),        // 更新 state，触发相关 listener
  get(path),             // 安全读取
  reset(),               // 清空状态（切换书架时）
}
```

### 2. FileReader — 文件读取层

统一文件读取接口，handle 模式和 entries 模式透明切换。

```js
const FileReader = {
  async read(handle, entries, path) {
    // 自动选择 handle 或 entries 模式
    // 返回 { ok: true, data } 或 { ok: false, error: '...' }
  },
  
  async validate(handle, entries) {
    // 检查必需文件：book.json, chapters/, story/
    // 返回 { valid: true } 或 { valid: false, missing: ['...'], got: '...' }
  },
  
  async loadAll(handle, entries) {
    // 并行读取所有文件，单文件失败不影响其他
    // 优先加载 book.json + chapters 用于快速显示总览
    // 后台加载 story/ 下的文件
    // 返回 { book, chapters, roles, files }
  },
  
  async collectRoles(handle, entries) {
    // 递归遍历 roles/(major|minor|主要角色|次要角色)/ 目录
    // 去重（同名角色只保留第一个）
  },
  
  async collectChapters(handle, entries) {
    // 读取 chapters/ 目录下所有 .md 文件
    // 按文件名排序（数字前缀）
  },
}
```

### 3. MDParser — Markdown 解析

支持异步分片解析，避免大文件阻塞主线程。

```js
const MDParser = {
  parse(src) {
    // 同步解析，用于小文本（内联、摘要）
  },
  
  async parseAsync(src, onProgress) {
    // 分块解析：每 100 行 yield 一次
    // 使用 requestIdleCallback 或 setTimeout(0) 分片
    // 可选 onProgress 回调用于进度显示
  },
  
  parseInline(s) {
    // 内联解析：粗体、斜体、代码、链接、删除线
  },
  
  // 辅助方法
  extractSection(text, re) {
    // 提取某个 ## 标题下的内容
  },
  
  extractField(text, labels) {
    // 从列表式字段中提取标签对应的值
    // 如 `- **欲望**：内容` → "内容"
  },
}
```

**解析改进：**
- 表格单元格内支持内联 Markdown
- 代码块正确识别语言标记
- 任务列表（`- [x]`）渲染为复选框
- 脚注支持（`[^1]`）

### 4. GraphEngine — 力导向图引擎

独立于渲染层，支持完整的生命周期管理。

```js
const GraphEngine = {
  init(canvas, { nodes, edges }) {
    // 初始化节点位置（带随机抖动避免重叠）
    // 绑定事件：pointerdown/move/up/wheel
    // 自适应 DPR
  },
  
  start() {
    // 启动 requestAnimationFrame 循环
    // 逐帧执行物理模拟 + 渲染
  },
  
  pause() {
    // 暂停循环
    // cancelAnimationFrame
  },
  
  resume() {
    // 恢复循环
  },
  
  destroy() {
    // 清理所有资源、事件监听、RAF
  },
  
  // 物理引擎
  physics: {
    tick() {
      // 1. 弹簧力（边）：目标距离 170px，强度 0.008
      // 2. 斥力（所有节点对）：-1400 / d²
      // 3. 中心引力：0.0012 * (center - pos)
      // 4. 阻尼：速度 *= 0.85
    },
    
    isSettled() {
      // 所有节点速度绝对值之和 < 0.5
      // 连续 10 帧满足则认为收敛
    },
    
    warm() {
      // 用户拖拽后加热，恢复物理模拟
    },
  },
  
  // 交互
  zoom: {
    scale: 1,
    apply(delta) { /* 滚轮缩放，限制 0.3~3x */ },
  },
  
  pan: {
    offsetX: 0, offsetY: 0,
    apply(dx, dy) { /* 拖拽平移 */ },
  },
  
  // 选择
  selectNode(i) {
    // 高亮节点 + 邻居 + 边
    // 更新右侧信息面板
    // 同步角色卡片高亮
  },
  
  hitTest(x, y) {
    // 检测点击位置是否在某个节点上
    // 返回节点索引或 -1
  },
}
```

**关键改进：**
- 收敛检测：连续 10 帧速度 < 0.5 阈值则自动停止
- 标签感知：切出 chars 标签时自动 `pause()`
- 滚轮缩放：限制 0.3x~3x，以鼠标位置为中心缩放
- 邻居高亮：选中节点时，其邻居节点加亮，非邻居变暗
- 拖拽后自动恢复物理模拟（加热）

### 5. Components — 标签页组件

每个组件是一个对象，包含 `render()`、`refresh()`、`destroy()` 方法。

#### Overview 组件

```js
const Overview = {
  render() {
    // 进度环（donut chart）
    // 6 张统计卡（总章节、目标章节、总字数、平均字数、单章目标、状态）
    // 当前状态（parseCurrentState）
    // 最近章节表（parseRecentSummaries → 表格渲染）
    // 审计漂移（renderAuditDrift → 折叠卡片）
    // 字数趋势迷你图（canvas 柱状图，按章节显示字数）
  },
}
```

**新增：** 字数趋势迷你图，显示每章字数变化，帮助作者识别"注水章"或"过短章"。

#### Settings 组件（设定完成度）

```js
const Settings = {
  render() {
    // 4 个设定文件进度条
    // 点击展开子项详情
    // 进度条颜色渐变：<30% 红，30-70% 橙，>70% 绿
    // 空文件/未找到文件的友好提示
  },
}
```

**改进：** 进度条颜色语义化，未找到文件显示明确提示而非 0%。

#### SettingsContent 组件（设定原文）

```js
const SettingsContent = {
  render() {
    // 5 个设定文件原文
    // 可折叠展开
    // 异步解析（大文件不阻塞）
    // 显示字数标签
  },
}
```

#### Characters 组件（人物关系）

```js
const Characters = {
  render() {
    // 搜索框 + 筛选（主要/次要/全部）
    // 关系图（GraphEngine 管理）
    // 角色卡片网格
    // 点击卡片 → 高亮图上节点 + 滚动到图
    // 点击图节点 → 高亮卡片 + 显示详情面板
  },
  
  search(query) {
    // 实时过滤角色列表
    // 图上对应节点高亮/变暗
  },
}
```

**新增：** 搜索框、角色 tier 筛选、双向联动（卡片↔图节点）。

#### Reader 组件（章节阅读）

```js
const Reader = {
  currentIndex: -1,
  
  render() {
    // 左栏目录
    // 右栏正文
    // 上一章/下一章按钮
    // 字号调整滑块
    // 导出全本 TXT 按钮
  },
  
  openChapter(i) {
    // 加载并渲染章节
    // 更新目录高亮
    // 滚动到顶部
  },
  
  search(query) {
    // 在当前章节中搜索
    // 高亮匹配文本
    // 显示匹配数量
    // 上下翻查
  },
  
  next() { this.openChapter(this.currentIndex + 1) },
  prev() { this.openChapter(this.currentIndex - 1) },
}
```

**新增：** 章节内搜索、字号调整、键盘快捷键（←/→ 翻章，Ctrl+F 搜索）。

### 6. Router — 标签路由

管理标签页切换、懒加载、过渡动画。

```js
const Router = {
  current: 'overview',
  history: [],  // 浏览历史，支持回退
  
  switch(tab) {
    // 1. 调用当前组件的 onLeave()
    // 2. 显示目标标签的加载状态
    // 3. 如果目标标签未渲染，调用其 render()
    // 4. 过渡动画（200ms 淡入）
    // 5. 更新 URL hash
    // 6. 调用目标组件的 onEnter()
    // 7. 更新 Store 中的 tabLoading
  },
  
  init() {
    // 读取 URL hash 确定初始标签
    // 绑定标签按钮事件
    // 监听键盘快捷键（Ctrl+1~5 切换标签）
  },
}
```

**新增：** 键盘快捷键 Ctrl+1~5 切换标签页。

### 7. Utils — 工具函数

```js
const Utils = {
  // 主题管理
  theme: {
    current: 'auto',  // auto / dark / light
    init() { /* 读取 localStorage + prefers-color-scheme */ },
    toggle() { /* 切换并持久化 */ },
    apply() { /* 设置 CSS 变量 */ },
  },
  
  // 格式化
  fmtNum(n) { /* 数字格式化 1234 → "1,234" */ },
  countWords(s) { /* 中文字数 + 英文单词数 */ },
  statusLabel(s) { /* 状态映射 drafting → "写作中" */ },
  escHtml(s) { /* HTML 转义 */ },
  truncate(s, n) { /* 截断字符串 */ },
  
  // 日期
  fmtDate(d) { /* 日期格式化 */ },
  timeAgo(d) { /* 相对时间 "3 天前" */ },
  
  // 键盘快捷键
  shortcuts: {
    register(key, handler) { /* 注册全局快捷键 */ },
    unregister(key) { /* 注销 */ },
    showPanel() { /* 显示快捷键面板（按 ? 触发） */ },
  },
}
```

## 性能优化

| 优化项 | 措施 | 预期效果 |
|--------|------|----------|
| 图循环 | 收敛检测 + 标签暂停 | CPU 使用率从 15% → 0%（非 chars 标签时） |
| MD 解析 | 异步分片解析 | 大文件解析不阻塞 UI |
| 渲染 | 组件懒加载 | 首次加载只渲染总览标签 |
| 图渲染 | 离屏 Canvas | 避免闪烁，提升帧率 |
| 状态更新 | 按需更新 | 避免全量重新渲染 |
| 物理模拟 | 优化碰撞检测 | 从 O(n²) 减少常数因子 |

## UX 改进

- **过渡动画**：标签切换 200ms 淡入
- **骨架屏**：加载时显示内容骨架，而非空白
- **空状态**：统一设计，带图标和说明文字
- **错误状态**：带重试按钮，友好错误信息
- **键盘快捷键**：`?` 显示面板，`←→` 翻章，`Ctrl+1~5` 切标签，`Ctrl+F` 搜索
- **搜索**：角色搜索、章节内搜索
- **字号调整**：阅读器字号可调
- **字数趋势**：总览页显示柱状图

## 不变的部分

- 仍然是单 HTML 文件，双击即可使用
- 仍然使用 File System Access API + webkitdirectory 兼容模式
- 仍然所有数据在本地读取，不上传服务器
- 仍然从 book.json 读取元数据，从 chapters/ 读取章节
- 仍然兼容 Chrome/Edge 86+，Safari/Firefox 兼容模式
- 仍然使用 IndexedDB 记住上次书架

## 已知 Bug 修复清单

代码分析发现以下关键 Bug，必须在重构中修复：

| # | 严重度 | 问题 | 行号 | 修复方案 |
|---|--------|------|------|----------|
| B1 | 🔴 | `idbSave` 未定义 → `IDB.save` | 353 | 修正函数名 |
| B2 | 🔴 | `e.fullPath` 应为 `e.webkitRelativePath` | 240,268,270,285,305,323 | 统一使用 `e.webkitRelativePath` |
| B3 | 🔴 | Canvas `ctx.font` 使用 `var(--sans)` 无效 | 607,620,629,630 | 读取 CSS 变量值后内联字体名 |
| B4 | 🔴 | rAF 循环永不取消，堆积 | 598-604 | GraphEngine.init() 先 cancel 之前的 raf |
| B5 | 🔴 | `className` 写了 JSX 语法 | 540 | 改为 `class` |
| B6 | 🟡 | `getComputedStyle` 每帧调用 | 608-611,630 | 主题切换时缓存一次 |
| B7 | 🟡 | `selected` 未重置 | 588 | GraphEngine.init() 重置 selected |
| B8 | 🟡 | `nodes.indexOf` 在循环内 O(n²) | 602,628 | 改用循环索引 |
| B9 | 🟡 | 无文件契约别名回退 | 340-345 | 添加别名 fallback 逻辑 |
| B10 | 🟡 | `chapters/index.json` 被忽略 | 279-294 | 优先读取 index.json |
| B11 | 🟡 | 主题切换无 light 模式 | 681-688 | 添加 light/dark/auto 三态 |
| B12 | 🟡 | 无 hash 深链接 | 675-679 | 添加 hashchange 监听 |
| B13 | 🟡 | 无 `prefers-reduced-motion` 支持 | 全局 | 添加媒体查询 |

## 新增功能

| # | 功能 | 说明 | 优先级 |
|---|------|------|--------|
| F1 | 章节搜索 | 在当前章节内搜索关键词，高亮匹配 | 高 |
| F2 | 角色搜索/筛选 | 按名称搜索角色，按 tier 筛选 | 高 |
| F3 | 字数趋势图 | 总览页显示每章字数柱状图 | 中 |
| F4 | 键盘快捷键 | `←→` 翻章，`Ctrl+1~5` 切标签，`?` 显示帮助 | 中 |
| F5 | 字号调整 | 阅读器字号可调 | 中 |
| F6 | 阅读器进度条 | 显示当前章节在全书中的位置 | 低 |
| F7 | 设定文件别名回退 | 兼容旧命名（story_bible.md → story_frame.md 等） | 高 |
| F8 | pending_hooks 展示 | 在总览中显示钩子状态 | 中 |
| F9 | current_focus 展示 | 在总览中显示当前写作焦点 | 中 |
| F10 | 导出文件名安全处理 | 移除文件名中的非法字符 | 高 |
| F11 | 字数统计去 Markdown | 只统计正文字数，不统计语法标记 | 中 |
| F12 | 最近章节表显示完整列 | 显示 state_changes 和 hook_activity | 低 |

## 实施计划

1. 重构 Store 模块
2. 重构 FileReader 模块
3. 重构 MDParser 模块（异步分片）
4. 重构 GraphEngine 模块（收敛检测 + 暂停机制）
5. 重构各 Components（Overview、Settings、SettingsContent、Characters、Reader）
6. 重构 Router 模块（过渡动画 + 懒加载）
7. 重构 Utils 模块（主题、快捷键、格式化）
8. 样式系统重构（CSS 变量 + 组件化）
9. 新增功能：字数趋势图、角色搜索、章节搜索、快捷键
10. 测试与调试