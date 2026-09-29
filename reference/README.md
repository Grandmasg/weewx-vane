# Reference — input material, not part of Vane

This folder contains material used *as input/comparison*, but that isn't
itself part of the Vane theme and isn't published along with it. See the
root `.gitignore` — part of this is deliberately ignored by git.

## `weewx-conf/`

- **`weewx.conf`** — the live, active `weewx.conf` of the Grandmasg station
  (WeatherFlow Tempest). Contains passwords/API keys for uploads (WOW,
  Wunderground, MQTT, etc.) — **git-ignored, never commit**. Used to verify
  which `[StdReport]`/`[Station]` settings and which observation types are
  actually available in practice.
- **`weewx.conf-5.5.0.dist`** — a clean, unmodified WeeWX 5.5.0 default
  configuration. Safe to commit; used to see what's default vs. customized
  in the live file above.

## `neowx-material/`

Full source code of the current, live theme (NeoWX Material) — 346 files,
including real Cheetah templates (`.tmpl`/`.inc`), `skin.conf`, CSS/JS.
Valuable as a **genuinely working example** of WeeWX Cheetah syntax in
practice (beyond the marketing page), but this is Neoground's code under
its own license — **git-ignored**, stays local, is not carried over 1:1
into Vane (see also the handoff instructions in
`design/mockup-handoff/.../README.md`: same principle — read for
inspiration, don't copy).
