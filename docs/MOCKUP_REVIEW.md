# Mockup Review — bevindingen op de Claude Design export

Bron: `design/mockup-handoff/ui-mockups-for-weewx-theme/project/WeeWX Dashboard.dc.html`
(export uit claude.ai/design, 26-09-2026). Bevindingen zijn een combinatie van
een Gemini-review op de screenshots + eigen leeswerk van de daadwerkelijke
broncode (Gemini zag alleen de plaatjes, geen code).

Status: **input voor implementatie**, nog niets hiervan is gebouwd.

## Functionele gaten (uit Gemini's review, bevestigd relevant)

- [ ] Regenaccumulaties op dashboard: alleen "vandaag" — mist deze maand
      (`$month.rain.sum`) en dit jaar (`$year.rain.sum`)
- [ ] Solar radiation / UV-grafiek ontbreekt op de Grafieken-pagina (alleen
      UV-tegel op dashboard)
- [ ] Gevoelstemperatuur niet expliciet windchill vs. heatindex
      (`$current.windchill` resp. `$current.heatindex`)
- [ ] Bliksem-tegel op dashboard (koppeling met ontladingen.nl) — nu alleen
      een tekstlink in de footer
- [ ] Windrichting over tijd (los van gemiddelde snelheid/stoten) in de
      windgrafiek
- [ ] Klimaatstatistieken in archief: aantal warme/zomerse/tropische/vorst-/
      ijsdagen per maand
- [ ] Jaar-navigatie/selector in Archief (nu alleen `< september 2026 >`,
      geen snelle jaarkeuze voor stations met 5+ jaar historie)
- [ ] Zon-/maanhoogte (azimuth) bij de almanak-boog, naast alleen tijden

## Technische nuances op Gemini's review (Gemini zag alleen screenshots)

- **Zonneschijnduur** is geen standaard WeeWX-veld. `radiation` (W/m²) is er
  wel, maar "zonneschijnuren" vereist een eigen drempelwaarde-berekening
  (vergelijkbaar met de losse `weewx-sunshine`-extensie) — dus geen kant-en-
  klare `$day.sunshine_hours.sum`.
- **Windroos**: geen ingebouwde WeeWX-tag hiervoor. Vereist zelf binnen in
  sectoren (N/NO/O/...) over `$span.wind.series`, het handigst via een kleine
  custom search-list-extension in Python (niet in pure Cheetah-loops).
- **Maanillustratie met schaduw** — dit zit al in de mockup (`alm.moonPath`,
  een SVG-path die de sikkel/schaduw tekent). Gemini's punt hierover is dus al
  gedekt, geen actie nodig.

## Eigen bevindingen uit het lezen van de broncode

1. **Windpijl niet data-gebonden** — `transform:rotate(45deg)` staat hard
   gecodeerd (regel 118 van het bronbestand), draait niet mee met de echte
   winddraaiing. Moet sowieso gefixt worden, los van of er een volledig
   kompaswidget bijkomt.
2. **Chart-implementatie is al framework-/library-loos** — de mockup gebruikt
   geen uPlot/ECharts/ApexCharts; hover/crosshair/lijnen/staven worden met
   pure SVG-paths + een handgeschreven `mkChart()`-functie getekend. **Dit is
   lichter dan het uPlot-plan in `THEME_PLAN.md`** — voorstel: dit patroon
   overnemen/uitbreiden i.p.v. alsnog een chart-library te introduceren.
3. **Stijlen zijn 100% inline** (iedere kaart herhaalt een lange
   `style="..."`-string). Prima voor een designtool-export, maar wordt bij
   implementatie omgezet naar echte CSS-classes met custom properties — niet
   1-op-1 overnemen (conform de handoff-instructies zelf).
4. **Taal-toggle is puur cosmetisch** — `state.lang` wisselt visueel, maar er
   wordt nergens een vertaalde string getoond; alle teksten staan hard in het
   Nederlands. De EN-vertaling (`lang/en.conf`) moet dus volledig zelf gebouwd
   worden, dit mockup helpt daar inhoudelijk niet bij.
5. **Geen zichtbare `:focus-visible`-states** op de `all:unset`-knoppen (nav,
   thema-toggle, periode-selector, jaartabel-rijen) — ontbrekend voor
   toetsenbordtoegankelijkheid, niet genoemd door Gemini.
6. **Geen windroos/regen-kalenderheatmap ergens in de 5 schermen** — dit is
   sterker dan "windrichting kan beter": er is nog helemaal geen widget voor.
   Sluit aan bij de openstaande designtaak in `THEME_PLAN.md`.

## Wat al goed zit (geen actie nodig)

- Kleursysteem in de mockup (`--bg`, `--surface`, `--accent-*`, ...) komt
  exact overeen met `DESIGN_PLAN.md` — geen aanpassing nodig.
- `data-props` in de mockup (`theme: auto/dark/light`, `accent: 4 presets`,
  `units: metrisch/imperiaal`) sluit aan bij het idee van "1 instelbare
  accentkleur" i.p.v. 19 losse thema's.
- Maanillustratie, live-badge, telemetrie-stijl: al conform plan.

## Openstaande technische vraag (naast bestaande punten in THEME_PLAN.md)

- [ ] Systeemlog (`journalctl -u weewx`) en proces-status (PID, uptime) op de
      Telemetrie-pagina: WeeWX genereert standaard alleen statische HTML via
      Cheetah en heeft geen root-toegang tot `journalctl`/processen. Vereist
      een klein losstaand Python-script/cronjob dat dit filtert en als JSON
      wegschrijft, of terugvallen op wat WeeWX zelf al bijhoudt
      (`$station.uptime`, extensie-states) voor een soberdere versie.

## Volgende stap

Implementatie starten met de **Dashboard**-pagina: inline-stijlen omzetten
naar CSS-classes, synthetische data vervangen door echte WeeWX Cheetah-tags,
en de bovenstaande gaten (regenaccumulaties, windpijl-binding, bliksem-tegel)
meteen meenemen i.p.v. later te patchen.
