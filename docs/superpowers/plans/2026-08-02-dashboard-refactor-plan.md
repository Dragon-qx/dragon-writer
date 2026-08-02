# Dashboard 激进重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重写 `dragon-writer/references/dashboard.html`，修复所有已知 bug，模块化架构，性能优化，UX 增强

**Architecture:** 单 HTML 文件，内部通过 IIFE 命名空间模块化，分为 Store/FileReader/MDParser/GraphEngine/Components/Router/Utils 七大模块

**Tech Stack:** 纯浏览器端 HTML/CSS/JS，File System Access API，Canvas 2D，IndexedDB

**文件:**
- 修改: `dragon-writer/references/dashboard.html`（全部重写，~1200 行）
- 测试: 浏览器手动测试（打开 HTML → 选择 sample-book 文件夹验证各标签页）

## Global Constraints

- 零外部依赖：不引入 npm 包、CDN 资源、构建工具
- 单文件：所有 CSS/HTML/JS 在同一个 `.html` 文件中
- 兼容性：File System Access API + webkitdirectory 双模式
- 数据本地化：所有数据在浏览器本地读取，不上传服务器
- 双击即用：通过 `file://` 协议直接打开

---

### Task 1: CSS 变量系统 + 布局骨架 + 落地页 HTML

**Files:**
- Create: `dragon-writer/references/dashboard.html`（从头开始）

**Interfaces:**
- Produces: 完整的 HTML 骨架 + CSS 变量系统 + 响应式布局 + 落地页模板

- [ ] **Step 1: 写 CSS 变量系统**

```css
:root {
  --bg: #f6f5f1;
  --bg-elevated: #ffffff;
  --bg-subtle: #efeae1;
  --text: #1c1b18;
  --text-muted: #6b6760;
  --border: #e0dcd4;
  --accent: #b5651d;
  --accent-soft: #f0e4d2;
  --success: #4a7c59;
  --danger: #b53b3b;
  --warning: #c97d2b;
  --track: #e7e3db;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow: 0 1px 2px rgba(0,0,0,.04), 0 4px 12px rgba(0,0,0,.04);
  --mono: ui-monospace,"SF Mono","Cascadia Code",Consolas,monospace;
  --serif: "Songti SC","Noto Serif SC","Source Han Serif SC",Georgia,serif;
  --sans: -apple-system,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;
  --font-size-base: 14px;
  --transition-fast: 150ms ease;
  --transition-normal: 200ms ease;
}
@media(prefers-color-scheme:dark) {
  :root.theme-auto {
    --bg: #161513; --bg-elevated: #1f1d1a; --bg-subtle: #26241f;
    --text: #ece7df; --text-muted: #9b9488; --border: #33302a;
    --accent: #d99a4e; --accent-soft: #3a2f1e; --success: #6fae80;
    --track: #2d2a25; --shadow: 0 1px 2px rgba(0,0,0,.4), 0 4px 14px rgba(0,0,0,.35);
  }
}
:root.theme-dark {
  --bg: #161513; --bg-elevated: #1f1d1a; --bg-subtle: #26241f;
  --text: #ece7df; --text-muted: #9b9488; --border: #33302a;
  --accent: #d99a4e; --accent-soft: #3a2f1e; --success: #6fae80;
  --track: #2d2a25; --shadow: 0 1px 2px rgba(0,0,0,.4), 0 4px 14px rgba(0,0,0,.35);
}
:root.theme-light {
  /* 同 :root 默认值，显式声明 */
  --bg: #f6f5f1; --bg-elevated: #ffffff; --bg-subtle: #efeae1;
  --text: #1c1b18; --text-muted: #6b6760; --border: #e0dcd4;
  --accent: #b5651d; --accent-soft: #f0e4d2; --success: #4a7c59;
  --track: #e7e3db; --shadow: 0 1px 2px rgba(0,0,0,.04), 0 4px 12px rgba(0,0,0,.04);
}
@media(prefers-reduced-motion:reduce) {
  *,*::before,*::after { animation-duration:0.01ms !important; transition-duration:0.01ms !important; }
}
```

- [ ] **Step 2: 写 HTML 骨架**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Dragon Writer · 写作仪表盘</title>
<style>/* CSS 在此 */</style>
</head>
<body>
<!-- 落地页 -->
<div id="landing">...</div>
<!-- 应用主体 -->
<div id="app">...</div>
<script>/* JS 在此 */</script>
</body>
</html>
```

- [ ] **Step 3: 写落地页 HTML**

```html
<div id="landing">
  <h1>🐉 Dragon Writer · 写作仪表盘</h1>
  <p>选择某本书的<b>根目录</b>...</p>
  <div class="row">
    <button class="primary" id="pickBtn">📖 选择书架文件夹</button>
    <label class="filelabel">
      <input type="file" id="fileInput" webkitdirectory>
      <button type="button" id="compatBtn">📂 兼容模式选择</button>
    </label>
    <button id="refreshBtn" style="display:none">🔄 刷新</button>
  </div>
  <div id="resumeArea" style="display:none">
    <p>上次打开：<span id="resumeName"></span> · <a href="#" id="resumeLink">点此继续</a></p>
    <p class="hint">或者从下方列表选择其他书：</p>
    <div id="recentBooks"></div>
  </div>
  <div id="loadingIndicator" class="loading" style="display:none">
    <div class="spinner"></div>
    <span>正在加载书源文件...</span>
  </div>
</div>
```

- [ ] **Step 4: 写应用主体 HTML 骨架**

```html
<div id="app">
  <header class="appbar">...</header>
  <div class="layout">
    <nav class="tabs" role="tablist">...</nav>
    <main class="content">
      <section class="panel active" id="panel-overview" role="tabpanel">...</section>
      <section class="panel" id="panel-settings" role="tabpanel">...</section>
      <section class="panel" id="panel-settings-content" role="tabpanel">...</section>
      <section class="panel" id="panel-chars" role="tabpanel">...</section>
      <section class="panel" id="panel-read" role="tabpanel">...</section>
    </main>
  </div>
</div>
```

- [ ] **Step 5: 写布局 CSS（appbar、tabs、content、responsive）**

```css
/* layout grid */
#app { display:none; min-height:100vh; }
body.loaded #landing { display:none; }
body.loaded #app { display:grid; grid-template-rows:auto 1fr; }
.layout { display:grid; grid-template-columns:180px 1fr; }

/* appbar */
.appbar { ... }

/* tabs */
.tabs[role="tablist"] { ... }
.tabs button[role="tab"] { ... }
.tabs button[role="tab"][aria-selected="true"] { ... }

/* responsive */
@media(max-width:820px) {
  .layout { grid-template-columns:1fr; }
  .tabs[role="tablist"] { flex-direction:row; flex-wrap:wrap; height:auto; }
}
```

- [ ] **Step 6: 写基本样式规范（card、grid、button、empty state）**

```css
.card { background:var(--bg-elevated); border:1px solid var(--border); border-radius:var(--radius); box-shadow:var(--shadow); padding:20px; }
.grid { display:grid; gap:16px; }
.grid.stats { grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); }
.empty-state { text-align:center; color:var(--text-muted); padding:40px 20px; }
.empty-state .icon { font-size:40px; margin-bottom:12px; }
.loading { display:flex; align-items:center; gap:10px; color:var(--text-muted); }
.spinner { width:20px; height:20px; border:2px solid var(--border); border-top-color:var(--accent); border-radius:50%; animation:spin .6s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }
```

- [ ] **Step 7: 提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 初始化 CSS 变量系统 + 布局骨架 + 落地页模板"
```

---

### Task 2: Utils 模块 — 工具函数 + 主题 + 快捷键

**Files:**
- Modify: `dragon-writer/references/dashboard.html`（在 `<script>` 中添加 Utils 模块）

**Interfaces:**
- Produces: `Utils` 命名空间对象，包含 `escHtml`, `fmtNum`, `countWords`, `statusLabel`, `truncate`, `fmtDate`, `timeAgo`, `theme.init/toggle`, `shortcuts.register/unregister/showPanel`

- [ ] **Step 1: 添加 Utils 模块代码**

```js
const Utils = (() => {
  // HTML 转义
  const escHtml = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);
  
  // 数字格式化
  const fmtNum = n => (n || 0).toLocaleString('zh-CN');
  
  // 字数统计（去 Markdown 语法）
  const countWords = s => {
    if (!s) return 0;
    // 移除代码块、表格、标题标记
    const clean = s
      .replace(/```[\s\S]*?```/g, '')
      .replace(/^#+\s*/gm, '')
      .replace(/^\|.*\|$/gm, '')
      .replace(/[*_~`]/g, '')
      .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1');
    return (clean.match(/[一-鿿]/g) || []).length + 
           (clean.match(/[A-Za-z0-9]+/g) || []).length;
  };
  
  // 状态标签映射
  const statusLabel = s => ({ outlining:'大纲中', drafting:'写作中', paused:'已暂停', completed:'已完成', active:'进行中' }[s] || s || '—');
  
  // 截断
  const truncate = (s, n = 60) => s && s.length > n ? s.slice(0, n) + '…' : s;
  
  // 日期格式化
  const fmtDate = d => d ? String(d).slice(0, 10) : '';
  const timeAgo = d => {
    if (!d) return '';
    const diff = Date.now() - new Date(d).getTime();
    const days = Math.floor(diff / 86400000);
    if (days < 1) return '今天';
    if (days < 2) return '昨天';
    if (days < 7) return `${days} 天前`;
    if (days < 30) return `${Math.floor(days / 7)} 周前`;
    return fmtDate(d);
  };
  
  // 主题管理
  const theme = (() => {
    const KEY = 'dw-theme';
    let current = 'auto';
    let cssVarCache = {};
    
    const readCSSVar = (name) => {
      return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    };
    
    const refreshCache = () => {
      const root = document.documentElement;
      const style = getComputedStyle(root);
      cssVarCache = {
        accent: style.getPropertyValue('--accent').trim() || '#b5651d',
        textMuted: style.getPropertyValue('--text-muted').trim() || '#6b6760',
        border: style.getPropertyValue('--border').trim() || '#e0dcd4',
        bgSubtle: style.getPropertyValue('--bg-subtle').trim() || '#efeae1',
        text: style.getPropertyValue('--text').trim() || '#1c1b18',
        sans: style.getPropertyValue('--sans').trim() || '-apple-system,sans-serif',
      };
    };
    
    const init = () => {
      try { current = localStorage.getItem(KEY) || 'auto'; } catch { current = 'auto'; }
      apply();
    };
    
    const apply = () => {
      document.documentElement.classList.remove('theme-auto', 'theme-dark', 'theme-light');
      if (current === 'dark') document.documentElement.classList.add('theme-dark');
      else if (current === 'light') document.documentElement.classList.add('theme-light');
      else document.documentElement.classList.add('theme-auto');
      refreshCache();
    };
    
    const toggle = () => {
      current = current === 'dark' ? 'light' : current === 'light' ? 'auto' : 'dark';
      apply();
      try { localStorage.setItem(KEY, current); } catch {}
      return current;
    };
    
    const get = (name) => cssVarCache[name] || readCSSVar(name);
    
    return { init, toggle, apply, get, refresh: refreshCache };
  })();
  
  // 键盘快捷键
  const shortcuts = (() => {
    const registry = new Map();
    const handler = (e) => {
      const key = [e.ctrlKey ? 'Ctrl' : '', e.shiftKey ? 'Shift' : '', e.altKey ? 'Alt' : '', e.key]
        .filter(Boolean).join('+');
      const fn = registry.get(key);
      if (fn) { fn(e); e.preventDefault(); }
    };
    
    const register = (key, fn) => { registry.set(key, fn); if (registry.size === 1) document.addEventListener('keydown', handler); };
    const unregister = (key) => { registry.delete(key); if (registry.size === 0) document.removeEventListener('keydown', handler); };
    
    return { register, unregister };
  })();
  
  return { escHtml, fmtNum, countWords, statusLabel, truncate, fmtDate, timeAgo, theme, shortcuts };
})();
```

- [ ] **Step 2: 提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 Utils 模块（工具函数 + 主题 + 快捷键）"
```

