# Dashboard Expansion Plan — from "bare MVP" to a full dashboard

## Status (2026-09-28): Phases 1-3 done, plus a few things not in this plan

All three phases below have been built and verified against a WSL test
install with **real WeatherFlow Tempest data** (no longer just the
Simulator):

- [x] **Phase 1** — sparklines + min/max on wind/pressure/humidity/rain
  tiles, color per data source (`--accent-wind`/`--accent-storm`), the Sun
  tile shows a countdown text instead of a broken-looking 0% bar before
  sunrise.
- [x] **Phase 2** — wind rose + rain calendar (last 7 days) on the
  Dashboard, reusing the existing `vane_windrose`/`vane_rain_color`.
- [x] **Phase 3** — Records teaser ("this year": highest/lowest temp,
  highest wind gust) on both Dashboard and Archive. **Deviation from the
  original text below**: "most rain in 24h" turned out to require a
  separate day-by-day aggregation that can't be done with a ready-made
  WeeWX tag — replaced with "rain this year" (`$year.rain.sum`), which can
  be done with existing tags.

**Not planned in this document, but built anyway** (as a result of ongoing
review while building, see also the code comments in `vane_extras.py`):

- **Wind vector radar** (`_wind_vector_data`) next to the wind rose —
  average speed vs. gusts per 8 main compass directions, own SVG polygon
  instead of a chart library (same principle as the wind rose). Reason: the
  wind rose shows *frequency* per direction, not *how much wind* there is
  per direction — a genuinely different question, so not a duplicate.
- **Shared footer** (`footer.inc`, Cheetah `#include` — used for the first
  time in this skin) with station info + practical links (Windy, generic
  from coordinates), now on all 5 pages instead of just the Dashboard.
- **Graphs page expanded**: Humidity, UV index and Radiation as separate
  charts (UV and Radiation deliberately not combined — too different a
  scale), plus the wind rose there too.
- Found and fixed along the way: a NOAA-modal CSS bug (`.vane-modal` had
  `display:flex` without an `[open]` guard, so the dialog was always
  visible in the page flow instead of hidden), a sensor-mapping mismatch
  between the WeatherFlow driver and the WeeWX schema
  (`lightning_strikes`/`avg_distance` didn't exist as column names — needed
  to be `lightning_strike_count`/`lightning_distance`), and a
  `color-scheme` fix so native form UI (the month picker on Graphs) follows
  the theme.

What's still **not** done from "Later, to decide separately" below: external
forecast API, gauge/dial widgets, webcam/radar — those deliberately remain
out of scope.

---

Motivation: the v1 dashboard page (`index.html.tmpl`) was built exactly to
the scope `DESIGN_PLAN.md` set for the first mockup — "hero card + stat
tiles + mini chart" — but in practice the result looks sparse and bare: on a
normal screen, >50% of the viewport is empty background, there's only one
small chart, and the color system itself (`--accent-wind`, `--accent-storm`)
isn't used on this page at all. This document researches what comparable
weather sites/WeeWX skins actually show, and turns that into a concrete,
phased plan — fitting within the architecture already laid down
(sensor-agnostic, `has_data` checks, uPlot, no framework), not a restart.

## Research: what does a full-featured PWS dashboard contain

