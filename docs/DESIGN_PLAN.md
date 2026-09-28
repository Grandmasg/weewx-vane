# Design Plan — Visueel ontwerp

Basis voor het eerste Claude-artifact mockup. Afgeleid uit onderzoek van de
bestaande huisstijl ([grandmasg.nl](https://www.grandmasg.nl),
[ontladingen.nl](https://www.ontladingen.nl)) en concurrerende WeeWX-skins
(vooral [NeoWX Material](https://neoground.com/en/open-source/neowx-material),
het huidige theme).

## Merkonderzoek — wat er al bestaat

**grandmasg.nl** (computed styles, geen schatting):
- Achtergrond: `rgb(2,6,23)` — Tailwind `slate-950`
- Tekst: `rgb(148,163,184)` (slate-400, body) / `rgb(241,245,249)` (slate-100, headings)
- Accent blauw (weerstation): `rgb(47,139,255)` – `rgb(124,196,255)`
- Accent oranje (Ontladingen-blok): `rgb(251,146,60)` / `rgb(234,108,16)`
- Status-groen (live/operationeel): `rgb(74,222,128)`
- Font: **Geist**, fallback `system-ui`
- Patroon: grote kaarten met dunne semi-transparante rand, groot cijfer +
  sparkline, kleine uppercase labels met letter-spacing (`WIND`, `VOCHT`, ...)

**ontladingen.nl** (computed styles):
- Achtergrond: `rgb(15,23,42)` — Tailwind `slate-900`
- Accent paars: `rgb(124,92,255)`
- Status-groen (live-badge): `rgb(81,224,154)`
- Glasachtige panelen: witte alpha-overlays (`rgba(255,255,255,0.02–0.07)`)
- Patroon: smalle icon-sidebar, icon-grid van tegels (icoon + label), topbar met
  zoek/live-badge/taal-toggle/thema-toggle

**Gemene deler**: donkere slate-achtergrond, glasachtige kaarten met subtiele
randen, één kleur per databron, groene stip+tekst voor "live"-status, sans-serif
met uppercase micro-labels. Dit is de visuele familie waar het WeeWX-theme in
moet passen.

## Kleursysteem

Eén systeem, geen 19 losse thema's (zoals NeoWX) — wél één instelbare accentkleur
voor als het theme gedeeld wordt met andere WeeWX-gebruikers.

| Token | Dark | Light | Gebruik |
|---|---|---|---|
| `--bg` | `#020617` (slate-950) | `#f8fafc` (slate-50) | paginabasis |
| `--surface` | `#0f172a` @ 55–78% alpha | wit @ 70% alpha | kaarten (glass) |
| `--text` | `#f1f5f9` | `#0f172a` | headings |
| `--text-muted` | `#94a3b8` | `#64748b` | labels/secundair |
| `--accent-primary` | instelbaar, default `#2f8bff` | idem | huidige conditie / temperatuur |
| `--accent-wind` | `#fb923c` | idem | wind / zon / UV |
| `--accent-storm` | `#7c5cff` | idem | onweer / bliksem / neerslag |
| `--status-live` | `#4ade80` | `#16a34a` | live-indicator |

Modus: automatisch via `prefers-color-scheme`, met handmatige toggle
(`data-theme="dark|light"`) die de voorkeur onthoudt (`localStorage`).
Instelbare accentkleur via een `skin.conf`-optie die een CSS-variabele overschrijft.

**Focus-indicator** (toegankelijkheid, geen losse toevoeging maar onderdeel
van het kleursysteem — zie ook `THEME_PLAN.md`): elk interactief element
(knoppen, tabs, tabelrijen) krijgt via `:focus-visible` een 2px-ring in
`--accent-primary` met 2px offset — WCAG 2.2-conform (min. 2px dik, 3:1
contrast). Nooit `outline: none` zetten zonder vervanging.

## Iconografie: animated weather icons

**[Meteocons](https://github.com/basmilius/meteocons)** (Bas Milius, MIT) —
4000+ handgemaakte, geanimeerde SVG-weericonen in 4 stijlen (fill/flat/line/
monochrome). Animatie zit in de SVG zelf (CSS-keyframes + SVG-transforms),
géén Lottie-runtime of JS-library nodig — gebruik de plain-SVG-variant, niet
de Lottie-JSON-variant.

- **Gekozen stijl: `line`** — **correctie na daadwerkelijk downloaden**: geen
  van de stijlen gebruikt `currentColor` (line heeft eigen vaste kleuren als
  `#F8AF18` voor de zon; monochrome gebruikt `black`/`white` als twee-toon
  cutout-effect, dus niet 1-op-1 vervangbaar door `currentColor` zonder de
  laag-op-laag tekening te breken). `line`'s eigen kleurenpalet (zongeel,
  wolkgrijs, regenblauw) is bovendien beter herkenbaar dan een plat silhouet
  — bewust gekozen boven het origineel bedachte "herkleurbaar" idee.
- Zelf gehost in `static/img/icons/` (zelfde patroon als uPlot), geen CDN —
  npm-pakket `@meteocons/svg@0.1.0`, `line`-map.
- Alleen de subset gedownload die WeeWX-condities daadwerkelijk nodig hebben:
  `clear-day`, `clear-night`, `partly-cloudy-day`, `partly-cloudy-night`,
  `cloudy`, `overcast`, `fog`, `drizzle`, `rain`, `thunderstorms`, `snow`,
  `sleet`, `hail`, `sunrise`, `sunset` — niet alle 475 varianten per stijl.
- **`prefers-reduced-motion` respecteren**: animatie bevriezen op stilstaand
  beeld voor wie bewegingsgevoelig is of op een lager-vermogen toestel
  (wall-display) kijkt — sluit aan bij de focus-indicator-toegankelijkheid
  hierboven.
- **Implementatie-aandachtspunt** (zie ook `THEME_PLAN.md`): WeeWX heeft geen
  ingebouwd "conditie"-observatietype. Er komt een kleine eigen
  mapping-tabel nodig (afgeleid van `cloudcover`/`solarRadiation`/neerslag →
  welk Meteocons-icoon), dit is geen kant-en-klare WeeWX-tag.

## Typografie

- **Geist** (open source, Vercel) als primair font, `system-ui` als fallback —
  geen extra licentiekosten, sluit aan bij grandmasg.nl.
- Hoofdmeting (bv. temperatuur): groot, bold, tabular nums.
- Micro-labels (WIND, VOCHT, LUCHTDRUK): uppercase, klein, letter-spacing,
  gedempte kleur — direct overgenomen patroon van grandmasg.nl.

## Sensor-agnostisch ontwerp

Belangrijk uitgangspunt (niet alleen technisch, ook visueel): het station
wisselt (nu WeatherFlow Tempest, over een paar maanden Ecowitt WittBoy, later
weer onbekend). De stat-tegel-grid moet dus **visueel verdragen dat het
aantal tegels varieert** (5 of 9, niet altijd hetzelfde), zonder er
onevenwichtig uit te zien:

- Grid met `auto-fit`/`minmax` (zoals de mockup al doet), geen vast
  kolomaantal — voorkomt lege gaten of rare wraps bij minder tegels.
- Ontbrekende sensor (bv. geen UV bij Vantage Vue) = tegel bestaat niet,
  geen "N/A"-tegel tonen.
- **Lege/onvolledige data-staat** ontwerpen: een net aangesloten station
  heeft geen jaar-historie — archief/jaargrafiek toont een nette tekst
  ("nog onvoldoende data voor dit overzicht") i.p.v. een lege/kapotte
  grafiek. Dit hoort in het eerste mockup al meegenomen te worden, niet
  achteraf toegevoegd.

## Componenten

1. **Hero-kaart huidige conditie** — groot cijfer + icoon + sparkline (24u),
   net als de weerstation-kaart op grandmasg.nl.
2. **Stat-tegels** — grid van kleine kaarten (wind, vocht, luchtdruk, neerslag,
   UV, zon), uppercase label boven, waarde + eenheid onder.
3. **Live-badge** — groene stip + tekst + tijdstip, herbruikbaar op elke pagina
   met actuele data (patroon van beide sites).
4. **Grafiekkaart** — periode-selector (dag/week/maand/jaar/all-time) +
   uPlot/ECharts-canvas in dezelfde kaartstijl, export naar CSV/PNG.
5. **Icon-sidebar** (optioneel, geïnspireerd op ontladingen.nl) — Dashboard,
   Grafieken, Archief, Telemetrie, Almanak — compacter dan een topnav.
6. **Taal- + thema-toggle** — vaste plek rechtsboven, zoals op beide sites.
7. **Telemetrie-tegel** — batterij/signaal/voltage, aansluitend bij de
   "systeemlog"-stijl die grandmasg.nl al gebruikt voor techniek/status.

## Pagina's (mockup-volgorde)

1. **Dashboard** — hero-kaart + stat-tegels + mini-grafiek (eerste mockup)
2. **Grafieken** — volledige interactieve charts met periode-selector
3. **Archief** — dag/maand/jaar-overzichten, NOAA-achtige tabellen
4. **Telemetrie** — batterij/signaal/voltage
5. **Almanac** (optioneel) — zon/maan

## Responsive

- Mobiel: stat-tegels stapelen 2-koloms, sidebar wordt bottom-tabbar of
  hamburger — desktop: icon-sidebar links, content-grid rechts (max-width
  container, geen edge-to-edge op grote schermen).
- Full-HD wall-display variant (zoals NeoWX) is een latere iteratie, geen
  vereiste voor v1.

## Volgende stap

Eerste Claude-artifact: dashboard-pagina, licht + donker, met dummy-data,
gebouwd op bovenstaand kleursysteem en componenten.