---

### Task 3: Store 模块 — 中央状态管理

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

**Interfaces:**
- Produces: `Store` 命名空间，包含 `state`, `on(component, fn)`, `off(component, fn)`, `set(path, val)`, `get(path)`, `reset()`

- [ ] **Step 1: 添加 Store 模块代码**

```js
const Store = (() => {
  const state = {
    book: null,
    chapters: [],
    roles: [],
    files: {},
    settings: {},
    graph: { nodes: [], edges: [] },
    loading: false,
    error: null,
    tabLoading: {},
  };
  
  const listeners = new Map();
  
  const get = (path) => {
    if (!path) return state;
    return path.split('.').reduce((o, k) => (o && o[k] !== undefined) ? o[k] : null, state);
  };
  
  const set = (path, val) => {
    const keys = path.split('.');
    const lastKey = keys.pop();
    const target = keys.reduce((o, k) => {
      if (o[k] === undefined) o[k] = {};
      return o[k];
    }, state);
    target[lastKey] = val;
    // 通知所有订阅者
    listeners.forEach((fns, component) => {
      fns.forEach(fn => { try { fn(path, val); } catch {} });
    });
  };
  
  const on = (component, fn) => {
    if (!listeners.has(component)) listeners.set(component, new Set());
    listeners.get(component).add(fn);
  };
  
  const off = (component, fn) => {
    const s = listeners.get(component);
    if (s) { s.delete(fn); if (s.size === 0) listeners.delete(component); }
  };
  
  const reset = () => {
    state.book = null;
    state.chapters = [];
    state.roles = [];
    state.files = {};
    state.settings = {};
    state.graph = { nodes: [], edges: [] };
    state.loading = false;
    state.error = null;
    state.tabLoading = {};
  };
  
  return { state, get, set, on, off, reset };
})();
```

- [ ] **Step 2: 提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 Store 中央状态管理模块"
```

---

### Task 4: FileReader 模块 — 文件读取层

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

**Interfaces:**
- Produces: `FileReader` 命名空间，包含 `read(handle, entries, path)`, `validate(handle, entries)`, `loadAll(handle, entries)`, `collectRoles(handle, entries)`, `collectChapters(handle, entries)`

**Bug 修复:**
- `idbSave` → `IDB.save`（B1）
- `e.fullPath` → `e.webkitRelativePath`（B2）
- 添加文件契约别名回退（B9）
- 优先读取 `chapters/index.json`（B10）

- [ ] **Step 1: 写 FileReader 模块代码**

```js
const FileReader = (() => {
  // 统一读取接口
  const read = async (handle, entries, path) => {
    try {
      if (handle) {
        const parts = path.split('/');
        let dir = handle;
        for (let i = 0; i < parts.length - 1; i++) {
          if (!parts[i]) continue;
          dir = await dir.getDirectoryHandle(parts[i]);
        }
        const fh = await dir.getFileHandle(parts[parts.length - 1]);
        return { ok: true, data: await (await fh.getFile()).text() };
      }
      if (entries) {
        const f = entries.find(e => {
          const rel = e.webkitRelativePath || e.relativePath || e.fullPath;
          return rel.endsWith('/' + path) || rel === path;
        });
        if (!f) return { ok: false, error: 'not_found' };
        return { ok: true, data: await f.text() };
      }
      return { ok: false, error: 'no_source' };
    } catch {
      return { ok: false, error: 'not_found' };
    }
  };
  
  // 别名映射：文件契约中定义的旧命名兼容
  const ALIASES = {
    'story/outline/story_frame.md': ['story/story_bible.md', 'story/setting.md', 'story/world.md'],
    'story/book_rules.md': ['story/rules.md'],
    'story/outline/volume_map.md': ['story/volume_map.md'],
    'story/current_state.md': ['story/current_state.md'],
    'story/chapter_summaries.md': ['story/chapter_summaries.md'],
    'story/style_guide.md': ['story/style_guide.md'],
    'story/audit-drift.md': ['story/audit_drift.md'],
  };
  
  // 带别名回退的读取
  const readWithAlias = async (handle, entries, path) => {
    const result = await read(handle, entries, path);
    if (result.ok) return result;
    const aliases = ALIASES[path];
    if (aliases) {
      for (const alias of aliases) {
        const r = await read(handle, entries, alias);
        if (r.ok) return r;
      }
    }
    return result;
  };
  
  // 验证书目录
  const validate = async (handle, entries) => {
    const missing = [];
    const bookResult = await read(handle, entries, 'book.json');
    if (!bookResult.ok) missing.push('book.json');
    // 检查 chapters/ 目录
    let hasChapters = false;
    try {
      if (handle) {
        const dh = await handle.getDirectoryHandle('chapters');
        hasChapters = !!dh;
      } else if (entries) {
        hasChapters = entries.some(e => {
          const rel = e.webkitRelativePath || e.relativePath || e.fullPath || '';
          return /chapters\/.+\.(md|MD)$/.test(rel);
        });
      }
    } catch { hasChapters = false; }
    if (!hasChapters) missing.push('chapters/');
    return { valid: missing.length === 0, missing };
  };
  
  // 收集角色
  const collectRoles = async (handle, entries) => {
    const roles = [];
    const ROLE_RE = /roles\/(?:major|minor|主要角色|次要角色)\/(.+?\.(?:md|MD))$/;
    
    if (handle) {
      async function walk(dir, prefix) {
        for await (const [name, h] of dir.entries()) {
          const path = prefix + '/' + name;
          if (h.kind === 'file' && name.endsWith('.md')) {
            const m = path.match(ROLE_RE);
            if (m) {
              const tier = /次要|minor/.test(path) ? '次要角色' : '主要角色';
              const text = await (await h.getFile()).text();
              roles.push({ tier, name: m[1].replace(/\.md$/i, ''), text });
            }
          } else if (h.kind === 'directory') {
            try { await walk(h, path); } catch {}
          }
        }
      }
      try { await walk(handle, ''); } catch {}
    } else if (entries) {
      for (const e of entries) {
        const rel = e.webkitRelativePath || e.relativePath || e.fullPath || '';
        const m = rel.match(ROLE_RE);
        if (m) {
          const tier = /次要|minor/.test(rel) ? '次要角色' : '主要角色';
          roles.push({ tier, name: m[1].replace(/\.md$/i, ''), text: await e.text() });
        }
      }
    }
    // 去重
    const seen = new Set();
    return roles.filter(r => { const k = r.tier + '|' + r.name; if (seen.has(k)) return false; seen.add(k); return true; });
  };
  
  // 收集章节
  const collectChapters = async (handle, entries) => {
    // 先尝试读取 index.json
    const idxResult = await read(handle, entries, 'chapters/index.json');
    if (idxResult.ok) {
      try {
        const idx = JSON.parse(idxResult.data.replace(/^﻿/, ''));
        const chapters = [];
        for (const item of idx) {
          const f = await read(handle, entries, 'chapters/' + item.file);
          if (f.ok) {
            chapters.push({ num: item.num, title: item.title, name: item.file, text: f.data });
          }
        }
        if (chapters.length) return chapters.sort((a, b) => a.num - b.num);
      } catch {}
    }
    
    // 回退：从文件名读取
    const out = [];
    if (handle) {
      try {
        const dh = await handle.getDirectoryHandle('chapters');
        for await (const [n, h] of dh.entries()) {
          if (n.endsWith('.md') && h.kind === 'file') {
            out.push({ n, text: await (await h.getFile()).text() });
          }
        }
      } catch {}
    } else if (entries) {
      for (const e of entries) {
        const rel = e.webkitRelativePath || e.relativePath || e.fullPath || '';
        if (/chapters\/.+\.(md|MD)$/.test(rel)) {
          out.push({ n: rel.split('/').pop(), text: await e.text() });
        }
      }
    }
    return out.sort((a, b) => a.n.localeCompare(b.n, 'zh', { numeric: true })).map(f => {
      const num = parseInt(f.n) || 0;
      const title = f.n.replace(/^\d+[_\-]?/, '').replace(/\.md$/i, '').trim();
      return { name: f.n, num, title, text: f.text };
    });
  };
  
  // 加载所有书数据
  const loadAll = async (handle, entries) => {
    const readFn = (p) => readWithAlias(handle, entries, p);
    
    const [bjs, sf, vm, br, cs, summ, style, drift, focus, hooks, intent] = await Promise.all([
      readFn('book.json'),
      readFn('story/outline/story_frame.md'),
      readFn('story/outline/volume_map.md'),
      readFn('story/book_rules.md'),
      readFn('story/current_state.md'),
      readFn('story/chapter_summaries.md'),
      readFn('story/style_guide.md'),
      readFn('story/audit-drift.md'),
      readFn('story/current_focus.md'),
      readFn('story/pending_hooks.md'),
      readFn('story/author_intent.md'),
    ]);
    
    const [chapters, roles] = await Promise.all([
      collectChapters(handle, entries),
      collectRoles(handle, entries),
    ]);
    
    return {
      book: bjs.ok ? JSON.parse(bjs.data.replace(/^﻿/, '')) : null,
      chapters,
      roles,
      files: {
        story_frame: sf.data, volume_map: vm.data, book_rules: br.data,
        current_state: cs.data, chapter_summaries: summ.data,
        style_guide: style.data, audit_drift: drift.data,
        current_focus: focus.data, pending_hooks: hooks.data,
        author_intent: intent.data,
      },
    };
  };
  
  return { read, validate, loadAll, collectRoles, collectChapters };
})();
```

- [ ] **Step 2: 提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 FileReader 模块（文件读取 + 别名回退 + index.json 支持）"
```

