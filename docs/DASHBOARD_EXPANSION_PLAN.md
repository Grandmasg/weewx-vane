# Dashboard Expansion Plan — van "kale MVP" naar volwaardig dashboard

## Status (2026-09-28): Fase 1-3 uitgevoerd, plus een aantal dingen die niet in dit plan stonden

Alle drie fases hieronder zijn gebouwd en geverifieerd tegen een WSL-testinstallatie
met **echte WeatherFlow Tempest-data** (niet meer alleen de Simulator):

- [x] **Fase 1** — sparklines + min/max op wind/druk/vocht/neerslag-tegels,
  kleur per databron (`--accent-wind`/`--accent-storm`), Zon-tegel toont een
  aftel-tekst i.p.v. een kapot ogende 0%-balk vóór zonsopgang.
- [x] **Fase 2** — windroos + regenkalender (laatste 7 dagen) op het
  Dashboard, hergebruik van bestaande `vane_windrose`/`vane_rain_color`.
- [x] **Fase 3** — Records-teaser ("dit jaar": hoogste/laagste temp,
  hoogste windstoot) op zowel Dashboard als Archief. **Afwijking van de
  oorspronkelijke tekst hieronder**: "meeste neerslag in 24u" bleek een
  aparte dag-voor-dag-aggregatie te vereisen die niet met een kant-en-klare
  WeeWX-tag te doen is — vervangen door "neerslag dit jaar" (`$year.rain.sum`),
  wat wel met bestaande tags kan.

**Niet in dit document gepland, wel gebouwd** (naar aanleiding van doorlopende
review tijdens het bouwen, zie ook de code-comments in `vane_extras.py`):

- **Wind-vector-radar** (`_wind_vector_data`) naast de windroos — gemiddelde
  snelheid vs. windstoten per 8 hoofdrichtingen, eigen SVG-polygoon i.p.v. een
  chart-library (zelfde principe als de windroos). Reden: de windroos toont
  *frequentie* per richting, niet *hoeveel wind* er per richting staat — een
  echt andere vraag, dus geen dubbeling.
- **Gedeelde footer** (`footer.inc`, Cheetah `#include` — voor het eerst
  gebruikt in deze skin) met stationsinfo + praktische links (Windy, generiek
  uit coördinaten), nu op alle 5 pagina's i.p.v. alleen het Dashboard.
- **Grafieken-pagina uitgebreid**: Vocht, UV-index en Straling als losse
  grafieken (UV en Straling bewust niet gecombineerd — te verschillende schaal),
  plus de windroos ook daar.
- Onderweg gevonden en gefixt: een NOAA-modal-CSS-bug (`.vane-modal` had
  `display:flex` zonder `[open]`-guard, dus de dialoog stond altijd zichtbaar
  in de paginaflow i.p.v. verborgen), een sensor-mapping-mismatch tussen de
  WeatherFlow-driver en het WeeWX-schema (`lightning_strikes`/`avg_distance`
  bestonden niet als kolomnamen — moest `lightning_strike_count`/
  `lightning_distance` zijn), en een `color-scheme`-fix zodat native
  formulier-UI (de maand-picker op Grafieken) het thema volgt.

Wat nog **niet** is gedaan uit "Later, apart te beslissen" hieronder: externe
forecast-API, gauge/dial-widgets, webcam/radar — die staan bewust nog steeds
buiten scope.

---

Aanleiding: de v1-dashboardpagina (`index.html.tmpl`) is precies gebouwd naar
de scope die `DESIGN_PLAN.md` voor de eerste mockup vastlegde — "hero-kaart +
stat-tegels + mini-grafiek" — maar in de praktijk oogt dat resultaat karig en
kaal: op een normaal scherm is >50% van de viewport lege achtergrond, er is
maar één grafiekje, en van het eigen kleursysteem (`--accent-wind`,
`--accent-storm`) wordt op deze pagina niets gebruikt. Dit document onderzoekt
wat vergelijkbare weersites/WeeWX-skins daadwerkelijk tonen, en zet dat om in
een concreet, gefaseerd plan — passend binnen de al vastgelegde architectuur
(sensor-agnostisch, `has_data`-checks, uPlot, geen framework), niet een
herstart.

## Onderzoek: wat bevat een volwaardig PWS-dashboard

