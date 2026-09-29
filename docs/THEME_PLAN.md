# Theme Plan — Technical architecture

Technical plan for the WeeWX skin itself. Separate from `DESIGN_PLAN.md`
(which covers appearance); this covers how it works under the hood.

## Personal integrations are a separate plugin, not part of Vane

**Vane itself always stays fully generic and publishable** — no reference at
all to grandmasg.nl, ontladingen.nl or other personal infrastructure in the
core skin. That kind of integration (e.g. an ontladingen.nl map/widget on the
dashboard) becomes a **separate, optional extension**, with its own
`install.py`, that uses a defined extension point in Vane instead of
modifying core templates:

- Vane's `[[Tiles]]` config gets an empty, generic slot:
  `dashboard_plugins = ` (comma-separated names, empty by default).
- Every name in that list gets looked up by the core template as
  `templates/plugins/<name>.inc` — if the file doesn't exist, nothing
  happens (no error).
- The published/public Vane repo therefore does contain the mechanism (the
  empty slot + documentation/example), but no actual plugin file.
- Your own `ontladingen` plugin (a separate package,
  `templates/plugins/ontladingen.inc` + `dashboard_plugins = ontladingen` in
  your own, git-ignored `weewx.conf`/`skin.conf` override) lives **outside**
  the Vane repo — same pattern as the live `weewx.conf` from `reference/`:
  the mechanism is public, the personal content isn't.
- Benefit: someone else installing Vane never sees anything of
  ontladingen.nl, but your own deployment can just turn it on without you
  having to maintain a fork of Vane.

## Basic architecture