---

### Task 5: MDParser 模块 — Markdown 解析器

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

**Interfaces:**
- Produces: `MDParser` 命名空间，包含 `parse(src)`, `parseAsync(src)`, `parseInline(s)`, `extractSection(text, re)`, `extractField(text, labels)`

**Bug 修复:**
- 硬换行（B5）：修复双空格换行
- 列表检测（B6）：用标记符号判断，不是文本内容
- XSS 链接（B8）：过滤 javascript: 协议
- 斜体误匹配（B9）：限制 `/.../` 斜体匹配范围

- [ ] **Step 1: 写 MDParser 模块代码**

```js
const MDParser = (() => {
  const esc = s => s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);
  
  const parseInline = (s) => {
    if (!s) return '';
    return s
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*\*([^*]+)\*\*\*/g, '<strong><em>$1</em></strong>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/~~([^~]+)~~/g, '<del>$1</del>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (m, text, url) => {
        // 过滤 javascript: 协议
        const safeUrl = url.replace(/^javascript:/i, '#blocked');
        return `<a href="${safeUrl}">${text}</a>`;
      });
  };
  
  const parse = (src) => {
    const lines = src.replace(/\r\n?/g, '\n').split('\n');
    let i = 0, out = [], pbuf = [];
    
    const flushP = () => {
      if (pbuf.length) {
        // 处理硬换行：双空格 + 换行 → <br>
        const text = pbuf.join('\n').replace(/  \n/g, '<br>\n');
        out.push('<p>' + text.split('\n').map(s => parseInline(s.trim())).join('<br>') + '</p>');
        pbuf = [];
      }
    };
    
    const splitRow = r => r.replace(/^\||\|$/g, '').split('|').map(c => c.trim());
    let tbuf = [];
    const flushT = () => {
      if (tbuf.length < 2) { tbuf.forEach(l => out.push('<p>' + parseInline(l) + '</p>')); tbuf = []; return; }
      const hdr = splitRow(tbuf[0]);
      const aln = splitRow(tbuf[1]);
      const ok = aln.length && aln.every(c => /^:?-+:?$/.test(c.trim()));
      let h = '<table><thead><tr>';
      hdr.forEach(c => h += '<th>' + parseInline(c.trim()) + '</th>');
      h += '</tr></thead><tbody>';
      for (let r = ok ? 2 : 1; r < tbuf.length; r++) {
        const cells = splitRow(tbuf[r]);
        h += '<tr>' + cells.map(c => '<td>' + parseInline(c.trim()) + '</td>').join('') + '</tr>';
      }
      h += '</tbody></table>';
      out.push(h);
      tbuf = [];
    };
    
    while (i < lines.length) {
      const line = lines[i];
      const t = line.trim();
      
      // 代码块
      if (/^(```|~~~)/.test(t)) {
        flushP(); flushT();
        const sym = t.slice(0, 3);
        const code = [];
        i++;
        while (i < lines.length && !lines[i].trim().startsWith(sym)) { code.push(lines[i]); i++; }
        i++;
        out.push('<pre><code>' + esc(code.join('\n')) + '</code></pre>');
        continue;
      }
      
      // 标题
      const hx = t.match(/^(#{1,6})\s+(.+)$/);
      if (hx) { flushP(); flushT(); out.push(`<h${hx[1].length}>${parseInline(hx[2])}</h${hx[1].length}>`); i++; continue; }
      
      // 水平线
      if (/^(\*{3,}|-{3,}|_{3,})$/.test(t)) { flushP(); flushT(); out.push('<hr>'); i++; continue; }
      
      // 引用
      if (t.startsWith('>')) {
        flushP(); flushT();
        const bq = [];
        while (i < lines.length && lines[i].trim().startsWith('>')) { bq.push(lines[i].trim().replace(/^>\s?/, '')); i++; }
        out.push('<blockquote>' + parse(bq.join('\n')).replace(/<\/?p>/g, '') + '</blockquote>');
        continue;
      }
      
      // 表格
      if (t.startsWith('|') && t.endsWith('|')) { flushP(); tbuf.push(t); i++; continue; }
      
      // 列表（使用标记符号判断类型）
      const taskMatch = t.match(/^(\s*)([-*+])\s+\[([ xX])\]\s+(.+)$/);
      const listMatch = t.match(/^(\s*)([-*+]|\d+\.)\s+(.+)$/);
      if (taskMatch || listMatch) {
        flushP(); flushT();
        const items = [];
        const isTask = !!taskMatch;
        const re = isTask ? /^(\s*)([-*+])\s+\[([ xX])\]\s+(.+)$/ : /^(\s*)([-*+]|\d+\.)\s+(.+)$/;
        while (i < lines.length) {
          const m = lines[i].match(re);
          if (!m) break;
          items.push({ chk: isTask ? m[3].toLowerCase() === 'x' : null, txt: m[4], marker: m[2] });
          i++;
        }
        const isOrdered = /^\d/.test(items[0].marker);
        const tag = isOrdered ? 'ol' : 'ul';
        if (items.some(it => it.chk !== null)) {
          out.push(`<${tag}>` + items.map(it => `<li>${it.chk ? '✓ ' : '○ '}${parseInline(it.txt)}</li>`).join('') + `</${tag}>`);
        } else {
          out.push(`<${tag}>` + items.map(it => `<li>${parseInline(it.txt)}</li>`).join('') + `</${tag}>`);
        }
        continue;
      }
      
      if (t === '') { flushP(); flushT(); i++; continue; }
      pbuf.push(line);
      i++;
    }
    flushP(); flushT();
    return out.join('\n');
  };
  
  // 异步分块解析（大文件不阻塞 UI）
  const parseAsync = (src, onProgress) => {
    return new Promise((resolve) => {
      const totalLines = src.split('\n').length;
      const CHUNK_SIZE = 100;
      let result = '';
      let pos = 0;
      
      const processChunk = () => {
        const end = Math.min(pos + CHUNK_SIZE, totalLines);
        const chunk = src.split('\n').slice(pos, end).join('\n');
        result += parse(chunk);
        pos = end;
        if (onProgress) onProgress(pos / totalLines);
        if (pos < totalLines) {
          setTimeout(processChunk, 0);
        } else {
          resolve(result);
        }
      };
      
      setTimeout(processChunk, 0);
    });
  };
  
  // 提取某个标题下的内容
  const extractSection = (text, re) => {
    if (!text) return [];
    const m = text.match(new RegExp(`##?\\s*[^\\n]*(?:${re})[\\s\\S]*?(?=\\n##?\\s|$)`, 'i'));
    if (!m) return [];
    return m[0].replace(/^#+\s*.*\n/, '').trim().split('\n').map(l => l.replace(/^[-*]\s*/, '').trim()).filter(Boolean);
  };
  
  // 从列表式字段中提取标签值
  const extractField = (text, labels) => {
    if (!text) return '';
    const labelList = (Array.isArray(labels) ? labels : [labels]).map(s => String(s).toLowerCase());
    for (const raw of text.split('\n')) {
      const m = raw.match(/^\s*[-*]\s*\*\*\s*([^*]+?)\s*\*\*\s*[：:]\s*(.*)$/);
      if (!m) continue;
      const tag = m[1].trim().toLowerCase();
      if (labelList.some(l => tag === l || tag.includes(l) || l.includes(tag))) return m[2].trim();
    }
    return '';
  };
  
  return { parse, parseAsync, parseInline, extractSection, extractField };
})();
```

- [ ] **Step 2: 提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 MDParser 模块（异步分片解析 + Bug 修复）"
```

---

### Task 6: Router 模块 + 标签页切换

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

**Interfaces:**
- Produces: `Router` 命名空间，包含 `current`, `switch(tab)`, `init()`, `onEnter(tab)`, `onLeave(tab)`
- 依赖: `Store`, `Utils.theme`

- [ ] **Step 1: 写 Router 模块代码**

```js
const Router = (() => {
  let current = 'overview';
  const componentMap = {};
  const transitionDuration = 200;
  
  const register = (name, component) => {
    componentMap[name] = component;
  };
  
  const switchTab = (tab) => {
    // 防止重复切换
    if (tab === current) return;
    
    // 调用旧组件的 onLeave
    const oldComp = componentMap[current];
    if (oldComp && oldComp.onLeave) oldComp.onLeave();
    
    // 更新 tab 按钮状态
    document.querySelectorAll('.tabs [role="tab"]').forEach(b => {
      const isActive = b.dataset.tab === tab;
      b.setAttribute('aria-selected', isActive);
      b.classList.toggle('active', isActive);
    });
    
    // 更新面板
    document.querySelectorAll('.panel').forEach(p => {
      const isActive = p.id === 'panel-' + tab;
      p.classList.toggle('active', isActive);
      p.hidden = !isActive;
    });
    
    // 调用新组件的 onEnter
    const newComp = componentMap[tab];
    if (newComp && newComp.onEnter) newComp.onEnter();
    
    current = tab;
    location.hash = tab;
  };
  
  const init = () => {
    // 读取 URL hash
    const hash = location.hash.replace('#', '');
    if (hash && componentMap[hash]) {
      current = hash;
      // 由启动逻辑调用 switch
    }
    
    // 绑定标签按钮
    document.querySelectorAll('.tabs [role="tab"]').forEach(b => {
      b.addEventListener('click', () => switchTab(b.dataset.tab));
    });
    
    // 监听 hash 变化
    window.addEventListener('hashchange', () => {
      const h = location.hash.replace('#', '');
      if (h && componentMap[h] && h !== current) switchTab(h);
    });
    
    // 注册快捷键 Ctrl+1~5
    Utils.shortcuts.register('Ctrl+1', () => switchTab('overview'));
    Utils.shortcuts.register('Ctrl+2', () => switchTab('settings'));
    Utils.shortcuts.register('Ctrl+3', () => switchTab('settings-content'));
    Utils.shortcuts.register('Ctrl+4', () => switchTab('chars'));
    Utils.shortcuts.register('Ctrl+5', () => switchTab('read'));
    
    // 激活初始面板
    switchTab(current);
  };
  
  return { register, switch, init, get current() { return current; } };
})();
```

