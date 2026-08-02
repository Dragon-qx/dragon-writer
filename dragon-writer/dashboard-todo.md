# Dragon Writer Dashboard 优化 TODO

本文档只跟踪 `assets/dashboard.html` 及其相关测试、构建和文档工作。小说写作流程、审计体系和通用文件契约的改造继续保留在 `todo.md`。

## 当前基线

以下事项在当前版本中已经实现，后续修改不得回退：

- [x] 仪表盘已移动到 `assets/dashboard.html`。
- [x] Router 首次进入支持强制渲染。
- [x] 加载新数据后会使页面组件失效并强制重绘当前标签。
- [x] 已加载 `current_focus.md`。
- [x] 设定内容页不再依赖先访问设定完成度页。
- [x] 兼容模式开始使用标准化相对路径和精确匹配。
- [x] 章节排序支持非补零数字章号。
- [x] GraphEngine 会移除 resize 监听器。
- [x] 未实现缩放时不再拦截滚轮。
- [x] Markdown 链接已有协议过滤、属性转义和外链 rel。
- [x] 已添加 CSP，并禁止网络连接。
- [x] 已添加基础 tab ARIA、主题按钮标签、搜索状态播报和 reduced-motion。
- [x] 兼容模式会在当前会话缓存 File 列表以支持刷新。
- [x] 已增加加载遮罩和阶段提示。
- [x] TXT 导出会清理非法文件名并使用 UTF-8。

## 第一批：P0 功能阻断项

### 1. 修复 Reader 搜索状态作用域

当前 `_bindSearch()` 把 `marks`、`currentMatch` 和 `cleanHtml` 声明为局部变量，但 `_saveCleanHtml()`、`_highlightText()`、`_updateCurrentMark()` 和 `_clearHighlights()` 把它们当成共享变量使用。打开章节时会产生 `ReferenceError`。

- [x] 将搜索状态改成 Reader 属性：`_marks`、`_currentMatch`、`_cleanHtml`。
- [x] 删除 `_bindSearch()` 中同名局部变量。
- [x] 所有 Reader 方法统一通过 `this._marks` 等属性访问状态。
- [x] `invalidateAll()` 同步清空 Reader 搜索状态。
- [x] `_clearHighlights()` 在 article 不存在时安全返回。
- [x] `_saveCleanHtml()` 在 article 不存在时安全返回。
- [x] 切章、切书、刷新和关闭搜索条时统一重置搜索状态。

### 2. 修复搜索下一项变量名

当前下一项按钮使用不存在的 `matches.length`，正确变量应为 marks。

- [x] 将 `% matches.length` 改为 `% this._marks.length`。
- [x] 增加至少三个重复匹配项的上一项/下一项循环测试。
- [x] 增加仅一个匹配项时的循环测试。
- [x] 增加无匹配项时按钮不报错测试。

### 3. 修复全局正则 lastIndex 污染

TreeWalker 的 `acceptNode` 使用带 `g` 标志的正则执行 `test()`，会在不同文本节点间保留 lastIndex，导致部分节点被跳过。

- [x] 为节点筛选创建不带 `g` 的 tester 正则。
- [x] 真正拆分文本时再使用带 `g` 的 matcher 正则。
- [x] 或在每次 `test()` 前显式设置 `lastIndex = 0`。
- [x] 增加相邻多个文本节点均包含搜索词的测试。

### 4. 修复兼容模式根前缀缓存

`cachedRootPrefix` 是全局单值，切换到第二个目录时不会重新计算，可能导致所有路径匹配失败。

- [x] 每次选择新的 File 列表时重新计算 root prefix。
- [x] 不使用跨 File 列表共享的全局缓存。
- [x] 可使用 `WeakMap<File[]/selection, prefix>` 或把 prefix 随 entries 上下文传递。
- [x] `loadBookFromEntries()` 开始时重置旧 prefix。
- [x] 增加连续选择两个不同根目录的测试。
- [x] 增加同一目录刷新仍能复用正确 prefix 的测试。

### 5. 修复目录验证仍使用模糊路径

`validateBookDir()` 的 entries 分支仍直接对原始路径执行 `/chapters/` 正则，没有使用标准化路径、根前缀和排除目录规则。

