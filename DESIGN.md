# Design System: scrAPE Tactical Dashboard

> Source of truth for the visual design language, component specs, typography, and UI guidelines for the **scrAPE** web user interface.

---

## 1. Visual Theme & Atmosphere

The design language follows **Utilitarian Brutalism**. It prioritizes extreme contrast, technical density, and unvarnished functional utility over decorative fluff.

- **Aesthetic Vibe**: Industrial, high-contrast, flat, tactical, raw.
- **Geometry**: Strictly sharp 90° corners (`border-radius: 0 !important`). Zero rounded elements across buttons, cards, tooltips, or form inputs.
- **Analog Telemetry Overlay**: Background features a subtle SVG turbulence noise filter (4% opacity overlay) to emulate high-contrast analog telemetry feeds.

---

## 2. Color Palette & Functional Roles

| Color Name | Hex Code / Variable | Functional Role |
|---|---|---|
| **Obsidian Dark** | `#0b0d0c` (`var(--bg-base)`) | Base page background, terminal body, and input fields |
| **Industrial Slate** | `#161917` (`var(--bg-surface)`) | Panel background, cards, sidebar, and tab surfaces |
| **Stealth Grey** | `#3a3f3c` (`var(--border-color)`) | Structural borders, card outlines, and dividers |
| **Acquisition Orange** | `#ff5500` (`var(--accent)`) | Primary accent, active status badges, buttons, and warnings |
| **Signal White** | `#f4f4f0` (`var(--text-primary)`) | Primary high-contrast text |
| **Muted Slate** | `#8c928e` (`var(--text-muted)`) | Secondary labels, descriptions, and `/ N total` sub-lines |
| **Alert Red** | `#ff3333` | Errors, abort buttons, and system telemetry warnings |
| **Signal Green** | `#00ff66` | Online status pulses, success indicators, and low resource load |

---

## 3. Typography Guidelines

- **Headers (`<h1>`, `<h2>`, `.logo-text`, `.stat-card .value`)**: `Oswald` (sans-serif) — Uppercase, bold, condensed to evoke high-impact military or security telemetry dashboards.
- **Body, Inputs, Buttons, Tooltips, Terminal Logs (`body`, `input`, `select`, `.btn`, `pre`)**: `JetBrains Mono` (monospaced) — High technical legibility, code integrity, and terminal authenticity.
- **Header Tracking**: `letter-spacing: 0.08em` to `0.18em` on uppercase section headers and titles.

---

## 4. Component Library Specification

### 4.1 Telemetry Stat Cards (`.stat-card`)
- **Container**: `background-color: var(--bg-surface); padding: 1.5rem; border: var(--border-heavy);`
- **Label**: `font-size: 0.75rem; color: var(--text-muted); font-weight: 700; letter-spacing: 0.1em;`
- **Value**: `font-family: 'Oswald'; font-size: 3.5rem; font-weight: 700; line-height: 1;`
- **Option C Sub-total Annotation (`.sub-total`)**: `font-size: 0.7rem; color: var(--text-muted); letter-spacing: 0.08em; margin-top: 0.3rem;`
- **Live Active Pulse (`.stat-card.running`)**: Pulsing orange border animation (`animation: pulse-border 1.5s infinite;`).

### 4.2 Tactical Sidebar & Navigation
- **Sidebar Container**: Fixed 280px left column (`width: 280px; height: 100vh; position: fixed; border-right: var(--border-heavy);`).
- **Sidebar Header**: Centered column layout featuring a glowing 72×72px vector SVG logo, `scrAPE` text (`1.6rem`), and `v0.18.0` version badge.
- **Command Center Nav Button (`.nav-item`)**:
  - `border: 1px solid var(--border-color); background-color: var(--bg-surface); gap: 0.65rem;`
  - SVG Grid Icon: 4-square cockpit dashboard vector icon on the left.
  - Active State (`.nav-item.active`): `border-color: var(--accent); color: var(--accent); background: rgba(255, 85, 0, 0.08); box-shadow: inset 0 0 10px rgba(255, 85, 0, 0.15);`
- **Subjects Vault List (`.sidebar-item`)**:
  - Left-aligned layout (`justify-content: flex-start; gap: 0.75rem;`).
  - Indicator Bullet (`.sub-indicator`): 6×6px square bullet on the left. Muted when inactive; glows bright orange (`box-shadow: 0 0 6px var(--accent)`) when active.

### 4.3 Mode Selector Bar (`.mode-selector`)
- High-contrast toggle bar at the top of the scrape parameters form (`[ CUSTOM CONFIGURATION ]` vs `[ INSTANT UNLIMITED RUN ]`).
- Selecting Unlimited Mode hides configuration fieldsets to reduce visual noise while executing un-capped runs.

### 4.4 Help Tooltips (`.tooltip-wrapper`)
- Inline `[?]` help badge trigger.
- Hovering reveals a `.tooltip-content` popup box (`background-color: var(--bg-surface); border: var(--border-heavy); box-shadow: 4px 4px 0 var(--accent); z-index: 100;`).

### 4.5 Hardware Safety Alerts (`.alert-warning`)
- Displays an alert banner (`background-color: rgba(255, 85, 0, 0.1); border: 2px solid var(--accent); color: var(--accent);`) when user input exceeds safe hardware bounds (>16 scrapers, >24 downloaders).

---

## 5. Layout Architecture

- **Left Sidebar**: Fixed 280px navigation and subject vault console.
- **Right Main Container**: `margin-left: 280px; padding: 2rem;`
- **Grid View**: Command Center uses a 2-column grid (Parameters Form on left, Live Terminal Log Feed on right).