- [ ] **Step 2: 提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 Router 模块（标签切换 + 快捷键 + hash 深链接）"
```

---

### Task 7: IndexedDB 持久化 + 自动重连

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

**Bug 修复:**
- `idbSave` → `IDB.save`（B1）

- [ ] **Step 1: 写 IndexedDB 模块**

```js
const IDB = (() => {
  let db = null;
  const DB_NAME = 'dragon-writer-dashboard';
  const STORE_NAME = 'handles';
  const VERSION = 1;
  
  const open = () => new Promise((res, rej) => {
    if (db) return res(db);
    try {
      const r = indexedDB.open(DB_NAME, VERSION);
      r.onupgradeneeded = e => {
        const store = e.target.result.createObjectStore(STORE_NAME);
        // 添加索引用于最近书架列表
        store.createIndex('timestamp', 'timestamp');
      };
      r.onsuccess = e => { db = e.target.result; res(db); };
      r.onerror = () => rej();
    } catch (e) { rej(e); }
  });
  
  const save = async (name, handle) => {
    await open();
    return new Promise((res, rej) => {
      try {
        const t = db.transaction(STORE_NAME, 'readwrite');
        t.objectStore(STORE_NAME).put(handle, name);
        t.oncomplete = () => res();
        t.onerror = () => rej();
      } catch (e) { rej(e); }
    });
  };
  
  const load = async (name) => {
    await open();
    return new Promise((res, rej) => {
      try {
        const t = db.transaction(STORE_NAME, 'readonly');
        const q = t.objectStore(STORE_NAME).get(name);
        q.onsuccess = () => res(q.result);
        q.onerror = () => rej();
      } catch (e) { rej(e); }
    });
  };
  
  const listKeys = async () => {
    await open();
    return new Promise((res, rej) => {
      try {
        const t = db.transaction(STORE_NAME, 'readonly');
        const q = t.objectStore(STORE_NAME).getAllKeys();
        q.onsuccess = () => res(q.result);
        q.onerror = () => rej();
      } catch (e) { rej(e); }
    });
  };
  
  return { save, load, listKeys };
})();
```

- [ ] **Step 2: 编写自动重连逻辑**

```js
// 自动重连
let lastHandle = null;
let autoResumed = false;

const tryResumeSilent = async (h) => {
  try {
    if (!h) return false;
    let perm = await h.queryPermission({ mode: 'read' });
    if (perm !== 'granted') {
      // 注意：requestPermission 需要用户手势，这里静默跳过
      // 用户可点击"点此继续"链接手动触发
      return false;
    }
    autoResumed = true;
    await loadBookFromHandle(h);
    return true;
  } catch (err) {
    console.warn('自动恢复书架失败', err);
    return false;
  }
};

const loadBookFromHandle = async (handle) => {
  Store.set('loading', true);
  lastHandle = handle;
  document.getElementById('refreshBtn').style.display = 'inline-block';
  try {
    const data = await FileReader.loadAll(handle, null);
    populateStore(data);
    // 保存句柄
    try { await IDB.save('last', handle); } catch {}
    document.body.classList.add('loaded');
  } catch (err) {
    Store.set('error', err.message);
    if (!autoResumed) alert('【加载失败】' + err.message);
  } finally {
    Store.set('loading', false);
  }
};
```

- [ ] **Step 3: 提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 IndexedDB 持久化 + 自动重连逻辑（修复 idbSave bug）"
```

---

### Task 8: Overview 组件 — 总览标签页

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

**Interfaces:**
- Consumes: `Store`, `MDParser`, `Utils`
- Registers with: `Router.register('overview', Overview)`

- [ ] **Step 1: 写 Overview 组件（进度环 + 统计卡 + 当前状态 + 最近章节 + 审计漂移 + 字数趋势图）**