- [x] 使用 `toRelPath()` 后的路径验证 chapters。
- [x] 验证时调用 `isExcludedPath()`。
- [x] 只接受根目录下的 `chapters/*.md`。
- [x] 不将 snapshot、backup 或 rewrite 内的章节认作正式章节。
- [x] 决定空 chapters 目录是否为合法新书，并让 handle/entries 两种模式保持一致。
- [x] 若 story 目录缺失，明确是阻断错误还是非阻断警告。

### 6. 只在加载成功后提交数据源

当前 handle 和 cached entries 在验证完成前就可能覆盖上一份有效数据源。

- [x] `lastHandle = handle` 移到 `loadBook()` 成功之后。
- [x] File input 不要在验证成功前覆盖 `cachedEntries`。
- [x] 加载失败后保留上一份可刷新数据源。
- [x] 加载失败后恢复旧书的关系图和当前页面，不留下半清空状态。
- [x] 错误提示明确当前仍显示哪一本书。

### 7. 修复 GraphEngine 销毁与强制路由的竞态

当当前标签是人物关系时，加载器先 `GraphEngine.destroy()`，随后强制切换同一标签会调用旧组件 `onLeave()`，进而执行 `pause()` 和 `draw()`；此时 ctx 已经为空。

- [x] `draw()` 在 ctx 或 canvas 为空时安全返回。
- [x] `pause()` 在 GraphEngine 未初始化时安全返回。
- [x] `resume()` 在 GraphEngine 未初始化时安全返回。
- [x] 调整顺序：先调用当前组件 onLeave，再 destroy，再载入新数据。
- [x] force 刷新同一组件时避免不必要的“旧组件 onLeave → 新组件 onEnter”竞态。
- [x] 增加在人物关系标签中刷新和切书的测试。

### 8. 修复快捷键覆盖

全局 ArrowLeft/ArrowRight 用于切换标签，Reader 再次注册相同键后会覆盖全局 handler；离开 Reader 后 handler 仍存在但什么也不做。

- [x] 不让不同组件直接覆盖同一快捷键 Map key。
- [x] 建立一个统一键盘路由器，根据当前 tab 决定行为。
- [x] Reader 标签中左右键翻章；其他标签中左右键切换 tab。
- [x] 输入框、select、range 聚焦时不触发全局导航。
- [x] Ctrl+F 只在 Reader 标签拦截，其他标签保留浏览器默认行为。
- [x] 增加访问 Reader 前后键盘行为一致性测试。

## 第二批：数据加载与契约

### 9. 将文件映射变成真正的单一来源

当前 HTML 中的 ALIASES 仍是独立维护的常量，只是注释声称与 file contract 同步。

- [x] 建立机器可读的文件契约，如 `references/file-contract.json`。
- [x] Python 脚本、测试和 dashboard 构建过程读取同一份契约。
- [x] 构建 self-contained dashboard 时把契约内联进 HTML。
- [x] CI 检查文档表格和机器契约一致。
- [x] 增加 canonical path、aliases、required、consumer 等字段。

### 10. 完善角色文件兼容

- [x] 决定是否支持 `character_matrix.md` 和 `characters.md`。
- [x] 若支持，增加从单文件解析多个角色的适配器。
- [x] 若不支持，仪表盘给出“旧角色文件格式暂不支持”的明确提示。
- [x] 角色重复时不要静默保留遍历到的第一份，应报告冲突来源。
- [x] 为同名但不同层级角色定义稳定 ID。

### 11. 改善文件缺失诊断

- [x] 区分 required、recommended 和 optional 文件。
- [x] 加载成功后显示非阻断缺失文件清单。
- [x] 每个面板说明自己缺少哪个源文件，而不是统一显示“暂无数据”。
- [x] book.json 解析错误显示行列或近似位置。
- [x] 对章节文件读取失败显示具体文件名。
- [x] 对重复章号、无效文件名和不连续章号显示告警。

### 12. 明确章节来源策略

- [x] 规定 dashboard 是否读取 `chapters/index.json`。
- [x] 若读取 index，定义 index 与实际文件冲突时的显示策略。
- [x] 若完全以章节文件为准，文档明确 index 只用于其他工具。
- [x] 对草稿、rewrite、隐藏文件和非 Markdown 文件定义排除规则。
- [x] 章节号为 0 或无法解析时不要悄悄显示为目录序号，应显示诊断。

## 第三批：Markdown、安全与内容呈现

### 13. 继续强化 URL 处理

