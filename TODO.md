# TODO

Open items tracked from development so far — not a roadmap, just things
that are known and deliberately not done yet.

## Repo language

- [ ] Most of the repo's own working language is Dutch (`docs/*.md`, code
  comments in `bin/user/vane_extras.py` and the `.tmpl` files, this file's
  earlier drafts). Now that this is a public GitHub repo, it'd be worth
  translating the docs and comments to English at some point — the
  *skin's* own `lang/nl.conf`/`lang/en.conf` (what site visitors see) is
  unaffected either way, this is purely about the project's own
  documentation/source-comment language for outside contributors.

## Deferred by design (see `docs/DASHBOARD_EXPANSION_PLAN.md`)

These were explicitly scoped out, not forgotten:

- [ ] External forecast integration (Xweather/Pirate Weather/Open-Meteo) —
  needs an API-key/cost decision, not just a template change.
- [ ] Gauge/dial-style widgets (Weather34-style) — a real design/SVG effort
  on its own, not a quick add.
- [ ] Webcam/radar embed — belongs behind the existing `dashboard_plugins`
  slot, not in core Vane.

## Smaller, genuinely open

- [ ] Rain chart on the Graphs page is a filled line chart; most reference
  skins (incl. the live NeoWX site) use a bar chart per interval instead —
  worth revisiting once there's more than a few hours of real data to judge
  it against.
- [ ] Radiation is intentionally *not* combined with UV on one chart (very
  different scales — UV would flatten to a flat line). A proper dual-axis
  chart is possible later if wanted, but `renderLineChart()` in
  `static/js/graphs.js` only supports a single shared y-axis today.
- [ ] No example file under `skins/Vane/plugins/` — the `dashboard_plugins`
  extension point exists and is documented, but there's no working sample
  `.inc` to copy from.
- [ ] Only NL/EN language files exist. Adding a third language is documented
  in `docs/THEME_PLAN.md` (copy the `[[VaneEN]]` stanza + a new
  `lang/<code>.conf`) but nobody's actually done it yet, so that path is
  unverified.
- [ ] `docs/THEME_PLAN.md` mentions a fuller Archive "records" page (not
  just the current-month view); the Dashboard/Archive "Records · this year"
  teaser exists, but there's no dedicated records page with e.g. all-time
  extremes.
- [ ] Cloud base readings from the test station look unusually low (single
  digits in meters) — plausible for foggy/low-cloud conditions, but never
  cross-checked against another source. Worth a second look once there's
  more varied weather to compare against.
- [ ] No automated tests / CI. Verification so far has been manual
  (regenerate + grep for error strings + Playwright screenshots) — fine for
  now, but there's no regression safety net for future changes.