**References**: [weewx-belchertown](https://github.com/poblabs/weewx-belchertown)
(market leader on features), [Weather34](https://github.com/Drealine/weewx-Weather34)
/ [Meteotemplate](https://www.meteotemplate.com/) (gauge-driven templates),
[weewx-wdc](https://github.com/Daveiano/weewx-wdc) (modern D3 skin), and —
most relevant, since it's already present locally as the direct predecessor
— **NeoWX Material** in `reference/neowx-material/index.html.tmpl`.

Common elements that Vane is missing or under-using:

| Element | Belchertown | Weather34/Meteotemplate | NeoWX Material (reference, local) | Vane now |
|---|---|---|---|---|
| Per-metric trend chart on the main page | ✅ (Highcharts, every observation) | ✅ (gauges + history) | ✅ — **every** tile (temp, wind, pressure, humidity, UV, rain, extra sensors) has its own chart card, directly below the values row | ❌ only the hero tile (temperature) has a sparkline |
| Wind rose visible on dashboard | ✅ | ✅ (often prominent, gauge) | ✅ (radar chart) | ❌ — already exists (`vane_windrose` in `vane_extras.py`), but only used on the Archive page |
| Min/max/average next to every value | ✅ | ✅ | ✅ (three columns: low / current / high, per tile) | ~partially — only the hero tile (temp) shows max/min, the other tiles don't |
| Trend arrow (rising/falling) per metric | ✅ | ✅ | ✅ (icon in every tile's title, not just pressure) | ~only for pressure, text instead of icon |
| Records (this year / all-time) | ✅ (separate page + teaser) | ✅ | via year/month overviews | ❌ — no teaser on dashboard, Archive page only shows the current month |
| Forecast (external, API key) | ✅ (Xweather/Pirate Weather) | ✅ (often built in) | ❌ | ❌ — deliberately not planned yet |
| Gauge/dial widgets | rarely core | ✅ **characteristic** | partly (progress-bar-like bars) | ~only the humidity tile has a bar |
| Color used consistently per data source | yes | yes, often bold | yes | ❌ — `--accent-wind`/`--accent-storm` *are* used on the Almanac page (sun arc, day-length chart), but not on the Dashboard, which uses the same blue everywhere |
| Webcam/radar embed | optional, community request (not a built-in core feature) | often yes | no | n/a — belongs in the plugin slot regardless, not in core (see `THEME_PLAN.md` "Personal integrations") |

**Research conclusion**: the problem isn't that Vane is missing a feature
that everyone else has — it's that the *density per tile* is low. Every
reference skin gives a tile three things: a value, a range (min/max or
gauge), and a history (chart or trend arrow). Vane's dashboard currently
mostly gives just the value.

## What this is not

No architecture change. Everything below fits within what's already
established:
- No new chart library — the existing own SVG sparkline technique
  (`vane_sparkline_path`, currently only for temperature) gets reused for
  other metrics; uPlot stays reserved for the Graphs page
  (interactive/zoomable), as `THEME_PLAN.md` already establishes.
- No build step, no framework, no new dependency.
- No forecast API — requires a third-party account/key and is a separate
  decision (see "Later, to decide separately" below), not part of "filling
  in the existing dashboard page better".
- No webcam/radar — that belongs in the existing plugin slot
  (`dashboard_plugins`), not in the core tiles.

## Phase 1 — Every tile gets a range + history (biggest visual gain)

This only touches `index.html.tmpl` + an extension of `vane_sparkline_path`
(or a generic variant) in `vane_extras.py`, no new sections:

1. **Mini sparkline on wind, pressure, humidity and rain** — same SVG
   technique as the hero tile, 24h window, but compact (~28px tall) at the
   bottom of the tile. Fills the currently empty space below each number and
   shows at a glance whether something is rising/falling/stable, instead of
   just a lone arrow-word for pressure.
2. **Add min/max to every tile**, not just the hero — wind, humidity and
   pressure already have this data available via `$day.<obs>.min`/`.max`
   (the same tags the hero tile already uses), this is purely a template
   extension, no new data source.
3. **Differentiate color per data source**, as `DESIGN_PLAN.md` already
   prescribes but the dashboard doesn't yet do: wind/sun → `--accent-wind`
   (already used on Almanac), rain/thunderstorm → `--accent-storm`
   (currently unused anywhere). Blue (`--accent-primary`) stays reserved
   for temperature. Costs nothing — the tokens already exist in `vane.css`.
4. **Sun tile: fix the 0% bar before sunrise** — currently an empty bar
   looks broken; replace it by only showing the bar after sunrise, or
   instead show a short "sunrise in X hours" text.

## Phase 2 — Wind rose + rain calendar onto the dashboard

Both already exist technically (`vane_windrose` in `vane_extras.py`, the
CSS-Grid rain calendar on the Archive page) but only live on Archive. A
**compact variant** (a smaller wind rose without the full label chrome, the
last 7 days of the rain calendar instead of the whole month) as an extra
card next to the existing hero+tiles row on the Dashboard. This is the main
step to fill the bottom half of the page without building a completely new
component.

## Phase 3 — Records teaser

A small "Records this year" card (highest/lowest temperature, most rain in
24h, highest wind gust) — data via `$year.<obs>.max`/`.min`, the same tag
family already used everywhere. No new page needed for v1, but a link to a
more extensive records overview on the Archive page as a later expansion of
that page (not in scope for this plan).

## Later, to decide separately (deliberately out of this plan)

- **External forecast (Xweather/Pirate Weather/Open-Meteo)** — requires a
  decision about API/key management and whether that should be
  configurable per install (same pattern as the existing
  `[Vane][[Lightning]] api_url`). Functionally valuable, but a separate
  decision with its own privacy/cost trade-off, not something to "add
  along the way" in this round.
- **Gauge/dial widgets (Weather34 style)** — visually appealing but its own
  SVG component that takes as much design work as the wind rose once did.
  Candidate for a later iteration if Phase 1+2 turn out not to be enough.
- **Webcam/radar** — belongs in the plugin slot (`dashboard_plugins`), not
  in Vane's core, per the existing "personal integrations are a separate
  plugin" rule in `THEME_PLAN.md`.

## Recommended order

Phase 1 first: lowest risk (only template + a small Python extension, no
new visual components to design), and addresses most of the "bare"
complaint (every tile becomes three times as informative). Phase 2 after
that to actually fill the bottom half of the page. Phase 3 is small and can
be done alongside Phase 2.

## Sources

- [poblabs/weewx-belchertown](https://github.com/poblabs/weewx-belchertown) — README and wiki (forecast, records, real-time streaming, wind rose)
- [poblabs/weewx-belchertown skin.conf](https://github.com/poblabs/weewx-belchertown/blob/master/skins/Belchertown/skin.conf)
- [Drealine/weewx-Weather34](https://github.com/Drealine/weewx-Weather34)
- [Daveiano/weewx-wdc](https://github.com/Daveiano/weewx-wdc) — readme.md (tile/diagram types, climatogram)
- [Meteotemplate](https://www.meteotemplate.com/) — gauges/dashboard blocks
- `reference/neowx-material/index.html.tmpl` (local) — direct predecessor, per-tile chart cards
- [Pi Stack — Self-Hosted Weather Station Software 2026](https://www.pistack.xyz/posts/2026-05-04-self-hosted-weather-station-software-weewx-meteobridge-weather34-guide/)