- [x] 明确处理 `//example.com` 协议相对 URL。
- [x] 明确处理反斜线、Unicode 冒号和实体编码协议绕过。
- [x] 使用 URL 解析器或严格白名单测试，而不是仅依赖正则。
- [x] 相对链接只允许安全字符和预期路径。
- [x] 增加安全测试样例：javascript、data、vbscript、file、控制字符、引号注入、协议相对 URL。
- [x] CI 验证 CSP 中 `connect-src 'none'` 不被移除。

### 14. 修复 Markdown 硬换行

当前先把双空格换行替换为 `<br>`，随后又经过 inline HTML 转义，可能把该标记显示成文本。

- [x] 不在转义前插入 HTML 字符串。
- [x] 用 token 或分段方式生成硬换行。
- [x] 测试普通换行、双空格换行和连续空行。

### 15. 完善 Markdown 表格解析

- [x] 支持转义管道符 `\|`。
- [x] 不在行内代码中的管道符处分列。
- [x] 处理列数不一致时给出合理补齐或降级展示。
- [x] 超宽表格保留横向滚动。
- [x] 测试事实表、钩子表、道具表和章节摘要表。

### 16. 明确自定义 Markdown 支持范围

- [x] 列出支持的标题、段落、引用、代码块、列表、任务列表、表格、链接和强调语法。
- [x] 不支持的嵌套列表、原始 HTML、图片等语法明确降级规则。
- [x] 删除未使用的异步解析代码，或实现不会破坏跨块 Markdown 结构的流式解析。
- [x] 对超大章节采用可预测的解析策略。

### 17. 避免 innerHTML 状态重建问题

- [x] 搜索高亮不依赖反复保存和恢复整个 `innerHTML`。
- [x] 优先保留原始渲染 DOM，并只增删 mark 节点。
- [x] 恢复高亮时保持事件、选择状态和滚动位置。
- [x] 所有来自书源的数据写入 innerHTML 前经过安全渲染或文本转义。

## 第四批：状态管理与组件架构

### 18. 用数据版本替代分散的 `_rendered`

- [x] Store 增加 `bookVersion` 或 `dataVersion`。
- [x] 每个组件记录最后渲染版本。
- [x] 数据版本变化时自动重绘，无需手工维护五个 `_rendered` 标记。
- [x] Router 只负责导航，不承担数据刷新逻辑。
- [x] 组件提供统一 `mount/render/unmount` 或 `enter/leave/invalidate` 接口。

### 19. 收敛全局可变状态

- [x] 将 lastHandle、cachedEntries、rootPrefix 和 autoResumed 收拢为 SourceSession。
- [x] 将 Reader 搜索、章节、字号状态放入 Reader state。
- [x] 将 Characters 搜索和过滤状态放入 Characters state。
- [x] 将 GraphEngine 生命周期状态封装，不允许外部依赖内部变量。
- [x] 明确刷新、切书、返回落地页时哪些状态保留、哪些重置。

### 20. 改善错误处理

- [x] `pickFolder()` 对非 AbortError 显示错误，不要静默吞掉。
- [x] 手动选择目录或兼容模式时明确将 autoResumed 设为 false。
- [x] 自动恢复失败后保留“点击继续”入口。
- [x] 区分权限拒绝、目录结构错误、JSON 错误和读取错误。
- [x] 避免 catch-all 把编程错误伪装成“文件不存在”。
- [x] 开发模式记录 stack，发布模式显示简洁错误。

## 第五批：关系图优化

### 21. 完善指针交互

- [x] pointerdown 后调用 `setPointerCapture()`。
- [x] 处理 `pointercancel` 和指针离开 canvas。
- [x] 拖拽结束时释放 pointer capture。
- [x] 触屏设备上测试拖动和页面滚动冲突。
- [x] 节点键盘选择通过角色卡或可聚焦替代列表实现。

### 22. 修复 resize 后空白风险

Canvas 改变 width/height 会清空画面；如果物理模拟已经停止，resize handler 当前不会主动重绘。

- [x] resize 完成后调用 draw。
- [x] 保留节点相对位置或按新尺寸缩放坐标。
- [x] 测试窗口缩放、侧栏变化和移动端断点。

### 23. 修复 resume 状态

