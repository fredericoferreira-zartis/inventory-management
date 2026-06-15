---
description: Redesign the app UI to a modern SaaS layout with a vertical dark sidebar navigation replacing the top nav bar
---

Transform this Vue 3 application into a modern SaaS-style interface. Replace the horizontal top navigation bar with a vertical dark sidebar, apply consistent spacing and design tokens, and produce a polished professional look similar to Linear or Vercel.

---

## Phase 1 — Explore (read before planning)

Launch an **Explore** agent with search depth "thorough" to read:
- `client/src/App.vue` — full file: current layout, nav structure, global CSS (`.top-nav`, `.nav-tabs`, `.main-content`, `.stats-grid`, `.card`, badges, table styles, all global CSS variables)
- `client/src/main.js` — all routes and their component names
- `client/src/composables/useI18n.js` — confirm `t()` and `currentCurrency` API
- One view file (e.g. `client/src/views/Dashboard.vue`) — to understand the `.page-header`, `.stats-grid`, `.card` patterns inside views

Report back: exact class names used globally, current CSS custom properties, nav link labels and paths, FilterBar component location.

---

## Phase 2 — Enter Plan Mode

Call **EnterPlanMode**. In plan mode, design the full implementation. The plan must cover:

### New shell layout (`App.vue`)

Replace the entire `<div class="app">` shell with a two-column CSS grid:

```
.app-shell {
  display: grid;
  grid-template-columns: 240px 1fr;
  height: 100vh;
  overflow: hidden;
}
```

**Left column — `<aside class="sidebar">`:**
- Top: logo block (icon square + company name + subtitle)
- Middle: `<nav>` with one `<router-link>` per route, each showing an SVG icon + label
- Bottom: language switcher + profile menu (currently in top nav)

**Right column — `<div class="main-area">`:**
- `<div class="filter-strip">` — contains the existing `<FilterBar />` component (moved from between top-nav and main-content)
- `<main class="content-scroll">` — `overflow-y: auto; height: calc(100vh - filter-strip-height)` — contains `<router-view />`

The modals (`ProfileDetailsModal`, `TasksModal`) stay at the root level, unchanged.

### Sidebar design tokens

Add these CSS custom properties to the global `<style>` in App.vue:

```css
--sidebar-width: 240px;
--sidebar-bg: #0f172a;
--sidebar-text: #94a3b8;
--sidebar-text-hover: #f1f5f9;
--sidebar-active-bg: #1e293b;
--sidebar-active-text: #38bdf8;
--sidebar-border: rgba(255,255,255,0.06);
--sidebar-logo-size: 64px;
```

### Sidebar nav items

Map each route to a label (via `t()`) and an inline SVG icon (20×20 viewBox, `currentColor` stroke):

| Route | i18n key | Icon description |
|-------|----------|-----------------|
| `/` | `nav.overview` | Grid 2×2 squares |
| `/inventory` | `nav.inventory` | Box / package outline |
| `/orders` | `nav.orders` | Clipboard with lines |
| `/demand` | `nav.demandForecast` | Trending-up arrow |
| `/spending` | `nav.finance` | Bar chart ascending |
| `/restocking` | `nav.restocking` | Refresh circular arrows |
| `/reports` | `reports` (hardcoded) | Document with lines |

Nav item active state: match when `$route.path === item.path` (use `===` for `/`, `startsWith` for others to avoid false positives).

### Sidebar CSS rules

```css
.sidebar {
  background: var(--sidebar-bg);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  border-right: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}
.sidebar-logo {
  height: var(--sidebar-logo-size);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid var(--sidebar-border);
}
.sidebar-logo-mark {
  width: 32px; height: 32px;
  background: #38bdf8;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 16px; color: #0f172a;
  flex-shrink: 0;
}
.sidebar-logo-name { font-size: 13px; font-weight: 700; color: #f1f5f9; }
.sidebar-logo-sub  { font-size: 11px; color: #64748b; margin-top: 1px; }
.sidebar-nav { flex: 1; padding: 12px 8px; display: flex; flex-direction: column; gap: 2px; }
.sidebar-nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px;
  border-radius: 7px;
  text-decoration: none;
  font-size: 13.5px; font-weight: 500;
  color: var(--sidebar-text);
  transition: background 0.15s, color 0.15s;
}
.sidebar-nav-item:hover  { background: var(--sidebar-active-bg); color: var(--sidebar-text-hover); }
.sidebar-nav-item.active { background: var(--sidebar-active-bg); color: var(--sidebar-active-text); }
.sidebar-nav-item .nav-icon { width: 18px; height: 18px; flex-shrink: 0; opacity: 0.8; }
.sidebar-nav-item.active .nav-icon { opacity: 1; }
.sidebar-footer {
  padding: 12px 8px;
  border-top: 1px solid var(--sidebar-border);
  display: flex; align-items: center; justify-content: space-between;
}
```

### Main area CSS rules

```css
.main-area {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: #f8fafc;
}
.filter-strip {
  flex-shrink: 0;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 2rem;
}
.content-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem;
}
```

### Global style changes (also in App.vue global `<style>`)

- **Remove** `.top-nav`, `.nav-container`, `.nav-tabs`, and their child rules
- **Remove** `.main-content` (replaced by `.content-scroll`)
- **Keep** all card, badge, table, stats-grid, loading, error styles unchanged — they live in views/components
- **Update** `.app` → `.app-shell` (the grid wrapper)

### Responsive (optional, mention in plan)

On viewport < 768px, hide sidebar text and shrink to 56px icon-only rail. Note this as a follow-up improvement, not part of this implementation.

---

## Phase 3 — Execute (after plan approval)

Follow CLAUDE.md rules strictly:

1. **App.vue** is a `.vue` file — delegate ALL changes to the **vue-expert** subagent. Give it the complete new `App.vue` template + script + style in the prompt (do not ask it to figure out the design — specify every class, every SVG path, every CSS rule).

2. No other `.vue` files need changes — the sidebar/layout is entirely in `App.vue`. Views keep their existing `.page-header`, `.stats-grid`, `.card` patterns unchanged.

3. After vue-expert completes, use **Playwright MCP tools** to open `http://localhost:3000` and take a screenshot to verify the new layout renders correctly. Check:
   - Sidebar visible on the left with dark background
   - All nav items present and labelled correctly
   - Active route highlighted
   - FilterBar visible in the content area
   - Existing view content (cards, tables) still renders

4. If any visual issues are found, fix them via vue-expert before reporting done.
