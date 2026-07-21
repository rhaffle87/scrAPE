# Design System: scrAPE Dashboard

This document serves as the source of truth for the visual style and design language of the **scrAPE** web user interface.

## 1. Visual Theme & Atmosphere
The design follows a **Utilitarian Brutalism** aesthetic. It is high-contrast, industrial, and raw, prioritizing technical density and functionality.
- **Aesthetic Vibe**: Utilitarian, flat, raw, high-contrast, technical.
- **Geometry**: Strictly sharp, squared-off edges with zero rounded corners (`border-radius: 0 !important`).
- **Texture**: Features a subtle background noise/grain overlay (4% opacity SVG turbulence filter) to emulate high-contrast analog telemetry feeds.

## 2. Color Palette & Roles
The design uses a restricted, high-contrast palette of five colors:

| Color Name | Hex Code | Functional Role |
| :--- | :--- | :--- |
| **Obsidian Dark** | `#0b0d0c` | Primary base background for pages, forms, and terminal windows. |
| **Industrial Slate** | `#161917` | Card and component surfaces (sidebar, panels, tabs). |
| **Stealth Grey** | `#3a3f3c` | Heavy layout borders and structural dividers. |
| **Acquisition Orange** | `#ff5500` | Accent color, active status badges, buttons, and system warnings. |
| **Signal White** | `#f4f4f0` | Primary readable text color. |
| **Muted Slate** | `#8c928e` | Secondary/de-emphasized text and labels. |

## 3. Typography Rules
- **Font Families**:
  - **Headers (`<h1>`, `<h2>`, `.logo-text`)**: `Oswald` (sans-serif) — Uppercase, bold, uppercase tracking, and condensed to evoke high-impact military or security telemetry dashboards.
  - **Body, Labels, Forms, Logs (`body`, `input`, `.btn`, `pre`)**: `JetBrains Mono` (monospaced) — Explicitly chosen for high technical legibility, code integrity, and terminal authenticity.
- **Header Letter Spacing**: `0.05em` on high-level section titles.

## 4. Component Stylings

### Buttons
- **Shape**: Strictly sharp corners, square blocks.
- **Borders**: Heavy borders matching the background or context.
- **Hover/Interactive Behavior**: Flat, solid translation offset on hover:
  `transform: translate(-2px, -2px); box-shadow: 4px 4px 0 var(--text-primary);`
  On click, it returns flat: `transform: translate(0, 0); box-shadow: none;`

### Cards & Panels
- **Shape**: Squared-off corners.
- **Border**: `2px solid #3a3f3c` (Stealth Grey).
- **Background**: `background-color: #161917` (Industrial Slate).
- **Hover state**: Solid offset shadow `box-shadow: 6px 6px 0 var(--accent);` with a border accent highlight.

### Inputs & Selects
- **Shape**: Square corners.
- **Border**: `2px solid #3a3f3c` (Stealth Grey).
- **Focus state**: Thick orange highlight border (`border-color: #ff5500`) with dim orange block shadow backdrop (`box-shadow: 4px 4px 0 rgba(255, 85, 0, 0.2)`).

## 5. Layout Principles
- **Sidebar Navigation**: Fixed 280px left sidebar acting as the primary navigation console (Command Center) and directory list vault (Subjects Vault).
- **Grid Architecture**: Main section utilizes a strict 2-column layout (Dashboard parameters form on the left, live logs terminal on the right).
- **Whitespace**: Tight, highly compact paddings (`1.5rem` to `2rem`) to maximize screen efficiency and resemble command console terminal hubs.
