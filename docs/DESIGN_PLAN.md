# Design Plan — Visual design

Basis for the first Claude Artifact mockup. Derived from research into the
existing brand identity ([grandmasg.nl](https://www.grandmasg.nl),
[ontladingen.nl](https://www.ontladingen.nl)) and competing WeeWX skins
(especially [NeoWX Material](https://neoground.com/en/open-source/neowx-material),
the current theme).

## Brand research — what already exists

**grandmasg.nl** (computed styles, not estimated):
- Background: `rgb(2,6,23)` — Tailwind `slate-950`
- Text: `rgb(148,163,184)` (slate-400, body) / `rgb(241,245,249)` (slate-100, headings)
- Accent blue (weather station): `rgb(47,139,255)` – `rgb(124,196,255)`
- Accent orange (Ontladingen block): `rgb(251,146,60)` / `rgb(234,108,16)`
- Status green (live/operational): `rgb(74,222,128)`
- Font: **Geist**, fallback `system-ui`
- Pattern: large cards with thin semi-transparent border, big number +
  sparkline, small uppercase labels with letter-spacing (`WIND`, `HUMIDITY`, ...)

**ontladingen.nl** (computed styles):
- Background: `rgb(15,23,42)` — Tailwind `slate-900`
- Accent purple: `rgb(124,92,255)`
- Status green (live badge): `rgb(81,224,154)`
- Glass-like panels: white alpha overlays (`rgba(255,255,255,0.02–0.07)`)
- Pattern: narrow icon sidebar, icon grid of tiles (icon + label), top bar with
  search/live badge/language toggle/theme toggle

**Common denominator**: dark slate background, glass-like cards with subtle
borders, one color per data source, green dot+text for "live" status,
sans-serif with uppercase micro-labels. This is the visual family the WeeWX
theme needs to fit into.

## Color system

One system, not 19 separate themes (like NeoWX) — but one configurable accent
color for when the theme is shared with other WeeWX users.

| Token | Dark | Light | Use |
|---|---|---|---|
| `--bg` | `#020617` (slate-950) | `#f8fafc` (slate-50) | page base |
| `--surface` | `#0f172a` @ 55–78% alpha | white @ 70% alpha | cards (glass) |
| `--text` | `#f1f5f9` | `#0f172a` | headings |
| `--text-muted` | `#94a3b8` | `#64748b` | labels/secondary |
| `--accent-primary` | configurable, default `#2f8bff` | same | current condition / temperature |
| `--accent-wind` | `#fb923c` | same | wind / sun / UV |
| `--accent-storm` | `#7c5cff` | same | thunderstorm / lightning / rain |
| `--status-live` | `#4ade80` | `#16a34a` | live indicator |

Mode: automatic via `prefers-color-scheme`, with a manual toggle
(`data-theme="dark|light"`) that remembers the preference (`localStorage`).
Configurable accent color via a `skin.conf` option that overrides a CSS
variable.

**Focus indicator** (accessibility, not a separate add-on but part of the
color system — see also `THEME_PLAN.md`): every interactive element
(buttons, tabs, table rows) gets a 2px ring in `--accent-primary` with a 2px
offset via `:focus-visible` — WCAG 2.2 compliant (min. 2px thick, 3:1
contrast). Never set `outline: none` without a replacement.

## Iconography: animated weather icons

**[Meteocons](https://github.com/basmilius/meteocons)** (Bas Milius, MIT) —
4000+ handcrafted, animated SVG weather icons in 4 styles (fill/flat/line/
monochrome). Animation is embedded in the SVG itself (CSS keyframes + SVG
transforms), no Lottie runtime or JS library needed — use the plain-SVG
variant, not the Lottie-JSON variant.

- **Chosen style: `line`** — **correction after actually downloading**: none
  of the styles use `currentColor` (line has its own fixed colors like
  `#F8AF18` for the sun; monochrome uses `black`/`white` as a two-tone
  cutout effect, so it's not 1:1 replaceable by `currentColor` without
  breaking the layered drawing). `line`'s own color palette (sun yellow,
  cloud gray, rain blue) is moreover more recognizable than a flat
  silhouette — deliberately chosen over the originally proposed
  "recolorable" idea.
- Self-hosted in `static/img/icons/` (same pattern as uPlot), no CDN —
  npm package `@meteocons/svg@0.1.0`, `line` folder.
- Only the subset actually needed for WeeWX conditions was downloaded:
  `clear-day`, `clear-night`, `partly-cloudy-day`, `partly-cloudy-night`,
  `cloudy`, `overcast`, `fog`, `drizzle`, `rain`, `thunderstorms`, `snow`,
  `sleet`, `hail`, `sunrise`, `sunset` — not all 475 variants per style.
- **Respect `prefers-reduced-motion`**: freeze animation on a still frame
  for anyone motion-sensitive or on a lower-power device (wall display) —
  ties in with the focus-indicator accessibility above.
- **Implementation note** (see also `THEME_PLAN.md`): WeeWX has no built-in
  "condition" observation type. A small custom mapping table is needed
  (derived from `cloudcover`/`solarRadiation`/precipitation → which
  Meteocons icon), this isn't a ready-made WeeWX tag.

## Typography

- **Geist** (open source, Vercel) as the primary font, `system-ui` as
  fallback — no extra licensing cost, aligns with grandmasg.nl.
- Headline metric (e.g. temperature): large, bold, tabular nums.
- Micro-labels (WIND, HUMIDITY, PRESSURE): uppercase, small, letter-spacing,
  muted color — pattern taken directly from grandmasg.nl.

## Sensor-agnostic design

Important starting point (not just technical, also visual): the station
changes (currently WeatherFlow Tempest, an Ecowitt WittBoy in a few months,
something unknown again later). The stat-tile grid therefore needs to
**visually tolerate a varying number of tiles** (5 or 9, not always the
same), without looking unbalanced:

- Grid with `auto-fit`/`minmax` (as the mockup already does), no fixed
  number of columns — avoids empty gaps or odd wraps with fewer tiles.
- Missing sensor (e.g. no UV on a Vantage Vue) = tile doesn't exist, don't
  show an "N/A" tile.
- **Design an empty/incomplete-data state**: a freshly connected station has
  no year of history — the archive/year chart should show a clean message
  ("not enough data for this view yet") instead of an empty/broken chart.
  This belongs in the first mockup already, not added afterward.

## Components

1. **Current-condition hero card** — big number + icon + sparkline (24h),
   just like the weather-station card on grandmasg.nl.
2. **Stat tiles** — grid of small cards (wind, humidity, pressure, rain,
   UV, sun), uppercase label on top, value + unit below.
3. **Live badge** — green dot + text + timestamp, reusable on every page
   with current data (pattern from both sites).
4. **Chart card** — period selector (day/week/month/year/all-time) +
   uPlot/ECharts canvas in the same card style, export to CSV/PNG.
5. **Icon sidebar** (optional, inspired by ontladingen.nl) — Dashboard,
   Graphs, Archive, Telemetry, Almanac — more compact than a top nav.
6. **Language + theme toggle** — fixed spot top-right, as on both sites.
7. **Telemetry tile** — battery/signal/voltage, in line with the
   "system log" style grandmasg.nl already uses for tech/status.

## Pages (mockup order)

1. **Dashboard** — hero card + stat tiles + mini chart (first mockup)
2. **Graphs** — full interactive charts with period selector
3. **Archive** — day/month/year overviews, NOAA-like tables
4. **Telemetry** — battery/signal/voltage
5. **Almanac** (optional) — sun/moon

## Responsive

- Mobile: stat tiles stack in 2 columns, sidebar becomes a bottom tab bar or
  hamburger menu — desktop: icon sidebar on the left, content grid on the
  right (max-width container, no edge-to-edge on large screens).
- Full-HD wall-display variant (like NeoWX) is a later iteration, not a
  requirement for v1.

## Next step

First Claude Artifact: dashboard page, light + dark, with dummy data, built
on the color system and components above.