**Referenties**: [weewx-belchertown](https://github.com/poblabs/weewx-belchertown)
(marktleider qua features), [Weather34](https://github.com/Drealine/weewx-Weather34)
/ [Meteotemplate](https://www.meteotemplate.com/) (gauge-gedreven templates),
[weewx-wdc](https://github.com/Daveiano/weewx-wdc) (moderne D3-skin), en —
het meest relevant, want al lokaal aanwezig als directe voorganger — **NeoWX
Material** in `reference/neowx-material/index.html.tmpl`.

Gemeenschappelijke elementen die bij Vane ontbreken of onderbenut zijn:

| Element | Belchertown | Weather34/Meteotemplate | NeoWX Material (referentie, lokaal) | Vane nu |
|---|---|---|---|---|
| Per-metric trendgrafiek op de hoofdpagina | ✅ (Highcharts, elke observatie) | ✅ (gauges + geschiedenis) | ✅ — **elke** tegel (temp, wind, druk, vocht, UV, regen, extra sensoren) heeft een eigen chart-kaart, direct onder de waarden-rij | ❌ alleen de hero-tegel (temperatuur) heeft een sparkline |
| Windroos zichtbaar op dashboard | ✅ | ✅ (vaak prominent, gauge) | ✅ (radar-chart) | ❌ — bestaat al (`vane_windrose` in `vane_extras.py`), maar alleen gebruikt op de Archief-pagina |
| Min/max/gemiddelde náást elke waarde | ✅ | ✅ | ✅ (drie kolommen: laag / huidig / hoog, per tegel) | ~gedeeltelijk — alleen de hero-tegel (temp) toont max/min, de andere tegels niet |
| Trendpijl (stijgend/dalend) per metric | ✅ | ✅ | ✅ (icoon in de titel van elke tegel, niet alleen druk) | ~alleen bij luchtdruk, tekst i.p.v. icoon |
| Records (dit jaar / all-time) | ✅ (aparte pagina + teaser) | ✅ | via jaar/maand-overzichten | ❌ — geen teaser op dashboard, Archief-pagina toont alleen huidige maand |
| Forecast (extern, API-key) | ✅ (Xweather/Pirate Weather) | ✅ (vaak ingebouwd) | ❌ | ❌ — bewust nog niet gepland |
| Gauge-/dial-widgets | zelden kern | ✅ **kenmerkend** | deels (progress-achtige balken) | ~alleen de vocht-tegel heeft een balk |
| Kleur per databron consistent gebruikt | ja | ja, vaak fel | ja | ❌ — `--accent-wind`/`--accent-storm` worden wél gebruikt op de Almanak-pagina (zon-boog, daglengte-grafiek), maar niet op het Dashboard, dat overal hetzelfde blauw gebruikt |
| Webcam/radar-embed | optioneel, community-verzoek (géén ingebouwde kern-feature) | vaak wel | nee | n.v.t. — hoort sowieso in de plugin-slot, niet in core (zie `THEME_PLAN.md` "Persoonlijke integraties") |

**Conclusie van het onderzoek**: het probleem is niet dat Vane een missende
functie heeft die alle anderen wél hebben — het is dat de *dichtheid per
tegel* laag is. Elke referentie-skin geeft een tegel drie dingen: een waarde,
een bereik (min/max of gauge), én een geschiedenis (grafiek of trendpijl).
Vane's dashboard geeft op dit moment meestal alleen de waarde.

## Wat dit niet is

Geen architectuurwijziging. Alles hieronder past binnen wat al vastligt:
- Geen nieuwe chart-library — de bestaande eigen SVG-sparkline-techniek
  (`vane_sparkline_path`, nu alleen voor temperatuur) wordt hergebruikt voor
  andere metrics; uPlot blijft gereserveerd voor de Grafieken-pagina
  (interactief/zoombaar), zoals `THEME_PLAN.md` al vastlegt.
- Geen build-stap, geen framework, geen nieuwe dependency.
- Geen forecast-API — vereist een account/key bij een derde partij en is een
  aparte beslissing (zie "Later, apart te beslissen" hieronder), geen
  onderdeel van "de bestaande dashboard-pagina beter vullen".
- Geen webcam/radar — dat hoort in de al bestaande plugin-slot
  (`dashboard_plugins`), niet in de core-tegels.

## Fase 1 — Elke tegel krijgt bereik + geschiedenis (grootste visuele winst)

Dit raakt alleen `index.html.tmpl` + een uitbreiding van
`vane_sparkline_path` (of een generieke variant) in `vane_extras.py`, geen
nieuwe secties:

1. **Mini-sparkline op wind, luchtdruk, vocht en neerslag** — zelfde
   SVG-techniek als de hero-tegel, 24u-venster, maar compact (~28px hoog)
   onderin de tegel. Vult de nu lege ruimte onder elk getal en toont in één
   oogopslag of iets aan het stijgen/dalen/stabiliseren is, i.p.v. alleen een
   los pijltje-woord bij luchtdruk.
2. **Min/max toevoegen aan élke tegel**, niet alleen de hero — wind, vocht en
   luchtdruk hebben deze data al beschikbaar via `$day.<obs>.min`/`.max`
   (dezelfde tags die de hero-tegel al gebruikt), dit is puur een
   template-uitbreiding, geen nieuwe databron.
3. **Kleur differentiëren per databron**, zoals `DESIGN_PLAN.md` al
   voorschrijft maar het dashboard nog niet doet: wind/zon → `--accent-wind`
   (al gebruikt op Almanak), neerslag/onweer → `--accent-storm` (nu nergens
   gebruikt). Blauw (`--accent-primary`) blijft gereserveerd voor
   temperatuur. Kost niets — de tokens bestaan al in `vane.css`.
4. **Zon-tegel: 0%-balk voor zonsopgang oplossen** — nu oogt een lege balk als
   kapot; vervang door de balk pas te tonen ná zonsopgang, of toon in plaats
   daarvan een korte "nog X uur tot zonsopgang"-tekst.

## Fase 2 — Windroos + regenkalender naar het dashboard

Beide bestaan al technisch (`vane_windrose` in `vane_extras.py`, de
CSS-Grid-regenkalender op de Archief-pagina) maar staan alleen op Archief.
Een **compacte variant** (kleinere windroos zonder de volledige
label-chrome, laatste 7 dagen van de regenkalender i.p.v. de hele maand) als
extra kaart naast de bestaande hero+tegels-rij op het Dashboard. Dit is de
belangrijkste stap om de onderste helft van de pagina te vullen zonder een
volledig nieuwe component te bouwen.

## Fase 3 — Records-teaser

Een kleine kaart "Records dit jaar" (hoogste/laagste temperatuur, meeste
neerslag in 24u, hoogste windstoot) — data via `$year.<obs>.max`/`.min`,
dezelfde tag-familie die al overal gebruikt wordt. Geen nieuwe pagina nodig
voor v1, wel een linkje naar een uitgebreider records-overzicht op de
Archief-pagina als latere uitbreiding van die pagina (niet in scope van dit
plan).

## Later, apart te beslissen (bewust buiten dit plan)

- **Externe forecast (Xweather/Pirate Weather/Open-Meteo)** — vereist een
  keuze over API/key-beheer en of dat per-installatie configureerbaar moet
  zijn (zelfde patroon als de al bestaande `[Vane][[Lightning]] api_url`).
  Functioneel waardevol, maar een aparte beslissing met eigen
  privacy/kosten-afweging, niet iets om "erbij te doen" in deze ronde.
- **Gauge/dial-widgets (Weather34-stijl)** — visueel aantrekkelijk maar een
  eigen SVG-component die evenveel ontwerpwerk vraagt als de windroos ooit
  kostte. Kandidaat voor een latere iteratie als Fase 1+2 niet genoeg blijken.
- **Webcam/radar** — hoort in de plugin-slot (`dashboard_plugins`), niet in
  Vane's core, conform de bestaande "persoonlijke integraties zijn een losse
  plugin"-regel in `THEME_PLAN.md`.

## Volgorde-advies

Fase 1 eerst: laagste risico (alleen template + kleine Python-uitbreiding,
geen nieuwe visuele componenten om te ontwerpen), en pakt het grootste deel
van de "kaal"-klacht aan (elke tegel wordt drie keer zo informatief). Fase 2
erna om de onderste helft van de pagina daadwerkelijk te vullen. Fase 3 is
klein en kan tegelijk met Fase 2.

## Bronnen

- [poblabs/weewx-belchertown](https://github.com/poblabs/weewx-belchertown) — README en wiki (forecast, records, real-time streaming, wind rose)
- [poblabs/weewx-belchertown skin.conf](https://github.com/poblabs/weewx-belchertown/blob/master/skins/Belchertown/skin.conf)
- [Drealine/weewx-Weather34](https://github.com/Drealine/weewx-Weather34)
- [Daveiano/weewx-wdc](https://github.com/Daveiano/weewx-wdc) — readme.md (tegel-/diagramtypes, climatogram)
- [Meteotemplate](https://www.meteotemplate.com/) — gauges/dashboard-blokken
- `reference/neowx-material/index.html.tmpl` (lokaal) — directe voorganger, per-tegel chart-kaarten
- [Pi Stack — Self-Hosted Weather Station Software 2026](https://www.pistack.xyz/posts/2026-05-04-self-hosted-weather-station-software-weewx-meteobridge-weather34-guide/)