```js
const Overview = {
  _rendered: false,
  
  onEnter() {
    if (!this._rendered) this.render();
  },
  
  render() {
    const book = Store.get('book');
    const chapters = Store.get('chapters');
    const files = Store.get('files');
    if (!book) { document.getElementById('panel-overview').innerHTML = '<div class="empty-state"><div class="icon">📚</div>未找到书籍数据</div>'; return; }
    
    const target = book.targetChapters || 0;
    const done = chapters.length;
    const pct = target ? Math.min(100, Math.round(done / target * 100)) : 0;
    const totalWords = chapters.reduce((s, c) => s + Utils.countWords(c.text), 0);
    
    document.getElementById('panel-overview').innerHTML = `
      <h2>总览</h2>
      <p class="lede">本书当前的写作进度与最新状态。</p>
      <div class="card" style="margin-bottom:20px;">
        <div class="ringwrap">
          <div class="ring" style="--p:${pct}">
            <span class="num">${pct}<span class="pct-sym">%</span></span>
          </div>
          <div>
            <div class="ringcaption">已完成 <strong>${done}</strong> / <strong>${target || '—'}</strong> 章</div>
            <div class="ringcaption">约 <strong>${Utils.fmtNum(totalWords)}</strong> 字 / 目标单章 <strong>${Utils.fmtNum(book.chapterWordCount || 3000)}</strong> 字</div>
            <div class="ringcaption muted">${book.updatedAt ? '更新于 ' + Utils.fmtDate(book.updatedAt) : ''}</div>
          </div>
        </div>
      </div>
      <div class="grid stats" id="statGrid">${this._renderStats(book, chapters, totalWords)}</div>
      <div class="section-title">当前状态</div>
      <div class="grid col2" id="stateGrid">${this._renderCurrentState(files.current_state)}</div>
      <div class="section-title">当前焦点</div>
      <div id="focusCard" class="card">${this._renderFocus(files.current_focus)}</div>
      <div class="section-title">最近章节</div>
      <div id="recentChapters" class="card">${this._renderRecentChapters(files.chapter_summaries)}</div>
      <div class="section-title">审计漂移</div>
      <div id="auditDrift" class="card">${this._renderAuditDrift(files.audit_drift)}</div>
      <div class="section-title">字数趋势</div>
      <div id="wordTrend" class="card">${this._renderWordTrend(chapters)}</div>
    `;
    this._rendered = true;
  },
  
  _renderStats(book, chapters, totalWords) {
    const done = chapters.length;
    const target = book.targetChapters || 0;
    const avg = done ? Math.round(totalWords / done) : 0;
    return [
      ['总章节', `${done} 章`],
      ['目标章节', target ? `${target} 章` : '—'],
      ['总字数', Utils.fmtNum(totalWords)],
      ['平均章字数', done ? Utils.fmtNum(avg) : '—'],
      ['单章目标', Utils.fmtNum(book.chapterWordCount || 3000)],
      ['状态', Utils.statusLabel(book.status)],
    ].map(([l, v]) => `<div class="stat card"><div class="label">${l}</div><div class="value">${v}</div></div>`).join('');
  },
  
  _renderCurrentState(text) {
    if (!text) return '<div class="card empty-state">未找到 current_state.md</div>';
    const section = (h) => {
      const m = text.match(new RegExp(`##?\\s*${h}[\\s\\S]*?(?=\\n##?\\s|$)`, 'i'));
      return m ? m[0].replace(/^#+\s*.*\n/, '').trim() : '';
    };
    const items = [
      ['location', '地点/时间', '地点?与?时间'],
      ['protagonist', '主角', '主角'],
      ['truth', '已知真相', '已知真[相]?'],
      ['relationship', '关系', '关系'],
      ['conflict', '当前冲突', '当前冲突'],
    ].map(([k, label, re]) => {
      const s = section(re);
      if (!s) return null;
      return `<div class="state-item"><b>${label}</b><span>${MDParser.parseInline(s.split('\n').filter(l => l.trim()).slice(0, 3).join('；'))}</span></div>`;
    }).filter(Boolean);
    return items.length ? `<div class="state-grid">${items.join('')}</div>` : '<div class="empty-state">暂无状态记录</div>';
  },
  
  _renderFocus(text) {
    if (!text) return '<div class="empty-state">暂无当前焦点</div>';
    const lines = MDParser.parse(text);
    return `<div class="article" style="font-size:14px">${lines}</div>`;
  },
  
  _renderRecentChapters(text) {
    if (!text) return '<div class="empty-state">暂无章节摘要</div>';
    const rows = text.split('\n').filter(l => /^\|\s*[：:]?\d/.test(l.trim()));
    const recent = rows.slice(-6).map(r => {
      const c = r.replace(/^\||\|$/g, '').split('|').map(x => x.trim());
      return { ch: c[0], title: c[1], chars: c[2], events: c[3], change: c[4], hook: c[5], mood: c[6] };
    }).filter(r => r.title);
    if (!recent.length) return '<div class="empty-state">暂无章节摘要</div>';
    return `<div class="table-wrap"><table><thead><tr><th>章</th><th>标题</th><th>角色</th><th>事件</th><th>变化</th><th>钩子</th><th>心境</th></tr></thead><tbody>` +
      recent.slice().reverse().map(r => `<tr><td style="font-family:var(--mono)">${Utils.escHtml(r.ch)}</td><td>${Utils.escHtml(r.title || '—')}</td><td class="muted">${Utils.escHtml(r.chars || '—')}</td><td class="muted">${Utils.escHtml(r.events || '—')}</td><td class="muted">${Utils.escHtml(r.change || '—')}</td><td class="muted">${Utils.escHtml(r.hook || '—')}</td><td class="muted">${Utils.escHtml(r.mood || '—')}</td></tr>`).join('') +
      `</tbody></table></div>`;
  },
  
  _renderAuditDrift(text) {
    if (!text) return '<div class="empty-state">暂无审计漂移记录</div>';
    const section = (title) => {
      const m = text.match(new RegExp(`## ${title}([\\s\\S]*?)(?=\\n## |$)`, 'i'));
      if (!m || !m[1].trim()) return '';
      return m[1];
    };
    const renderDriftSection = (title, body) => {
      const items = body.split(/\n###\s+/).filter(Boolean);
      return `<div class="drift-section"><div class="drift-title">${title}</div>` +
        items.map(it => {
          const li = it.split('\n').filter(l => l.trim());
          const head = li.shift() || '';
          return `<div class="drift-item"><b>${Utils.escHtml(head.trim().replace(/^第\d+章 · /, ''))}</b>` +
            li.map(l => `<div class="muted">${Utils.escHtml(l.replace(/^-\s*/, '').trim())}</div>`).join('') +
            `</div>`;
        }).join('') + `</div>`;
    };
    const fixed = section('已修复');
    const open = section('已知漂移');
    let out = '';
    if (fixed) out += renderDriftSection('已修复', fixed);
    if (open) out += renderDriftSection('已知漂移', open);
    return out || `<div class="article">${MDParser.parse(text)}</div>`;
  },
  
  _renderWordTrend(chapters) {
    if (!chapters.length) return '<div class="empty-state">暂无章节数据</div>';
    // 用 Canvas 画柱状图
    const maxWords = Math.max(...chapters.map(c => Utils.countWords(c.text)), 1);
    const barWidth = Math.max(4, Math.min(20, 600 / chapters.length));
    const gap = 2;
    const height = 120;
    const width = Math.max(600, chapters.length * (barWidth + gap));
    const accent = Utils.theme.get('accent');
    const muted = Utils.theme.get('textMuted');
    
    const bars = chapters.map((c, i) => {
      const h = (Utils.countWords(c.text) / maxWords) * (height - 20);
      const x = i * (barWidth + gap);
      const y = height - 10 - h;
      return `<rect x="${x}" y="${y}" width="${barWidth}" height="${h}" fill="${accent}" opacity="0.7" rx="1">
        <title>第${c.num || (i + 1)}回: ${Utils.fmtNum(Utils.countWords(c.text))} 字</title>
      </rect>`;
    }).join('');
    
    // 目标线
    const targetWords = Store.get('book')?.chapterWordCount || 3000;
    const targetY = height - 10 - (targetWords / maxWords) * (height - 20);
    const targetLine = `<line x1="0" y1="${targetY}" x2="${width}" y2="${targetY}" stroke="${muted}" stroke-dasharray="4,3" stroke-width="1"/>
      <text x="${width - 4}" y="${targetY - 4}" fill="${muted}" font-size="10" text-anchor="end">目标 ${Utils.fmtNum(targetWords)} 字</text>`;
    
    return `<div style="overflow-x:auto"><svg width="${width}" height="${height + 20}" viewBox="0 0 ${width} ${height + 20}">
      ${bars}${targetLine}
    </svg></div><div class="muted" style="font-size:12px;margin-top:4px">每章字数（鼠标悬停查看具体数值）</div>`;
  },
};
```


```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 Overview 组件（总览 + 字数趋势图 + 当前焦点）"
```

---

### Task 9: Settings 组件 — 设定完成度 + 设定内容

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

**Interfaces:**
- Consumes: `Store`, `MDParser`, `Utils`
- Registers with: `Router.register('settings', Settings)`, `Router.register('settings-content', SettingsContent)`

- [ ] **Step 1: 写 Settings 组件（设定完成度）**

```js
const Settings = {
  _rendered: false,
  
  onEnter() {
    if (!this._rendered) this.render();
  },
  
  render() {
    const files = Store.get('files');
    const domains = [
      { key: 'story_frame', title: '故事框架 (story_frame.md)', subs: ['主题[与和]基调', '前[台景]故事|背景故事', '核心冲突|对手', '世界[法]?[则律]', '终局[目][标]'] },
      { key: 'volume_map', title: '卷纲 (volume_map.md)', subs: ['弧线[结构]?|[故]?事弧线', '情感曲线', '钩子[种伏]?[子]?|回报图|伏笔', '人[物][角色]?弧线|角色成长', '节奏[原]?[则]?'] },
      { key: 'book_rules', title: '规则书 (book_rules.md)', subs: ['POV|[视][角]', '题材[规]?[则]', '定局锁|硬锁|canon', '力[量]?|限制', '禁[手止]', '风[格]?[约]?束'] },
      { key: 'current_state', title: '当前状态 (current_state.md)', subs: ['[当]?[前]?章节|进度', '地点|时间', '主角', '已知真[相]?|线索', '关系|人际', '资源|伤势|库存', '冲[突]'] },
    ];
    
    const completion = domains.map(d => {
      const text = files[d.key];
      if (!text) return { key: d.key, title: d.title, present: false, pct: 0, items: [] };
      const items = d.subs.map(re => {
        const sec = text.match(new RegExp('##?\\s*[^\\n]*' + re + '[\\s\\S]*?(?=\\n##?\\s|$)', 'i'));
        let filled = false;
        if (sec) {
          const body = sec[0].replace(/^.*\n/, '').trim();
          filled = body.length > 0 && !/^[-\s]*$/.test(body) && !/待[编写定充实]|TODO|xx|请输入|TBD|待补|占位/i.test(body);
        }
        return { label: re.replace(/[\[\]?|]/g, c => ({ '[': '', ']': '', '?': '', '|': ' / ' })[c]), ok: filled };
      });
      const pct = items.length ? Math.round(items.filter(i => i.ok).length / items.length * 100) : 0;
      return { key: d.key, title: d.title, present: true, pct, items };
    });
    
    // 保存到 Store 供其他组件使用
    Store.set('settings', completion);
    
    document.getElementById('panel-settings').innerHTML = `
      <h2>设定完成度</h2>
      <p class="lede">基于书源文件中各子章节的填充情况自动计算。展开可逐项查看。</p>
      ${completion.map((d, idx) => `
        <div class="card domain" id="dom-${idx}">
          <div class="row" tabindex="0" role="button" aria-expanded="${d.pct < 100}">
            <span class="chev">▶</span>
            <span class="name">${Utils.escHtml(d.title)}</span>
            ${d.present ? `<span class="pct" style="color:${this._pctColor(d.pct)}">${d.pct}%</span>` : '<span class="pct muted">未找到</span>'}
          </div>
          <div class="progress-wrap" style="margin-left:16px;">
            <div class="progress-bar">
              <span style="width:${d.pct}%;background:${this._pctColor(d.pct)}"></span>
            </div>
          </div>
          <ul>${d.items.map(it => `<li class="${it.ok ? 'ok' : ''}">${Utils.escHtml(it.label)}</li>`).join('')}</ul>
        </div>
      `).join('')}
    `;
    
    // 绑定展开事件
    completion.forEach((d, idx) => {
      const el = document.getElementById('dom-' + idx);
      if (!el) return;
      const row = el.querySelector('.row');
      row.addEventListener('click', () => {
        el.classList.toggle('open');
        row.setAttribute('aria-expanded', el.classList.contains('open'));
      });
      row.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); row.click(); }
      });
      if (d.pct < 100) el.classList.add('open');
    });
    
    this._rendered = true;
  },
  
  _pctColor(pct) {
    if (pct < 30) return 'var(--danger)';
    if (pct < 70) return 'var(--warning)';
    return 'var(--success)';
  },
  
  onLeave() {},
};
```

- [ ] **Step 2: 写 SettingsContent 组件（设定原文）**

```js
const SettingsContent = {
  _rendered: false,
  
  onEnter() {
    if (!this._rendered) this.render();
  },
  
  render() {
    const files = Store.get('files');
    const SETTING_FILES = [
      { key: 'story_frame', title: '故事框架' },
      { key: 'volume_map', title: '卷纲' },
      { key: 'book_rules', title: '规则书' },
      { key: 'current_state', title: '当前状态' },
      { key: 'style_guide', title: '风格指南' },
    ];
    
    const settings = Store.get('settings') || [];
    
    document.getElementById('panel-settings-content').innerHTML = `
      <h2>设定内容</h2>
      <p class="lede">全部设定文件的完整原文，可在仪表盘内直接阅读。</p>
      ${SETTING_FILES.filter(f => files[f.key]).map((f, idx) => {
        const text = files[f.key];
        const comp = settings.find(s => s.key === f.key);
        const pct = comp ? comp.pct : 0;
        return `<div class="card settingfile open" id="sfc-${idx}">
          <div class="row" tabindex="0" role="button" aria-expanded="true">
            <span class="chev">▶</span>
            <span class="name">${Utils.escHtml(f.title)}</span>
            <span class="tag">${Utils.fmtNum(Utils.countWords(text))} 字</span>
            <span class="pct" style="color:${this._pctColor(pct)}">${pct}% 完成</span>
          </div>
          <div class="body"><div class="article">${MDParser.parse(text)}</div></div>
        </div>`;
      }).join('') || '<div class="card empty-state">暂无设定文件</div>'}
    `;
    
    SETTING_FILES.filter(f => files[f.key]).forEach((f, idx) => {
      const el = document.getElementById('sfc-' + idx);
      if (!el) return;
      const row = el.querySelector('.row');
      row.addEventListener('click', () => {
        el.classList.toggle('open');
        row.setAttribute('aria-expanded', el.classList.contains('open'));
      });
      row.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); row.click(); }
      });
    });
    
    this._rendered = true;
  },
  
  _pctColor(pct) {
    if (pct < 30) return 'var(--danger)';
    if (pct < 70) return 'var(--warning)';
    return 'var(--success)';
  },
};
```

- [ ] **Step 3: 注册组件**

```js
Router.register('settings', Settings);
Router.register('settings-content', SettingsContent);
```

- [ ] **Step 4: 提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 Settings 组件（设定完成度 + 设定原文）"
```

