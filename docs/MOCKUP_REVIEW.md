# Mockup Review — findings on the Claude Design export

Source: `design/mockup-handoff/ui-mockups-for-weewx-theme/project/WeeWX Dashboard.dc.html`
(export from claude.ai/design, 2026-09-26). Findings are a combination of a
Gemini review of the screenshots + own reading of the actual source code
(Gemini only saw the images, no code).

Status: **input for implementation**, none of this has been built yet.

## Functional gaps (from Gemini's review, confirmed relevant)

- [ ] Rain accumulations on dashboard: "today" only — missing this month
      (`$month.rain.sum`) and this year (`$year.rain.sum`)
- [ ] Solar radiation / UV chart missing on the Graphs page (only a UV tile
      on the dashboard)
- [ ] Feels-like temperature not explicitly windchill vs. heatindex
      (`$current.windchill` resp. `$current.heatindex`)
- [ ] Lightning tile on the dashboard (link with ontladingen.nl) — currently
      only a text link in the footer
- [ ] Wind direction over time (separate from average speed/gusts) in the
      wind chart
- [ ] Climate statistics in the archive: number of warm/summer/tropical/
      frost/ice days per month
- [ ] Year navigation/selector in Archive (currently only
      `< September 2026 >`, no quick year picker for stations with 5+ years
      of history)
- [ ] Sun/moon altitude (azimuth) alongside the almanac arc, in addition to
      just times

## Technical nuances on Gemini's review (Gemini only saw screenshots)

- **Sunshine duration** isn't a standard WeeWX field. `radiation` (W/m²) is
  available, but "sunshine hours" requires its own threshold-based
  calculation (similar to the separate `weewx-sunshine` extension) — so
  there's no ready-made `$day.sunshine_hours.sum`.
- **Wind rose**: no built-in WeeWX tag for this. Requires binning into
  sectors (N/NE/E/...) over `$span.wind.series` ourselves, most practically
  via a small custom search-list-extension in Python (not in pure Cheetah
  loops).
- **Moon illustration with shadow** — this is already in the mockup
  (`alm.moonPath`, an SVG path that draws the crescent/shadow). Gemini's
  point about this is therefore already covered, no action needed.

## Own findings from reading the source code

1. **Wind arrow not data-bound** — `transform:rotate(45deg)` is hardcoded
   (line 118 of the source file), doesn't rotate with the actual wind
   direction. Needs fixing regardless of whether a full compass widget gets
   added.
2. **Chart implementation is already framework-/library-free** — the mockup
   doesn't use uPlot/ECharts/ApexCharts; hover/crosshair/lines/bars are drawn
   with plain SVG paths + a hand-written `mkChart()` function. **This is
   lighter than the uPlot plan in `THEME_PLAN.md`** — suggestion: adopt/
   extend this pattern instead of introducing a chart library after all.
3. **Styles are 100% inline** (every card repeats a long `style="..."`
   string). Fine for a design-tool export, but gets converted to real CSS
   classes with custom properties during implementation — not carried over
   1:1 (per the handoff instructions themselves).
4. **Language toggle is purely cosmetic** — `state.lang` switches visually,
   but no translated string is shown anywhere; all text is hardcoded in
   Dutch. The EN translation (`lang/en.conf`) therefore needs to be built
   entirely from scratch, this mockup doesn't help with the content there.
5. **No visible `:focus-visible` states** on the `all:unset` buttons (nav,
   theme toggle, period selector, year-table rows) — missing for keyboard
   accessibility, not mentioned by Gemini.
6. **No wind rose/rain calendar heatmap anywhere in the 5 screens** — this is
   stronger than "wind direction could be better": there's no widget for it
   at all yet. Aligns with the open design task in `THEME_PLAN.md`.

## What's already fine (no action needed)

- The color system in the mockup (`--bg`, `--surface`, `--accent-*`, ...)
  matches `DESIGN_PLAN.md` exactly — no adjustment needed.
- `data-props` in the mockup (`theme: auto/dark/light`, `accent: 4 presets`,
  `units: metric/imperial`) aligns with the idea of "1 configurable accent
  color" instead of 19 separate themes.
- Moon illustration, live badge, telemetry style: already per plan.

## Open technical question (in addition to existing points in THEME_PLAN.md)

- [ ] System log (`journalctl -u weewx`) and process status (PID, uptime) on
      the Telemetry page: WeeWX by default only generates static HTML via
      Cheetah and has no root access to `journalctl`/processes. Requires
      either a small standalone Python script/cronjob that filters this and
      writes it out as JSON, or falling back to what WeeWX itself already
      tracks (`$station.uptime`, extension states) for a more modest version.

## Next step

Start implementation with the **Dashboard** page: convert inline styles to
CSS classes, replace synthetic data with real WeeWX Cheetah tags, and address
the gaps above (rain accumulations, wind-arrow binding, lightning tile)
immediately rather than patching them in later.
