# Vane — WeeWX Theme

Een eigen, modern WeeWX-skin: licht/donker, meertalig, lichtgewicht client-side
grafieken, en sensor-agnostisch (werkt ongewijzigd bij een stationswissel,
bv. WeatherFlow Tempest → Ecowitt). Opvolger van
[NeoWX Material](https://neoground.com/en/open-source/neowx-material), niet als
kopie maar als lichtere, modernere eigen build.

## Status

Werkend en getest tegen een echte WeeWX-installatie met live WeatherFlow
Tempest-data (niet alleen de Simulator): Dashboard, Grafieken, Archief,
Telemetrie en Almanak staan er allemaal, inclusief windroos, windvector-radar,
regenkalender, records-teaser en meertaligheid (NL/EN). Zie
`docs/DASHBOARD_EXPANSION_PLAN.md` voor de status per onderdeel.

## Installeren

Zie **[INSTALL.md](INSTALL.md)** voor de volledige installatie-/update-instructies
(zip bouwen, verschil pip- vs. pakket-installatie, updaten).

Kort:

```bash
python build.py
weectl extension install dist/vane-<versie>.zip
sudo systemctl restart weewx
```

## Mapstructuur

- [`docs/`](docs/) — de plannen en beslissingen (zie hieronder)
- [`skins/Vane/`](skins/Vane/) — de daadwerkelijke WeeWX-skin (Cheetah-templates, CSS, JS)
- [`bin/user/vane_extras.py`](bin/user/vane_extras.py) — search-list-extension
  (sensor-detectie, windroos/windvector-berekeningen, SVG-helpers)
- [`install.py`](install.py) — WeeWX `ExtensionInstaller`
- [`build.py`](build.py) — bouwt de installeerbare zip uit `install.py`'s eigen bestandenlijst
- [`design/`](design/) — designwerk: `mockup-handoff/` (Claude Design-export),
  `chart-test/` (uPlot vs. eigen-SVG benchmark), `wsl-test-output/` (gegenereerde
  testoutput, git-ignored)
- [`reference/`](reference/) — invoermateriaal, geen onderdeel van Vane zelf
  (actief `weewx.conf` met wachtwoorden, volledige broncode van het NeoWX
  Material-theme) — zie `reference/README.md`. Gevoelige/derde-partij-bestanden
  hierin zijn **git-ignored**.

## Documentatie

- [`docs/DESIGN_PLAN.md`](docs/DESIGN_PLAN.md) — visueel ontwerp: kleuren, typografie,
  componenten, pagina's, sensor-agnostisch tegel-ontwerp.
- [`docs/THEME_PLAN.md`](docs/THEME_PLAN.md) — technisch plan: WeeWX-skinarchitectuur,
  sensor-agnostische `[[Tiles]]`-configuratie, datastrategie (uPlot), i18n, distributie.
- [`docs/DASHBOARD_EXPANSION_PLAN.md`](docs/DASHBOARD_EXPANSION_PLAN.md) —
  onderzoek naar andere WeeWX-skins/weersites, gefaseerd uitbreidingsplan en
  status van wat daarvan daadwerkelijk gebouwd is.
- [`docs/MOCKUP_REVIEW.md`](docs/MOCKUP_REVIEW.md) — bevindingen op het
  originele Claude Design-mockup.
- [`INSTALL.md`](INSTALL.md) — installatie/update.

## Referenties / concurrentie-onderzoek

| Skin | Belangrijkste eigenschap | Charting |
|---|---|---|
| [NeoWX Material](https://neoground.com/en/open-source/neowx-material) | huidige theme, 19 kleurthema's, mature | ApexCharts |
| [weewx-belchertown](https://github.com/poblabs/weewx-belchertown) | live updates via MQTT/websockets, forecast | Highcharts (licentie!) |
| [Weather34](https://github.com/Drealine/weewx-Weather34) | gauge-gedreven templates | eigen |
| [weewx-wdc](https://github.com/Daveiano/weewx-wdc) | IBM Carbon + Nivo, veel widgets | Nivo (React-stack) |
| [weewx-aganetwx](https://github.com/aganet/weewx-aganetwx) | i18n, dark mode, sensor-agnostisch | Apache ECharts |

Zie `docs/THEME_PLAN.md` en `docs/DASHBOARD_EXPANSION_PLAN.md` voor de
volledige afweging en gekozen richting.

## Vereisten

- WeeWX 5.x
- Python 3.7+ (voor de skin-generator/installer)
- Geen build-stap voor de frontend (vanilla JS, geen framework) — houdt het licht
  en makkelijk te onderhouden.

## Licentie

[MIT](LICENSE) — zelfde als de meeste referentie-skins hierboven.