---

### Task 10: GraphEngine 模块 — 力导向图引擎

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

**Bug 修复:**
- rAF 循环永不取消（B4）：init 时先 cancel 旧 raf
- `getComputedStyle` 每帧调用（B6）：使用 Utils.theme.get() 缓存
- Canvas `ctx.font` 使用 `var(--sans)`（B3）：使用内联字体名
- `nodes.indexOf` 在循环内 O(n²)（B8）：使用索引
- `selected` 未重置（B7）：init 时重置

- [ ] **Step 1: 写 GraphEngine 模块代码**

```js
const GraphEngine = (() => {
  let canvas, ctx, W = 0, H = 0;
  let nodes = [], edges = [];
  let selected = -1, dragging = -1;
  let raf = null;
  let physicsRunning = false;
  let settledCount = 0;
  const SETTLE_THRESHOLD = 0.5;
  const SETTLE_FRAMES = 10;
  
  const init = (cvs, gdata) => {
    // 取消旧的 rAF
    if (raf) { cancelAnimationFrame(raf); raf = null; }
    
    canvas = cvs;
    ctx = canvas.getContext('2d');
    selected = -1;
    dragging = -1;
    physicsRunning = false;
    settledCount = 0;
    
    const resize = () => {
      const r = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = r.width * dpr;
      canvas.height = r.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      W = r.width;
      H = r.height;
    };
    resize();
    window.addEventListener('resize', resize);
    
    nodes = gdata.nodes.map((n, i) => ({
      ...n,
      x: W / 2 + (Math.random() - 0.5) * 200,
      y: H / 2 + (Math.random() - 0.5) * 200,
      vx: 0, vy: 0,
    }));
    edges = gdata.edges;
    
    // 事件绑定
    canvas.onpointerdown = (e) => {
      const h = hitTest(e);
      dragging = h;
      if (h >= 0) {
        selectNode(h);
        // 拖拽时恢复物理模拟
        if (!physicsRunning) start();
      }
    };
    canvas.onpointermove = (e) => {
      if (dragging >= 0) {
        const r = canvas.getBoundingClientRect();
        nodes[dragging].x = e.clientX - r.left;
        nodes[dragging].y = e.clientY - r.top;
        nodes[dragging].vx = 0;
        nodes[dragging].vy = 0;
      }
      canvas.style.cursor = hitTest(e) >= 0 ? 'pointer' : 'grab';
    };
    canvas.onpointerup = () => { dragging = -1; };
    canvas.onwheel = (e) => {
      e.preventDefault();
      // 缩放（简化实现，完整版需要矩阵变换）
    };
    
    start();
  };
  
  const start = () => {
    if (physicsRunning) return;
    physicsRunning = true;
    settledCount = 0;
    loop();
  };
  
  const pause = () => {
    physicsRunning = false;
    if (raf) { cancelAnimationFrame(raf); raf = null; }
    // 暂停时绘制一帧静态图
    draw();
  };
  
  const resume = () => {
    if (!physicsRunning) {
      physicsRunning = true;
      loop();
    }
  };
  
  const destroy = () => {
    if (raf) { cancelAnimationFrame(raf); raf = null; }
    physicsRunning = false;
    canvas.onpointerdown = null;
    canvas.onpointermove = null;
    canvas.onpointerup = null;
    canvas.onwheel = null;
    nodes = [];
    edges = [];
  };
  
  const loop = () => {
    if (!physicsRunning) return;
    
    // 物理模拟
    for (const n of nodes) { n.vx *= 0.85; n.vy *= 0.85; }
    
    // 弹簧力
    for (const e of edges) {
      const a = nodes[e.s], b = nodes[e.t];
      const dx = b.x - a.x, dy = b.y - a.y;
      const d = Math.sqrt(dx * dx + dy * dy) || 1;
      const f = (d - 170) * 0.008;
      const ux = dx / d, uy = dy / d;
      a.vx += ux * f; a.vy += uy * f;
      b.vx -= ux * f; b.vy -= uy * f;
    }
    
    // 斥力
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        let dx = b.x - a.x, dy = b.y - a.y;
        const d = Math.sqrt(dx * dx + dy * dy) || 1;
        const f = -1400 / (d * d);
        const ux = dx / d, uy = dy / d;
        a.vx += ux * f; a.vy += uy * f;
        b.vx -= ux * f; b.vy -= uy * f;
      }
    }
    
    // 中心引力
    for (const n of nodes) {
      n.vx += (W / 2 - n.x) * 0.0012;
      n.vy += (H / 2 - n.y) * 0.0012;
    }
    
    // 更新位置
    let totalSpeed = 0;
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      if (i !== dragging) {
        n.x += n.vx;
        n.y += n.vy;
        n.x = Math.max(30, Math.min(W - 30, n.x));
        n.y = Math.max(30, Math.min(H - 30, n.y));
      }
      totalSpeed += Math.abs(n.vx) + Math.abs(n.vy);
    }
    
    // 收敛检测
    if (totalSpeed < SETTLE_THRESHOLD) {
      settledCount++;
      if (settledCount >= SETTLE_FRAMES) {
        physicsRunning = false;
        draw();
        return;
      }
    } else {
      settledCount = 0;
    }
    
    draw();
    raf = requestAnimationFrame(loop);
  };
  
  const draw = () => {
    ctx.clearRect(0, 0, W, H);
    
    if (!nodes.length) {
      ctx.fillStyle = Utils.theme.get('textMuted');
      ctx.font = '14px ' + Utils.theme.get('sans');
      ctx.textAlign = 'center';
      ctx.fillText('暂无角色数据', W / 2, H / 2);
      return;
    }
    
    const accent = Utils.theme.get('accent');
    const lineColor = Utils.theme.get('border');
    const labelColor = Utils.theme.get('textMuted');
    const bgSoft = Utils.theme.get('bgSubtle');
    const minorColor = Utils.theme.get('textMuted');
    const textColor = Utils.theme.get('text');
    const sans = Utils.theme.get('sans');
    
    // 连线
    for (const e of edges) {
      const a = nodes[e.s], b = nodes[e.t];
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = lineColor;
      ctx.globalAlpha = selected >= 0 && (e.s === selected || e.t === selected) ? 0.8 : 0.25;
      ctx.lineWidth = selected >= 0 && (e.s === selected || e.t === selected) ? 2.5 : 1.2;
      ctx.stroke();
      ctx.globalAlpha = 1;
      
      // 边标签
      if (e.label && (selected < 0 || e.s === selected || e.t === selected)) {
        const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        const txt = e.label;
        ctx.font = '11px ' + sans;
        const tw = ctx.measureText(txt).width;
        ctx.fillStyle = bgSoft;
        ctx.fillRect(mx - tw / 2 - 4, my - 7, tw + 8, 14);
        ctx.fillStyle = labelColor;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(txt, mx, my);
      }
    }
    
    // 节点
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      const r = 18 + Math.min(14, edges.filter(e => e.s === i || e.t === i).length * 2);
      const isDimmed = selected >= 0 && i !== selected && !edges.some(e => (e.s === selected && e.t === i) || (e.t === selected && e.s === i));
      
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.globalAlpha = isDimmed ? 0.3 : 1;
      ctx.fillStyle = /次要|minor/.test(n.tier) ? minorColor : accent;
      ctx.fill();
      ctx.globalAlpha = 1;
      
      if (i === selected) {
        ctx.lineWidth = 3;
        ctx.strokeStyle = accent;
        ctx.stroke();
      }
      
      // 节点内文字
      ctx.fillStyle = '#fff';
      ctx.font = `${Math.round(r * 0.7)}px ${sans}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(n.name.slice(0, 3), n.x, n.y);
      
      // 节点下方名称
      ctx.fillStyle = isDimmed ? labelColor : textColor;
      ctx.font = '12px ' + sans;
      ctx.textBaseline = 'alphabetic';
      ctx.fillText(n.name, n.x, n.y + r + 12);
    }
  };
  
  const hitTest = (e) => {
    const r = canvas.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const radius = 18 + Math.min(14, edges.filter(ed => ed.s === i || ed.t === i).length * 2);
      if ((mx - n.x) ** 2 + (my - n.y) ** 2 < radius ** 2) return i;
    }
    return -1;
  };
  
  const selectNode = (i) => {
    selected = i;
    draw();
    const info = document.getElementById('graphInfo');
    if (i < 0) {
      info.innerHTML = '<div class="empty-state">点击图中节点或右侧角色卡片，查看该角色的故事功能、欲望 / 恐惧、当前状态与关系。</div>';
      return;
    }
    const n = nodes[i];
    const fields = [
      ['故事功能', n.func],
      ['欲望', n.desire],
      ['恐惧', n.fear],
      ['当前状态', n.state],
      ['弧线', n.arc],
      ['秘密', n.secrets],
    ].filter(a => a[1]);
    const rels = edges.filter(e => e.s === i || e.t === i).map(e => {
      const o = nodes[e.s === i ? e.t : e.s];
      return `<div class="rel-item"><span class="rname">${Utils.escHtml(o.name)}</span>${e.label ? ' — ' + MDParser.parseInline(e.label) : ''}</div>`;
    });
    info.innerHTML = `<div class="name">${Utils.escHtml(n.name)}</div><div class="tier">${Utils.escHtml(n.tier)}</div>` +
      (fields.length ? `<dl>${fields.map(([k, v]) => `<dt>${Utils.escHtml(k)}</dt><dd>${MDParser.parseInline(v)}</dd>`).join('')}</dl>` : '') +
      (rels.length ? `<div class="rels">${rels.join('')}</div>` : '');
  };
  
  return { init, start, pause, resume, destroy, selectNode, hitTest };
})();
```

- [ ] **Step 2: 提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 GraphEngine 模块（力导向图 + 收敛检测 + 暂停恢复）"
```

---

### Task 11: Characters 组件 — 人物关系标签页

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

- [ ] **Step 1: 写 buildGraph 数据构建函数 + Characters 组件**