- [x] resume 时重置 settledCount 和 frameCount，或统一调用 start。
- [x] 已达到 MAX_PHYSICS_FRAMES 后重新进入标签仍可合理绘制。
- [x] 无节点时不启动无意义的动画循环。
- [x] 暂停和恢复不改变已选节点。

### 24. 改善大型关系图性能

- [x] 为节点数设置性能阈值。
- [x] 节点较多时降低迭代频率或使用空间索引近似斥力。
- [x] 预计算节点度数，避免 draw/hitTest 中反复过滤所有 edges。
- [x] 对重边、孤立节点和自环定义显示规则。
- [x] 允许按主要/次要角色过滤图，而不仅过滤下方卡片。

### 25. 改善关系图可读性

- [x] 关系标签过长时截断并提供完整提示。
- [x] 重叠边标签采用偏移或避让。
- [x] 主要/次要角色除颜色外增加形状、边框或文字标识。
- [x] 选中角色时同步滚动并高亮角色卡。
- [x] 角色卡筛选后仍保持正确的图节点索引。
- [x] 明确是否实现画布平移和缩放；未实现时不要在文档中承诺。

## 第六批：Reader 和导出体验

### 26. 改善章节阅读状态

- [x] 刷新同一本书时尽量保留当前章节号，而不是总回到未选择状态。
- [x] 切换不同书时重置章节号。
- [x] 目录当前项增加 `aria-current`。
- [x] 切章后滚动正确的阅读容器到顶部，而不是假定 article 自身可滚动。
- [x] 支持按章节号或标题过滤目录。

### 27. 改善搜索可访问性

- [x] 搜索按钮增加 aria-label。
- [x] 当前匹配使用 `aria-current` 或可读状态。
- [x] Escape 关闭搜索条并恢复焦点。
- [x] 打开搜索条时保存原焦点，关闭后恢复。
- [x] 搜索结果变化保持 aria-live 简洁，避免重复播报整章。

### 28. 改善 TXT 导出

- [x] 提供“保留 Markdown”和“纯正文”两种导出模式。
- [x] 统一换行符策略。
- [x] 大书导出使用分段构造或可控内存策略。
- [x] 导出失败时显示错误。
- [x] 为无标题、重复标题和特殊字符书名增加测试。

## 第七批：加载、权限和离线体验

### 29. 改善自动恢复

- [x] 不在缺少用户手势时强制触发权限请求弹窗。
- [x] queryPermission 非 granted 时显示明确的“点击授权并继续”。
- [x] 自动恢复成功后隐藏多余恢复入口。
- [x] 文档使用“权限仍有效时自动重连”，不承诺永久零交互。
- [x] 增加权限 denied、prompt 和 granted 三种状态测试。

### 30. 改善加载反馈

- [x] Loading overlay 在 app 和 landing 两种状态都可见。
- [x] 防止多次并发加载覆盖彼此结果。
- [x] 使用 load request ID 或 AbortController 忽略过期结果。
- [x] 加载阶段细分为验证目录、读取文件、解析章节和渲染页面。
- [x] 加载失败后恢复按钮可用状态和旧数据源。

### 31. 保持真正自包含和离线

- [x] 不引入 CDN 脚本、字体或外部图片。
- [x] CI 扫描 HTML 中的外部 src/href 资源依赖。
- [x] CSP 保持 connect-src none。
- [x] 所有图标使用文本、内联 SVG 或 data URI。
- [x] 复制到任意书目录后无需构建工具即可运行。

## 第八批：响应式与可访问性

### 32. 完善 tab 键盘模型

- [x] 左右键只在 tablist 或非输入控件场景切换 tab。
- [x] Home/End 跳转第一个/最后一个 tab。
- [x] 切换后焦点移动到新 tab。
- [x] panel hidden、aria-selected 和 tabindex 始终同步。

### 33. 完善移动端布局

- [x] 测试 320、375、768、820、1024 像素宽度。
- [x] appbar 中长书名不挤压操作按钮。
- [x] tablist 在小屏幕可横向滚动或折叠。
- [x] 关系图和角色详情在窄屏正确堆叠。
- [x] Reader 目录在移动端可收起。
- [x] 表格、代码块和趋势图不会撑破页面。

### 34. 完善语义与视觉可访问性

