# Station Notes — findings from the real `weewx.conf`

Based on `reference/weewx-conf/weewx.conf` (live, WeatherFlow Tempest) and
`reference/neowx-material/skin.conf`. Goal: base Vane's `[[Tiles]]` config and
templates on what actually comes in, not on assumptions from the design
mockup (which appears to be based on Davis Vantage vocabulary).

## Clarified via the official [Tempest UDP API](https://weatherflow.github.io/Tempest/api/udp/v143/)

The `obs_st` packet contains 18 fields in a fixed order, including: wind lull,
wind avg, **wind gust**, wind direction (one, not separate for gust), station
pressure, air temp, humidity, **illuminance**, UV, solar radiation, rain/min,
precipitation type, lightning avg distance, lightning count, battery, report
interval.

1. **`luxXXX = illuminance.ST-00018664.obs_st`** — the source-data path
   (`illuminance...`) is correct and genuinely exists in `obs_st` (field
   10/18). Only the WeeWX-side name `luxXXX` is an unused placeholder —
   suggestion: rename to `luminosity` or `illuminance`.
2. **`windGust` is missing, but is available** (field 4/18). Likely line to
   add, by analogy with the existing `wind_speed`/`wind_direction` names from
   `rapid_wind`:

   ```ini
   windGust = wind_gust.ST-00018664.obs_st
   ```

   Verify the exact field path in the weewx log (`log_raw_packets = True` is
   already on) before locking it in.
3. **`windGustDir` doesn't exist separately for Tempest** — there's only one
   wind-direction field per `obs_st` report (no separate gust direction like
   Davis has). The design mockup shows this as separate; for Tempest
   stations, Vane therefore simply omits this widget instead of faking it
   with the same value as `windDir`.

## What this means for Vane's tile configuration

- **`pressure` is provided, `barometer` isn't directly** — but
  `StdWXCalculate` is set to `prefer_hardware` for `barometer`, so WeeWX
  computes it itself in software. `$current.barometer` therefore just works,
  no action needed.
- **All "feels-like temperature" derivatives already work**: `dewpoint`,
  `windchill`, `heatindex`, `appTemp`, `cloudbase`, `ET` are all set to
  `prefer_hardware` in `[StdWXCalculate]` → software fallback active. So the
  windchill/heatindex split mentioned in `MOCKUP_REVIEW.md` is simply
  possible.
- **Lightning is already captured**: `lightning_strikes` and `avg_distance`
  are mapped straight from the Tempest itself (alongside the separate
  ontladingen.nl source from `THEME_PLAN.md`). **Still to verify**: these
  aren't standard WeeWX column names from `schemas.wview_extended` — check
  whether they actually end up in `weewx.sdb`, otherwise the schema needs to
  be extended for this.
- **One battery, not two**: `outTempBatteryStatus` and `windBatteryStatus`
  both point to the same Tempest battery field (one integrated sensor unit).
  The Telemetry tiles from the mockup ("Transmitter battery" + "Console
  battery" separately) are Davis-specific — for this station that becomes one
  "Outdoor unit battery" tile.
- **No signal/reception percentage mapped** — the mockup shows "Reception
  98.4%" (Davis' `rxCheckPercent`), but there's no equivalent for this
  WeatherFlow config. The Telemetry page therefore doesn't show this tile for
  this station (confirms the sensor-agnostic approach from `THEME_PLAN.md` —
  this is exactly such a case).

## What's confirmed (no change needed)

- `unit_system = metric` and `lang = nl` are already set correctly in
  `weewx.conf`, matching `THEME_PLAN.md`'s choice of a fixed unit system.
- Database: single-station SQLite (`weewx.sdb`), schema `wview_extended`.
- The deploy path is already set up: FTPS to `weerstationlangezwaag.nl` (see
  `[[FTP]]` in `weewx.conf`) — Vane therefore doesn't need to invent a new
  deploy method, just needs to be added later as an extra/replacement
  `[[VaneReport]]` stanza in `[StdReport]` alongside (or instead of)
  `StandardReport`.
- **NeoWX Material does no sensor detection** — the `[Extras]` block in
  `skin.conf` is purely manual yes/no toggles (e.g. `show_almanac = yes`),
  no `has_data` check. Confirms that Vane's `has_data`-driven `[[Tiles]]`
  approach is a real improvement, not something already solved elsewhere.
- No `ImageGenerator` in NeoWX's `skin.conf` — confirms that the current
  theme already renders purely client-side too, no server-side PNGs. Aligns
  with Vane's own data strategy.