```js
// 数据构建
const buildGraph = (roles) => {
  const accent = Utils.theme.get('accent');
  const minorColor = Utils.theme.get('textMuted');
  const nodes = roles.map((r, i) => ({
    i, name: r.name, tier: r.tier,
    color: /次要|minor/.test(r.tier) ? minorColor : accent,
    func: MDParser.extractSection(r.text, 'Story [Ff]unction|故事功能|角色[定定]?[位义]|功能').slice(0, 6).join('；'),
    desire: MDParser.extractField(r.text, ['欲望', 'desire']) || MDParser.extractSection(r.text, '[Dd]esire|欲望').slice(0, 6).join('；'),
    fear: MDParser.extractField(r.text, ['恐惧', 'fear']) || MDParser.extractSection(r.text, '[Ff]ear|恐惧').slice(0, 6).join('；'),
    state: MDParser.extractField(r.text, ['当前状态', 'current state']) || MDParser.extractSection(r.text, '[Cc]urrent [Ss]tate|当前状态').slice(0, 6).join('；'),
    arc: MDParser.extractField(r.text, ['弧线', '成长', 'arc']) || MDParser.extractSection(r.text, '[Aa]rc|弧线|成长').slice(0, 6).join('；'),
    secrets: MDParser.extractSection(r.text, '[Ss]ecrets|秘密').slice(0, 6).join('；'),
  }));
  const nameIdx = new Map(nodes.map(nd => [nd.name.toLowerCase(), nd.i]));
  const edges = [];
  roles.forEach(r => {
    const lines = MDParser.extractSection(r.text, '[Rr]elationships?|关系[网战]?');
    const si = nodes.findIndex(nd => nd.name === r.name);
    for (const l of lines) {
      const m = l.match(/^([^:：\-（\(]{1,20})\s*[—\-:：]\s*(.+)$/);
      if (m) {
        const ti = nameIdx.get(m[1].trim().toLowerCase());
        if (ti !== undefined && ti !== si) edges.push({ s: si, t: ti, label: m[2].trim() });
      }
    }
  });
  return { nodes, edges };
};

// Characters 组件
const Characters = {
  _rendered: false,
  _searchQuery: '',
  _filterTier: 'all',
  
  onEnter() {
    if (!this._rendered) this.render();
    GraphEngine.resume();
  },
  
  onLeave() {
    GraphEngine.pause();
  },
  
  render() {
    const roles = Store.get('roles');
    const graph = buildGraph(roles);
    Store.set('graph', graph);
    
    document.getElementById('panel-chars').innerHTML = `
      <h2>人物关系</h2>
      <p class="lede">点击节点查看角色详情。节点颜色区分主要 / 次要角色。</p>
      <div class="char-controls">
        <input type="search" id="charSearch" placeholder="搜索角色名称..." class="search-input">
        <select id="charFilter" class="filter-select">
          <option value="all">全部角色</option>
          <option value="major">主要角色</option>
          <option value="minor">次要角色</option>
        </select>
      </div>
      <div class="section-title">关系图</div>
      <div class="graphwrap card" style="padding:10px;margin-bottom:20px;">
        <div class="gfx"><canvas id="graph"></canvas></div>
        <aside class="info" id="graphInfo">
          <div class="empty-state">点击图中节点或右侧角色卡片，查看该角色的故事功能、欲望 / 恐惧、当前状态与关系。</div>
        </aside>
      </div>
      <div class="section-title">角色列表</div>
      <div class="char-list" id="charList"></div>
    `;
    
    // 初始化图
    GraphEngine.init(document.getElementById('graph'), graph);
    this._renderCharList(graph.nodes);
    
    // 绑定搜索和筛选
    const searchInput = document.getElementById('charSearch');
    const filterSelect = document.getElementById('charFilter');
    searchInput.addEventListener('input', (e) => {
      this._searchQuery = e.target.value;
      this._renderCharList(graph.nodes);
    });
    filterSelect.addEventListener('change', (e) => {
      this._filterTier = e.target.value;
      this._renderCharList(graph.nodes);
    });
    
    // 角色卡片点击
    document.getElementById('charList').addEventListener('click', (e) => {
      const c = e.target.closest('.charcard');
      if (c) {
        const i = parseInt(c.dataset.i);
        GraphEngine.selectNode(i);
        // 高亮卡片
        document.querySelectorAll('.charcard').forEach(el => el.style.borderColor = '');
        c.style.borderColor = 'var(--accent)';
      }
    });
    
    this._rendered = true;
  },
  
  _renderCharList(nodes) {
    const query = this._searchQuery.toLowerCase().trim();
    const filter = this._filterTier;
    const filtered = nodes.filter(n => {
      if (filter === 'major' && /次要|minor/.test(n.tier)) return false;
      if (filter === 'minor' && !/次要|minor/.test(n.tier)) return false;
      if (query && !n.name.toLowerCase().includes(query)) return false;
      return true;
    });
    document.getElementById('charList').innerHTML = filtered.length
      ? filtered.map(nd => `
        <div class="charcard" data-i="${nd.i}">
          <div class="name">${Utils.escHtml(nd.name)}</div>
          <div class="tier">${Utils.escHtml(nd.tier)}${nd.func ? ' · ' + MDParser.parseInline(nd.func) : ''}</div>
          ${nd.desire ? `<div class="kv"><b>欲</b>${MDParser.parseInline(nd.desire)}</div>` : ''}
          ${nd.fear ? `<div class="kv"><b>惧</b>${MDParser.parseInline(nd.fear)}</div>` : ''}
          ${nd.state ? `<div class="kv"><b>今</b>${MDParser.parseInline(nd.state)}</div>` : ''}
          ${nd.arc ? `<div class="kv"><b>弧</b>${MDParser.parseInline(nd.arc)}</div>` : ''}
        </div>`).join('')
      : '<div class="empty-state" style="grid-column:1/-1">没有匹配的角色</div>';
  },
};
```


```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 Characters 组件（关系图 + 角色列表 + 搜索筛选）"
```

---

### Task 12: Reader 组件 — 章节阅读标签页

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

- [ ] **Step 1: 写 Reader 组件**