WeeWX skins consist of:
- `skin.conf` — configuration: generators, chart definitions, texts, language
- Templates (`.tmpl`) in **Cheetah** — the only officially supported
  templating engine (Jinja2 was floated on the dev mailing list once, never
  implemented in WeeWX 5.x, so don't use it)
- `lang/xx.conf` — translation files
- Installation via `weectl extension install` (an `ExtensionInstaller` class
  sets a `[[SkinName]]` stanza in `weewx.conf`)

Sources: [WeeWX customization guide](https://weewx.com/docs/5.4/custom/introduction/),
[Cheetah generator](https://weewx.com/docs/5.2/custom/cheetah-generator/),
[Extensions](https://weewx.com/docs/5.5/custom/extensions/).

## Sensor-agnostic architecture (core principle, not an afterthought)

**Motivation**: the current station is a WeatherFlow (Tempest), an Ecowitt
WittBoy in a few months — and that may change again later. Vane must
therefore never assume a specific sensor (UV, solar, ET, rxCheckPercent,
lightning) is present. This is the starting point of the architecture, not a
later addition.

**Pattern: curated core + auto-discovered extras** (worked out after
researching how aganetwx actually solves this — GPLv3, so the pattern is
adopted, not their code):

1. **CORE set**: a fixed, Vane-designed list of core observations
   (`outTemp`, `windSpeed`, `windDir`, `windGust`, `outHumidity`, `barometer`,
   `rain`, `UV`, `radiation`, ...) gets its own curated tiles from
   `DESIGN_PLAN.md`. Every tile checks its own `$day.<obs>.has_data`
   (WeeWX's built-in check) before rendering — no data means nothing shown,
   no broken/NaN widget. This remains the neat, designed core of the
   dashboard, regardless of station type.
2. **Automatic discovery of everything else**: a small, custom WeeWX
   search-list extension (`bin/user/vane_extras.py`) inspects, on every
   report generation, which database columns (`db_manager.sqlkeys`) actually
   have a value in the latest record, filters out the CORE set, and groups
   the rest via simple pattern matching (`extraTemp*`/`soilTemp*` →
   temperature group, `pm*`/`co2*` → air quality, battery/signal fields →
   status, unknown → other). This lands in a generic **"Extra sensors"
   panel**, filled automatically — so no `skin.conf` change is needed when
   switching stations.
3. Result: the same skin works unchanged for Vantage, Tempest, Ecowitt,
   RTL_433, or whatever comes later — known metrics get nice curated tiles,
   unknown/extra sensors show up automatically in a generic panel instead of
   you having to register them.

**Known differences between stations (why this is needed)**:

- **WeatherFlow Tempest** (current station): has solar/UV, and **its own
  lightning detection** (distance + time) — a possible 2nd lightning source
  alongside ontladingen.nl, not necessarily filled in the same way.
- **Ecowitt WittBoy** (future station): often extended with extra channels
  (soil moisture, leaf wetness, extra temp/humidity sensors) via a gateway;
  reception/battery telemetry looks different from Davis' `rxCheckPercent`.
- **Davis Vantage** (what the current mockup is based on): only has UV/
  solar/ET with the right separate sensor, and `rxCheckPercent` is
  Davis-specific — doesn't exist on other brands.
- Consequence: telemetry tiles (signal/battery) need to be able to show a
  different set of fields per station type, not one fixed list.

**Pressure measurement — an explicit choice is needed**: WeeWX has 3
pressure values: `barometer` (sea-level corrected), `pressure` (raw station
pressure), `altimeter` (altitude-corrected). Vane uses **`barometer`** as the
default dashboard value (what users expect), but this is a deliberate
choice, not an accident — document it in the template comments.

**Unit system**: WeeWX normally converts **at generation time**, via
`[[Units]]` in `skin.conf` (fixed, no runtime toggle). A metric/imperial
switch in the browser (as the design mockup suggests) would require the JSON
payload to carry both units and the browser to switch client-side.
**Decision for v1**: fixed unit system via `skin.conf` (metric, like all
NL skins) — **no** runtime toggle, since that's a separate architecture
layer that isn't needed yet. Can still be added later, but deliberately.

**Empty/incomplete data**: a freshly connected station has no year of
history. Archive/year charts must show a clean empty state ("not enough
data yet") instead of a broken/empty chart.

## Data strategy: JSON + client-side charting (no server-side PNGs)

Older skins (Seasons, partly Belchertown) let WeeWX itself render PNGs via
`ImageGenerator`. All modern competitors no longer do that: `CheetahGenerator`
writes out a JSON file per period (`data/day.json`, `data/month.json`, ...),
and the browser renders the chart. Benefits: interactive zoom/hover, no
font/PNG dependencies on the server, smaller payload than a PNG.

**Decision revisited based on an actual benchmark** (`design/chart-test/`,
2026-09-26): originally the plan was "own SVG as primary, uPlot only as a
fallback for the All-time period". Measured build+render time (same
synthetic data, both implementations, browser devtools):

| Points | Own SVG (ms) | uPlot (ms) |
|---|---|---|
| 100 | 8.8 | 8.8 |
| 500 | 4.1 | 3.8 |
| 2,000 | 5.2 | 4.7 |
| 10,000 | 10.0 | 7.1 |
| 50,000 | 23.5 | 12.5 |
| 150,000 | 50.2 | 19.1 |

**uPlot wins at every scale**, even for small datasets (day/week), and gets
up to >2.5x faster for large datasets. Combined with the compatibility
advantage mentioned earlier (uPlot has already ironed out cross-browser edge
cases — old mobile Safari, embedded WebViews, wall displays — a hand-rolled
SVG implementation would have to figure all of that out itself), there's no
longer a good reason to keep the own-SVG approach as the primary choice.

**New decision: uPlot becomes the default chart library for all time-series
charts** (day/week/month/year/all), not just a fallback. ~51KB is an
acceptable, one-time dependency given the measurable gain in speed and
reliability.

Trade-off against alternatives (why not the rest):

| Library | License | Weight | Used by |
|---|---|---|---|
| ApexCharts | MIT | medium | NeoWX Material (current theme) |
| Nivo (React) | MIT, but needs a React stack | heavy | weewx-wdc |
| Highcharts | **commercial** for non-personal use | medium | weewx-belchertown |
| Apache ECharts | Apache-2.0 | medium | aganetwx, weewx-jas |
| **uPlot** | MIT | **light (~51KB)** | "Horizon" (in development) — now chosen as default |

**Wind rose and rain heatmap get no chart library** (not even uPlot) —
**confirmed through research, not just assumed**: all existing wind-rose
libraries (react-windrose-chart, react-windrose, DevExtreme, Highcharts
polar) require React and/or D3; cal-heatmap (the well-known calendar-heatmap
library) still requires D3.js as a hard dependency even in its latest
version. So there's no lightweight ready-made alternative — the own
approach below is, after research, the best option, not a compromise:

- **Wind rose**: own lightweight inline SVG component — a compass ring in
  which vanilla JS rotates an arrow (`transform: rotate(${windDir}deg)`) and
  colors sectors based on wind force. **Note**: this must actually be tied
  to `windDir` — the current design mockup still has this hardcoded to 45°,
  see `MOCKUP_REVIEW.md`.
- **Rain calendar heatmap**: simple CSS Grid (12×~31 cells) with vanilla JS
  that sets `background-color`/opacity based on rain amount per day. No
  chart library needed.

**Live updates**: start with **polling**, not MQTT/websockets (like
Belchertown) — too much extra infrastructure (a broker) for v1. WeeWX
rewrites `day.json` every archive interval (2.5–5 min); the browser does a
`fetch()` every minute, with an ETag or timestamp to avoid unnecessary
re-renders. **Keep the architecture MQTT-ready though**: decouple the
update function in JS from the data source, e.g. one
`updateDashboard(data)` function that can be fed both by the `fetch()`
poller and later by an `mqtt.on('message', ...)` callback. That way MQTT can
be added later without rebuilding the render logic.

**MQTT broker: no choice needed, the protocol is generic** (researched, not
assumed). MQTT-over-websockets is a standard; a browser client (MQTT.js)
talks to any standards-compliant broker (Mosquitto, EMQX, HiveMQ) — and the
server side too (the `weewx-mqtt` extension, publishes over the regular MQTT
port 1883) is broker-independent via host/port/user/password. **Vane
therefore doesn't need to pick a broker**, only needs to make it
configurable: `mqtt_broker_ws_url`, `mqtt_topic`, optional
`mqtt_username`/`mqtt_password` in `skin.conf`. The one practical footnote:
a broker needs a websocket listener — with Mosquitto that isn't always on
by default (requires an explicit `listener 9001` line plus
`protocol websockets` in `mosquitto.conf`) — that's an operational
instruction for the user, not a choice baked into the skin code.

**Watch out for `data/*.json.tmpl` (a Cheetah pitfall)**: Cheetah loops
easily produce a trailing comma, which makes the browser's `JSON.parse()`
fail immediately. Pattern to follow:

```
[
  #for $record in $day.records
  {"t": $record.dateTime.raw, "temp": $record.outTemp.raw}#if not $foreach.last,#end
  #end for
]
```

## Downsampling strategy (how many points per period)

Separate from the chart benchmark above (which was about how fast uPlot
*renders* points): this is about how many points the JSON generator
actually **writes out**, since that determines payload size, not just render
time. A station with years of 5-minute archive data must never send raw
records for the "All" period to the browser.

**WeeWX can already do this itself** via the `.series()` tag with
`aggregate_type`/`aggregate_interval`, no custom aggregation logic needed:

```
$month.outTemp.series(aggregate_type='max', aggregate_interval='day').json(time_series='start')
```

Add `.round(ndigits)` for a more compact JSON (fewer decimals).

**Aggregation rules per period** (to fix in `data/*.json.tmpl`):

| Period | Source | Aggregation | Approx. point count |
|---|---|---|---|
| Day | raw archive records (5 min) | none | ~288 |
| Week | raw records or hourly aggregation | `aggregate_interval=hour` | ~168–2,000 |
| Month | hourly aggregation | `aggregate_interval=hour` | ~720 |
| Year | daily aggregation | `aggregate_interval=day` | ~365 |
| All | daily or weekly aggregation, depending on timespan | `aggregate_interval=day` (or `week` for >5 years) | ~365–3,650 |

This keeps every period comfortably below the counts that already showed up
quickly in the uPlot benchmark (tens of thousands+), regardless of how many
years of history a station has — so the benchmark results become a margin,
not an assumption you need to look up for every new station.

## Dev/test workflow (WSL Ubuntu, no FTP needed while building)

Iterating on the skin doesn't need to go through the live server. WeeWX runs
entirely inside WSL Ubuntu using the built-in **`Simulator`** driver
(`weewx.drivers.simulator`, already in `weewx.conf` as an example) —
generates fake weather data without real hardware:

- **`mode = generator`**: pushes out LOOP packets as fast as possible
  (instead of waiting for the real interval) — fills a test database with
  months/years of data within minutes, ideal for testing the downsampling
  aggregations and the "All" period straight away with realistic volumes.
- **`mode = simulator`**: real-time pace, more useful for testing live
  updates/polling the way it feels in production.
- Installed via WeeWX's own apt repository (`weewx.com/apt/`) — a standalone
  WeeWX install in WSL, separate from the production install on the live
  server, so nothing there can accidentally get overwritten.
- Viewing the generated HTML: simply `python3 -m http.server` in the
  `HTML_ROOT` directory of the WSL test install, or open the file directly —
  no FTP needed until you actually deploy to production.

## `#errorCatcher Echo` is required, not a leftover debug flag (discovered in practice)

Without `#errorCatcher Echo` at the top of the template, Cheetah's
**compile-time** name resolution fails with `Reason: cannot find 'format'`
as soon as a template contains dynamic/optional constructs — in Vane's case
the `has_data` checks on observations that aren't always present
(`luminosity`, `lightning_strikes`) and the Python helper calls
(`$vane_sparkline_path()`). This is not a bug in our own code: Cheetah's
default NameMapper tries to statically verify such chains upfront and
sometimes rightly/wrongly throws errors about it, and the official error
message itself points to this directive as the fix. **Verified** (WSL test
install): with `#errorCatcher Echo` the page generates error-free — the
output was searched for embedded error text (`error`/`exception`/
`traceback`/`cannot find`), no hits. So this stays permanently in every
Vane template, not just during development.

## Front-end stack

- **No build step, no framework** — vanilla JS + CSS custom properties.
  Fits how WeeWX itself works (static generation) and saves on maintenance.
- CSS: custom properties for the color system from `DESIGN_PLAN.md`,
  `prefers-color-scheme` + manual toggle, `localStorage` for the preference.
- JS: small modules — theme toggle, language toggle, uPlot wrapper per
  chart type, JSON poller for live data.

## PWA/favicon set (minimal, current — 2026 practice)

No longer need 8+ separate PNG formats like old checklists suggest.
Concretely needed:

- **`favicon.svg`** — scales infinitely, works in all modern browsers.
  Choose a neutral base color that stands out on both light and dark
  (Safari ignores dark-mode media queries in SVG favicons).
- **`favicon.ico`** — multi-size fallback container, for older/other
  browsers that don't support SVG favicons.
- **`apple-touch-icon.png`** (180×180) — required for iOS home screen;
  without this specific tag, an added bookmark gets a generic screenshot
  instead of the logo.
- **`manifest.json`** with **192×192 and 512×512 PNG** (no SVG — Android
  requires raster images for manifest icons) + a **maskable** variant: extra
  padding around the icon so launchers can safely crop it into a circle
  (safe core zone: a circle of 409×409 within the 512 canvas).

## Accessibility: focus indicator (a design token, not optional)

From `MOCKUP_REVIEW.md`: the `all:unset` buttons in the design mockup have
no visible focus state. WCAG 2.2 (Focus Appearance, SC 2.4.13) gives
concrete minimum requirements: a focus indicator at least 2 CSS pixels
thick, with a contrast ratio of at least 3:1 against both the unfocused
component and the background. To be fixed as a CSS variable in
`DESIGN_PLAN.md`, applied via `:focus-visible` (not `:focus`, which also
shows a ring on a mouse click — not wanted):

```css
:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}
```

## Multilingual (i18n)

WeeWX has this built in, no gettext/PO needed:
- `lang/en.conf` as the base, `lang/nl.conf` etc. with a `[Texts]` section
  (key → translation)
- Language selection via `lang = nl` in `[StdReport]` in `weewx.conf`
- Source: [Localization - WeeWX 5.3](https://www.weewx.com/docs/5.3/custom/localization/)

Starting languages: **NL** (primary), **EN** (for eventual sharing/
publishing).

**Adding a language end-to-end** touches 3 places, none of them templates
(every page just loops over `$Vane.Languages` and calls
`$vane_language_name($lcode)`, see the `<select class="lang-select">` in
each `.html.tmpl`):

1. `skin.conf` `[Vane][[Languages]]` — one line, the language code mapped to
   its output subfolder (empty for the primary/root language):
   ```ini
   [[Languages]]
       nl =
       en = en
       de = de
   ```
   **This is often the only skin.conf change needed.** The `<select>`'s
   display name (native name + a decorative flag emoji, see
   DESIGN_PLAN.md/UX research: native names, not codes) comes from
   `vane_language_name()` in `bin/user/vane_extras.py`, which checks
   `skin.conf [Vane][[LanguageNames]]` first, then falls back to a
   built-in `LANGUAGE_NAMES` table covering common ISO 639-1 codes
   (de/fr/es/it/pt/pl/da/sv/no/fi/fy, alongside nl/en) — only add an entry
   to `[[LanguageNames]]` to override one of those or to name a code the
   table doesn't know at all:
   ```ini
   [[LanguageNames]]
       de = 🇩🇪 Deutsch am Bodensee   # only needed to override/add
   ```
2. `install.py` — a new `[[VaneDE]]` `StdReport` stanza (copy the
   `[[VaneEN]]` block: new `HTML_ROOT`, `lang`, and `Vane.root_href`).
3. `lang/de.conf` — the actual translations (`[Texts]` section, copied and
   translated from `lang/en.conf`), plus any locale-specific overrides
   `lang/nl.conf` shows the pattern for (`[Labels]` hemisphere letters,
   `[Units][[Ordinates]]` compass abbreviations, `[Almanac]` moon-phase
   names).

Step 1 is skin-level config (applies to every install using that
`skin.conf`); step 2 is installer-level (what `weectl extension install`
actually writes into the end user's `weewx.conf`); step 3 is the
translation content itself. All three need to agree on the same language
code.

## Dark/light + accent color

- Base: 1 system, automatic via `prefers-color-scheme`, override via a
  data attribute + localStorage (see `DESIGN_PLAN.md`)
- Configurable accent color via a `skin.conf` option (e.g.
  `accent_color = #2f8bff`) that gets written into a
  `:root { --accent-primary: ... }` rule at generation time — not 19
  separate pre-baked themes like NeoWX.

## Directory structure (verified against a real WeeWX run, WSL)

**Important, practically-discovered rule**: WeeWX's `CheetahGenerator`
mirrors a template's path 1:1 to the output location under `HTML_ROOT`
(`D/F.E.tmpl` → `HTML_ROOT/D/F.E`, literally as the official docs also say).
A `templates/` subfolder for organization seemed logical, but that means
every page ends up at `HTML_ROOT/templates/index.html` instead of
`HTML_ROOT/index.html` — so **page templates sit flat in the skin root**
(same pattern as NeoWX Material in `reference/`), a subfolder is only used
where the output URL actually should have that subfolder too (e.g. `data/`
for the JSON files, that's deliberately wanted there).

```
D:\Weewx_Theme\
  README.md
  docs\
    DESIGN_PLAN.md
    THEME_PLAN.md
  skin\                      <- the actual WeeWX skin
    skin.conf
    index.html.tmpl          <- flat in the root, not in templates\
    lang\
      en.conf
      nl.conf
    data\                    <- a subfolder is deliberate here (HTML_ROOT/data/*.json)
      day.json.tmpl
      month.json.tmpl
      year.json.tmpl
    plugins\                 <- #include-only, never as its own [[[name]]] page
    static\
      css\
      js\
        vendor\
          uPlot.iife.min.js
          uPlot.min.css
      img\
  bin\user\
    vane_extras.py            <- search-list extension
  install.py                 <- ExtensionInstaller
```

## Pages/generators (mapping to skin.conf)

| Page | Template | Generator | Data needs |
|---|---|---|---|
| Dashboard | `index.html.tmpl` | CheetahGenerator | `$current`, `$day`, + `has_data` check per tile |
| Graphs | `graphs.html.tmpl` + `data/*.json.tmpl` | CheetahGenerator | time series per period, per available observation |
| Archive | `archive.html.tmpl` | CheetahGenerator | `$month`, `$year`, NOAA texts |
| Telemetry | `telemetry.html.tmpl` | CheetahGenerator | battery/signal observations, **differs per station type** (see sensor-agnostic architecture) |

**`skin.conf` holds the CORE configuration**, not the templates. Proposal:

```ini
[Vane]
    [[Tiles]]
        dashboard = outTemp, windSpeed, windGust, outHumidity, barometer, rain, UV, radiation, luminosity
        telemetry = txBatteryStatus, consBatteryVoltage, rssi, rxCheckPercent
    [[Lightning]]
        source = ontladingen        # ontladingen | tempest | none
    [[ExtraSensors]]
        # filled automatically by bin/user/vane_extras.py — this block is
        # only for overrides (e.g. deliberately excluding a column)
        exclude =
```

Every CORE tile is checked with `has_data` before rendering — if an
observation is missing (e.g. no UV sensor), the tile simply doesn't appear.
Everything *not* in the CORE list but that does have data automatically ends
up in the "Extra sensors" panel via the search-list extension (see above).
That way the same skin works unchanged when switching from Tempest to
Ecowitt, without `skin.conf` needing to be manually updated.

## Distribution

- Packaged as a WeeWX extension (`ExtensionInstaller` in `install.py`),
  installable via `weectl extension install`.
- License: proposal MIT (in line with most reference skins).

## Open decisions

- [x] Wind rose/rain heatmap: own inline SVG + CSS Grid, no ECharts needed
- [x] Live updates v1: polling (`data/current.json.tmpl` + `static/js/
      dashboard-live.js`, every 60s), **MQTT is now also fully built**
      (not just "kept ready") — opt-in via `[Vane][[MQTT]]`, the same
      `updateDashboard(data)` function for both paths. Tested with a real
      local broker (amqtt, TCP+websocket listener) and a real Chromium
      browser (Playwright): message published over MQTT → received via
      websockets by the vendored `mqtt.min.js` → DOM actually updated, no
      console errors. Polling path confirmed separately (JSON overwritten,
      browser fetches it again). Off by default, so no impact for anyone
      not using it.
- [x] Theme name: **Vane**
- [x] License: **MIT** (see `LICENSE`)
- [x] Charting strategy: **revisited after benchmark** (`design/chart-test/`)
      — uPlot wins at every scale + is more compatible, becomes the default
      for all time-series charts (not just as a fallback). Wind rose/rain
      heatmap remain their own SVG/CSS Grid (not time-series charts).
- [x] Sensor dependency: **curated CORE tiles** (`[[Tiles]]` +
      `has_data` check) + **auto-discovered extra sensors** via a custom
      search-list extension (`bin/user/vane_extras.py`, pattern inspired by
      aganetwx, not their code — GPLv3) — no `skin.conf` change needed when
      switching stations
- [x] Unit system v1: fixed via `skin.conf` `[[Units]]`, no runtime toggle
- [x] Wind rose/rain heatmap: **research confirms** no lightweight
      ready-made library exists (everything requires React/D3) — own
      SVG/CSS Grid is the best option, not a compromise
- [x] MQTT broker: **no choice needed** — the protocol is generic
      (websockets is a standard), Vane makes it configurable
      (`mqtt_broker_ws_url`/`mqtt_topic`/credentials), no fixed broker in
      the skin code. The only operational check when introducing it: does
      the broker in use (e.g. grandmasg.nl infra) have a websocket listener
      turned on?
- [x] Scope of Tempest lightning data vs. ontladingen.nl: **revisited,
      made smarter** — `[Vane][[Lightning]] source = auto` first tries
      local archive data (any sensor that fills `lightning_strikes`, not
      necessarily Tempest), otherwise falls back to a generically
      configured `api_url` (a fixed JSON contract, no ontladingen.nl
      knowledge in core — see "Personal integrations" above). Tested: local
      path (column missing in test db → clean fallback), API path (fake
      server → tile correctly shows the fetched values).