- [x] 检查亮色和暗色主题的对比度。
- [x] 图表颜色满足色觉缺陷场景。
- [x] 所有 icon-only 按钮拥有可见 tooltip 和 aria-label。
- [x] 加载、错误、搜索和导出结果使用合适 live region。
- [x] reduced-motion 下禁用平滑滚动和关系图动画。
- [x] Canvas 提供等价的文字关系列表。

## 第九批：代码组织与构建

### 35. 将开发源码模块化

- [x] 把 Utils、Store、Router、FileLoader、MDParser、GraphEngine、Reader 和各面板拆成源码模块。
- [x] 保留 `assets/dashboard.html` 作为构建产物。
- [x] 添加 build 脚本把 CSS、JS 和契约重新内联为单文件。
- [x] 构建必须确定性，重复构建无无意义 diff。
- [x] 在生成文件顶部记录版本和生成命令。
- [x] 明确禁止直接编辑生成产物，或反过来明确单文件就是源码。

### 36. 清理死亡代码和重复结构

- [x] 删除未使用的 Utils 方法。
- [x] 删除未使用的解析函数和状态字段。
- [x] 删除静态 panel 占位内容与动态模板中的重复 ID/重复结构。
- [x] 删除注释中已完成但仍写“后续实现”的残留说明。
- [x] 使用 lint 检查未声明变量，例如 matches、marks、cleanHtml。

## 第十批：测试与验收

### 37. 增加 dashboard 单元测试

- [x] 测试 root prefix 计算和切换目录。
- [x] 测试精确路径匹配和排除目录。
- [x] 测试 canonical/alias 映射。
- [x] 测试章节排序和无效章号。
- [x] 测试 Markdown URL 安全。
- [x] 测试 Markdown 表格和硬换行。
- [x] 测试完成度计算。
- [x] 测试 Reader 搜索状态和重复匹配。
- [x] 测试关系解析和重复角色。
- [x] 测试 TXT 文件名和内容。

### 38. 增加浏览器集成测试

- [x] 首次打开默认总览。
- [x] 直接通过每个 URL hash 打开。
- [x] 加载标准 fixture。
- [x] 从任意标签刷新。
- [x] 在人物关系标签刷新和切书。
- [x] 连续选择两个不同兼容目录。
- [x] 先访问 Reader 再验证 tab 键盘导航。
- [x] 搜索同一个词多次出现的章节。
- [x] 权限失效后手动恢复。
- [x] 深浅主题切换并重绘关系图。
- [x] 导出 TXT。
- [x] 注入恶意 Markdown 后确认没有脚本执行或网络请求。

### 39. 增加静态质量检查

- [x] JavaScript 语法检查。
- [x] ESLint no-undef，阻止未声明的 matches/marks/cleanHtml。
- [x] HTML 可访问性检查。
- [x] CSP 和外部依赖检查。
- [x] 本地链接检查。
- [x] 构建产物大小监控。
- [x] 测试失败时保存截图和控制台日志到 `tests/artifacts/`。

## 文档同步

### 40. 同步 dashboard 文档

- [x] `references/workflow-dashboard.md` 与当前功能一致。
- [x] `SKILL.md` 只保留何时复制和如何打开 dashboard，不重复详细功能实现。
- [x] README 明确显示 5 份设定文件时包含 style guide。
- [x] README 补充当前焦点和字数趋势。
- [x] 删除未实现的画布平移承诺。
- [x] 将“零交互”改成“权限仍有效时自动重连”。
- [x] 文档说明兼容模式刷新和页面重开后的权限差异。

## Dashboard 最终验收标准

- [x] 打开任意章节不会发生 Reader ReferenceError。
- [x] 搜索上一项、下一项和关闭操作均正常。
- [x] 连续选择不同目录不会复用错误 root prefix。
- [x] 加载失败不会覆盖上一份有效数据源。
- [x] 在人物关系标签刷新或切书不会因空 ctx 崩溃。
- [x] Reader 与 tab 导航快捷键不会互相覆盖。
- [x] 快照、备份和 rewrite 文件不会被误读为权威数据。
- [x] 所有 canonical 和 alias 路径按同一份机器契约解析。
- [x] Markdown 内容不能执行脚本、读取后上传书源数据或突破 CSP。
- [x] 首次加载、刷新、切书、兼容模式和权限恢复均有浏览器测试覆盖。
- [x] 亮色、暗色、移动端和纯键盘操作均可用。
- [x] 最终分发物仍是一份无外部依赖的自包含 HTML。