```js
const Reader = {
  _rendered: false,
  currentIndex: -1,
  _fontSize: 17,
  
  onEnter() {
    if (!this._rendered) this.render();
  },
  
  render() {
    const chapters = Store.get('chapters');
    
    document.getElementById('panel-read').innerHTML = `
      <h2>阅读章节</h2>
      <p class="lede">在仪表盘内直接阅读任意章节。</p>
      <div class="reader-controls">
        <label>字号：<input type="range" id="fontSizeSlider" min="13" max="28" value="${this._fontSize}" step="1">
        <span id="fontSizeLabel">${this._fontSize}px</span></label>
      </div>
      <div class="reader">
        <nav class="toc" id="toc" role="navigation" aria-label="章节目录">
          <div class="toc-title">目录 · ${chapters.length} 章</div>
        </nav>
        <article class="article" id="article" style="font-size:${this._fontSize}px">
          <div class="empty-state">← 请从左侧目录选择一章</div>
        </article>
      </div>
      <div class="readnav">
        <button id="prevBtn" disabled>‹ 上一章</button>
        <span id="chapterProgress" class="muted"></span>
        <button id="nextBtn" disabled>下一章 ›</button>
      </div>
      <div class="read-actions">
        <button id="exportBtn">📤 导出全本 TXT</button>
        <span class="muted" style="font-size:13px;margin-left:10px;">按章节顺序合并为单一 txt 文件</span>
      </div>
      <div id="searchBar" class="search-bar" style="display:none">
        <input type="search" id="chapterSearch" placeholder="搜索当前章节...">
        <span id="searchResult" class="muted" style="font-size:13px"></span>
        <button id="searchPrev">▲</button>
        <button id="searchNext">▼</button>
        <button id="searchClose">✕</button>
      </div>
    `;
    
    this._renderToc(chapters);
    this._bindEvents(chapters);
    
    this._rendered = true;
  },
  
  _renderToc(chapters) {
    const toc = document.getElementById('toc');
    toc.innerHTML = `<div class="toc-title">目录 · ${chapters.length} 章</div>` +
      chapters.map((c, i) => `<button data-i="${i}" class="${i === this.currentIndex ? 'active' : ''}">
        <span class="ch-no">第 ${c.num || (i + 1)} 回</span>${Utils.escHtml(c.title || c.name)}
      </button>`).join('');
  },
  
  _bindEvents(chapters) {
    // 目录点击
    document.getElementById('toc').addEventListener('click', (e) => {
      const b = e.target.closest('button');
      if (b) this.openChapter(parseInt(b.dataset.i), chapters);
    });
    
    // 上一章/下一章
    document.getElementById('prevBtn').addEventListener('click', () => {
      if (this.currentIndex > 0) this.openChapter(this.currentIndex - 1, chapters);
    });
    document.getElementById('nextBtn').addEventListener('click', () => {
      if (this.currentIndex < chapters.length - 1) this.openChapter(this.currentIndex + 1, chapters);
    });
    
    // 键盘快捷键
    Utils.shortcuts.register('ArrowLeft', () => {
      if (Router.current === 'read' && this.currentIndex > 0) this.openChapter(this.currentIndex - 1, chapters);
    });
    Utils.shortcuts.register('ArrowRight', () => {
      if (Router.current === 'read' && this.currentIndex < chapters.length - 1) this.openChapter(this.currentIndex + 1, chapters);
    });
    Utils.shortcuts.register('Ctrl+f', () => {
      if (Router.current === 'read') {
        const bar = document.getElementById('searchBar');
        bar.style.display = bar.style.display === 'none' ? 'flex' : 'none';
        if (bar.style.display !== 'none') document.getElementById('chapterSearch').focus();
      }
    });
    
    // 字号调整
    document.getElementById('fontSizeSlider').addEventListener('input', (e) => {
      this._fontSize = parseInt(e.target.value);
      document.getElementById('article').style.fontSize = this._fontSize + 'px';
      document.getElementById('fontSizeLabel').textContent = this._fontSize + 'px';
    });
    
    // 导出
    document.getElementById('exportBtn').addEventListener('click', () => this._exportTxt(chapters));
    
    // 搜索
    this._bindSearch(chapters);
  },
  
  openChapter(i, chapters) {
    const ch = chapters[i];
    if (!ch) return;
    this.currentIndex = i;
    
    // 更新目录高亮
    document.querySelectorAll('#toc button').forEach((b, k) => b.classList.toggle('active', k === i));
    
    // 渲染正文
    document.getElementById('article').innerHTML = `
      <h1>${Utils.escHtml(ch.title || ('第 ' + (ch.num || (i + 1)) + ' 回'))}</h1>
      <div class="muted" style="margin-bottom:20px;font-family:var(--sans);font-size:13px;">
        共 ${Utils.fmtNum(Utils.countWords(ch.text))} 字
      </div>
      ${MDParser.parse(ch.text)}
    `;
    
    // 更新导航
    document.getElementById('prevBtn').disabled = i <= 0;
    document.getElementById('nextBtn').disabled = i >= chapters.length - 1;
    document.getElementById('chapterProgress').textContent = `第 ${i + 1} / ${chapters.length} 章`;
    
    // 滚动到顶部
    document.getElementById('article').scrollTop = 0;
    
    // 自动切换到阅读标签
    if (Router.current !== 'read') Router.switch('read');
  },
  
  _bindSearch(chapters) {
    const input = document.getElementById('chapterSearch');
    const result = document.getElementById('searchResult');
    const prevBtn = document.getElementById('searchPrev');
    const nextBtn = document.getElementById('searchNext');
    const closeBtn = document.getElementById('searchClose');
    let matches = [];
    let currentMatch = -1;
    
    input.addEventListener('input', () => {
      const ch = chapters[this.currentIndex];
      if (!ch || !input.value) { matches = []; result.textContent = ''; this._clearHighlights(); return; }
      
      const q = input.value.toLowerCase();
      const text = ch.text;
      matches = [];
      let idx = -1;
      while ((idx = text.toLowerCase().indexOf(q, idx + 1)) !== -1) {
        matches.push(idx);
      }
      currentMatch = matches.length > 0 ? 0 : -1;
      result.textContent = matches.length ? `${currentMatch + 1}/${matches.length}` : '无匹配';
      this._highlightText(text, matches, currentMatch);
    });
    
    prevBtn.addEventListener('click', () => {
      if (matches.length === 0) return;
      currentMatch = (currentMatch - 1 + matches.length) % matches.length;
      result.textContent = `${currentMatch + 1}/${matches.length}`;
      this._highlightText(chapters[this.currentIndex].text, matches, currentMatch);
      this._scrollToMatch(matches[currentMatch]);
    });
    
    nextBtn.addEventListener('click', () => {
      if (matches.length === 0) return;
      currentMatch = (currentMatch + 1) % matches.length;
      result.textContent = `${currentMatch + 1}/${matches.length}`;
      this._highlightText(chapters[this.currentIndex].text, matches, currentMatch);
      this._scrollToMatch(matches[currentMatch]);
    });
    
    closeBtn.addEventListener('click', () => {
      document.getElementById('searchBar').style.display = 'none';
      input.value = '';
      this._clearHighlights();
    });
  },
  
  _highlightText(text, matches, current) {
    // 简单实现：用 <mark> 包裹匹配文本
    // 对于大文本，用 innerHTML 替换
    const article = document.getElementById('article');
    const html = article.innerHTML;
    // 移除现有的 <mark>
    const clean = html.replace(/<mark[^>]*>/g, '').replace(/<\/mark>/g, '');
    if (matches.length === 0) { article.innerHTML = clean; return; }
    
    const q = document.getElementById('chapterSearch').value;
    const escQ = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp('(' + escQ + ')', 'gi');
    article.innerHTML = clean.replace(re, (m, i) => {
      const pos = text.indexOf(m);
      const isCurrent = pos === matches[current];
      return isCurrent ? '<mark class="current">' + m + '</mark>' : '<mark>' + m + '</mark>';
    });
  },
  
  _scrollToMatch(pos) {
    const article = document.getElementById('article');
    const marks = article.querySelectorAll('mark');
    if (marks.length > 0) {
      marks[Math.min(document.querySelectorAll('mark.current').length > 0 ? Array.from(marks).findIndex(m => m.classList.contains('current')) : 0, marks.length - 1)].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  },
  
  _clearHighlights() {
    const article = document.getElementById('article');
    article.innerHTML = article.innerHTML.replace(/<mark[^>]*>/g, '').replace(/<\/mark>/g, '');
  },
  
  _exportTxt(chapters) {
    if (!chapters.length) { alert('暂无章节可导出'); return; }
    const book = Store.get('book');
    const lines = [];
    lines.push(book.title || '未命名');
    lines.push('='.repeat(40));
    lines.push(`共 ${chapters.length} 章 / 约 ${Utils.fmtNum(chapters.reduce((s, c) => s + Utils.countWords(c.text), 0))} 字`);
    lines.push('');
    chapters.forEach((c, i) => {
      lines.push(`\n第 ${c.num || (i + 1)} 回${c.title ? ' · ' + c.title : ''}`);
      lines.push('-'.repeat(30));
      lines.push(c.text.trim());
    });
    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    // 安全处理文件名
    const safeTitle = (book.title || 'book').replace(/[\/\\:*?"<>|]/g, '_');
    a.download = `${safeTitle}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
```


```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加 Reader 组件（阅读器 + 搜索 + 快捷键 + 导出）"
```

---

### Task 13: 主入口 + 加载逻辑 + 集成

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

- [ ] **Step 1: 写 populateStore 函数 + 入口绑定 + 自动重连**

```js
// 填充 Store
const populateStore = (data) => {
  Store.set('book', data.book);
  Store.set('chapters', data.chapters);
  Store.set('roles', data.roles);
  Store.set('files', data.files);
  
  // 更新 appbar
  const book = data.book || {};
  document.getElementById('bookTitle').textContent = book.title || '未命名';
  document.getElementById('bookSub').textContent = [book.genre, book.language === 'zh' ? '中文' : book.language].filter(Boolean).join(' · ');
  document.getElementById('bookStatus').textContent = Utils.statusLabel(book.status);
};

// 入口绑定
const initApp = () => {
  // 主题初始化
  Utils.theme.init();
  document.getElementById('themeBtn').addEventListener('click', () => {
    const mode = Utils.theme.toggle();
    document.getElementById('themeBtn').textContent = mode === 'dark' ? '☀️' : mode === 'light' ? '🌙' : '🌓';
  });
  
  // 选择书架
  document.getElementById('pickBtn').addEventListener('click', pickFolder);
  document.getElementById('compatBtn').addEventListener('click', () => document.getElementById('fileInput').click());
  document.getElementById('refreshBtn').addEventListener('click', () => {
    if (lastHandle) loadBookFromHandle(lastHandle);
    else pickFolder();
  });
  document.getElementById('rePickBtn').addEventListener('click', () => {
    document.body.classList.remove('loaded');
    Store.reset();
    pickFolder();
  });
  
  // 兼容模式文件选择
  document.getElementById('fileInput').addEventListener('change', async (e) => {
    if (e.target.files.length) {
      await loadBookFromEntries(Array.from(e.target.files));
    }
  });
  
  // 注册所有组件
  Router.register('overview', Overview);
  Router.register('settings', Settings);
  Router.register('settings-content', SettingsContent);
  Router.register('chars', Characters);
  Router.register('read', Reader);
  
  // 初始化 Router
  Router.init();
};

const loadBookFromEntries = async (entries) => {
  Store.set('loading', true);
  try {
    const data = await FileReader.loadAll(null, entries);
    populateStore(data);
    document.body.classList.add('loaded');
  } catch (err) {
    Store.set('error', err.message);
    if (!autoResumed) alert('【加载失败】' + err.message);
  } finally {
    Store.set('loading', false);
  }
};

// 启动
(async () => {
  initApp();
  
  // 自动重连
  if (window.showDirectoryPicker) {
    try {
      const h = await IDB.load('last');
      if (h) {
        document.getElementById('resumeArea').style.display = 'block';
        document.getElementById('resumeName').textContent = h.name;
        document.getElementById('resumeLink').addEventListener('click', async (e) => {
          e.preventDefault();
          autoResumed = true;
          await loadBookFromHandle(h);
        });
        // 静默尝试
        await tryResumeSilent(h);
      }
    } catch {}
  }
})();
```

- [ ] **Step 2: 提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 添加主入口 + 加载逻辑 + 组件集成"
```

---

### Task 14: final — 全量测试与 Bug 修复

**Files:**
- Modify: `dragon-writer/references/dashboard.html`

- [ ] **Step 1: 浏览器打开 dashboard.html，选择 sample-book 验证**

```bash
start dragon-writer/references/dashboard.html
```

- [ ] **Step 2: 验证清单**

| 编号 | 验证项 | 预期 |
|------|--------|------|
| 1 | 落地页显示 | 标题、说明、三个按钮 |
| 2 | 选择 sample-book 文件夹 | 加载成功，进入仪表盘 |
| 3 | 总览标签 | 进度环、统计卡、当前状态、当前焦点、最近章节、审计漂移、字数趋势图 |
| 4 | 设定完成度标签 | 4 个进度条，可展开子项 |
| 5 | 设定内容标签 | 5 个设定文件原文，可折叠 |
| 6 | 人物关系标签 | 关系图渲染、节点可拖拽、角色卡片可点击 |
| 7 | 阅读章节标签 | 目录显示、点击打开章节、上一章/下一章 |
| 8 | 切换书架 | 重新选择文件夹，数据刷新 |
| 9 | 刷新按钮 | 重新读取当前书架 |
| 10 | 主题切换 | light/dark/auto 三态切换 |
| 11 | 键盘快捷键 | `Ctrl+1~5` 切换标签，`←→` 翻章 |
| 12 | 章节搜索 | `Ctrl+F` 打开搜索栏，搜索高亮 |
| 13 | 导出全本 | 下载 TXT 文件，文件名不含非法字符 |
| 14 | 角色搜索 | 输入名称过滤角色列表 |
| 15 | 字数字体 | 统计去除了 Markdown 语法 |
| 16 | 字数趋势图 | 柱状图显示，鼠标悬停显示数值 |
| 17 | 关系图性能 | 切换到其他标签后图循环停止 |
| 18 | 兼容模式 | 使用兼容按钮选择文件夹（WebKit 浏览器） |

- [ ] **Step 3: 修复测试中发现的问题，重新验证**

- [ ] **Step 4: 最终提交**

```bash
git add dragon-writer/references/dashboard.html
git commit -m "feat(dashboard): 全量测试与 Bug 修复"
```