# Theme Plan — Technische architectuur

Technisch plan voor de WeeWX-skin zelf. Los van `DESIGN_PLAN.md` (dat gaat over
het uiterlijk); dit gaat over hoe het onder de motorkap werkt.

## Persoonlijke integraties zijn een losse plugin, geen onderdeel van Vane

**Vane zelf blijft altijd volledig generiek en publiceerbaar** — geen enkele
verwijzing naar grandmasg.nl, ontladingen.nl of andere persoonlijke
infrastructuur in de core-skin. Dat soort koppelingen (bv. een
ontladingen.nl-kaart/-widget op het dashboard) worden een **losse, optionele
extensie**, met een eigen `install.py`, die een gedefinieerd uitbreidingspunt
in Vane gebruikt in plaats van core-templates te wijzigen:

- Vane's `[[Tiles]]`-configuratie krijgt een leeg, generiek slot:
  `dashboard_plugins = ` (comma-separated namen, standaard leeg).
- Elke naam in die lijst wordt door de core-template opgezocht als
  `templates/plugins/<naam>.inc` — bestaat het bestand niet, dan gebeurt er
  simpelweg niets (geen fout).
- De published/publieke Vane-repo bevat dus wél het mechanisme (de lege
  slot + documentatie/voorbeeld), maar geen enkel concreet plugin-bestand.
- Jouw eigen `ontladingen`-plugin (los pakket,
  `templates/plugins/ontladingen.inc` + `dashboard_plugins = ontladingen` in je eigen,
  git-ignored `weewx.conf`/`skin.conf`-override) leeft **buiten** de Vane-repo
  — zelfde patroon als het actieve `weewx.conf` uit `reference/`: het
  mechanisme is publiek, de persoonlijke invulling niet.
- Voordeel: iemand anders die Vane installeert ziet nooit iets van
  ontladingen.nl, maar jouw eigen deployment kan het gewoon aanzetten zonder
  dat je een fork van Vane hoeft te onderhouden.

## Basisarchitectuur

WeeWX-skins bestaan uit:
- `skin.conf` — configuratie: generators, grafiek-definities, teksten, taal
- Templates (`.tmpl`) in **Cheetah** — de enige officieel ondersteunde
  templating-engine (Jinja2 is ooit geopperd op de dev-mailinglist, nooit
  doorgevoerd in WeeWX 5.x, dus niet gebruiken)
- `lang/xx.conf` — vertaalbestanden
- Installatie via `weectl extension install` (een `ExtensionInstaller`-klasse
  zet een `[[SkinNaam]]`-stanza in `weewx.conf`)

Bronnen: [WeeWX customization guide](https://weewx.com/docs/5.4/custom/introduction/),
[Cheetah generator](https://weewx.com/docs/5.2/custom/cheetah-generator/),
[Extensions](https://weewx.com/docs/5.5/custom/extensions/).

## Sensor-agnostische architectuur (kernprincipe, geen bijzaak)

**Aanleiding**: huidig station is een WeatherFlow (Tempest), over een paar
maanden een Ecowitt WittBoy — en dat kan later weer veranderen. Vane mag dus
nergens aannemen dat een specifieke sensor (UV, solar, ET, rxCheckPercent,
bliksem) aanwezig is. Dit is het uitgangspunt van de architectuur, niet een
latere toevoeging.

**Patroon: curated core + automatisch ontdekte extra's** (uitgewerkt na
onderzoek naar hoe aganetwx dit daadwerkelijk oplost — GPLv3, dus het
patroon overnemen, niet hun code):

1. **CORE-set**: een vaste, door Vane zelf ontworpen lijst kernobservaties
   (`outTemp`, `windSpeed`, `windDir`, `windGust`, `outHumidity`, `barometer`,
   `rain`, `UV`, `radiation`, ...) krijgt de eigen, curated tegels uit
   `DESIGN_PLAN.md`. Elke tegel checkt zelf `$day.<obs>.has_data` (WeeWX's
   ingebouwde check) voordat hij rendert — geen data betekent niets tonen,
   geen kapotte/NaN-widget. Dit blijft de nette, ontworpen kern van het
   dashboard, ongeacht stationstype.
2. **Automatische ontdekking van al het overige**: een kleine, eigen
   WeeWX search-list-extension (`bin/user/vane_extras.py`) inspecteert bij
   elke report-generatie welke databasekolommen (`db_manager.sqlkeys`) in het
   laatste record daadwerkelijk een waarde hebben, filtert de CORE-set eruit,
   en groepeert de rest via simpele patroonherkenning (`extraTemp*`/
   `soilTemp*` → temperatuurgroep, `pm*`/`co2*` → luchtkwaliteit,
   batterij/signaal-velden → status, onbekend → overig). Dit landt in een
   generiek **"Extra sensoren"-paneel**, automatisch gevuld — dus geen
   `skin.conf`-aanpassing nodig bij een stationswissel.
3. Resultaat: dezelfde skin werkt ongewijzigd voor Vantage, Tempest, Ecowitt,
   RTL_433, of wat er later bij komt — bekende metrics krijgen mooie curated
   tegels, onbekende/extra sensoren verschijnen vanzelf in een generiek paneel
   i.p.v. dat je ze moet registreren.

**Bekende verschillen tussen stations (waarom dit nodig is)**:

- **WeatherFlow Tempest** (huidig station): heeft solar/UV, én **eigen
  bliksemdetectie** (afstand + tijd) — een mogelijke 2e bliksembron náást
  ontladingen.nl, niet per se hetzelfde in te vullen.
- **Ecowitt WittBoy** (toekomstig station): vaak uitgebreid met extra
  kanalen (bodemvocht, bladvocht, extra temp/vocht-sensoren) via een gateway;
  reception/batterij-telemetrie ziet er anders uit dan Davis' `rxCheckPercent`.
- **Davis Vantage** (waar de huidige mockup op gebaseerd is): heeft UV/solar/ET
  alleen met de juiste losse sensor, en `rxCheckPercent` is Davis-specifiek —
  bestaat niet bij andere merken.
- Consequentie: telemetrie-tegels (signaal/batterij) moeten per stationstype
  een eigen set velden kunnen tonen, niet één harde lijst.

**Drukmeting — expliciete keuze nodig**: WeeWX kent 3 drukwaarden:
`barometer` (zeeniveau-gecorrigeerd), `pressure` (ruwe stationsdruk),
`altimeter` (hoogtemeter-gecorrigeerd). Vane gebruikt **`barometer`** als
standaard dashboardwaarde (wat gebruikers verwachten), maar dit is een
bewuste keuze, geen toeval — vastleggen in de template-comments.

**Eenheidsstelsel**: WeeWX rekent normaal om **bij het genereren**, via
`[[Units]]` in `skin.conf` (vast, geen runtime-toggle). Een metrisch/imperiaal
-schakelaar in de browser (zoals de designmockup suggereert) vereist dat de
JSON-payload beide eenheden meestuurt en de browser client-side omschakelt.
**Beslissing voor v1**: vast eenheidsstelsel via `skin.conf` (metrisch,
zoals alle NL-skins) — géén runtime-toggle, want dat is een aparte
architectuurlaag die nog niet nodig is. Kan later alsnog, maar dan bewust.

**Lege/onvolledige data**: een net aangesloten station heeft geen jaar-
historie. Archief/jaargrafieken moeten een nette leeg-staat tonen ("nog
onvoldoende data") in plaats van een kapotte/lege grafiek.

## Datastrategie: JSON + client-side charting (géén server-side PNG's)

Oudere skins (Seasons, deels Belchertown) laten WeeWX zelf PNG's renderen via
`ImageGenerator`. Alle moderne concurrenten doen dat niet meer: `CheetahGenerator`
schrijft per periode een JSON-bestand weg (`data/day.json`, `data/month.json`, ...),
en de browser rendert de grafiek. Voordelen: interactief zoomen/hoveren, geen
font-/PNG-afhankelijkheden op de server, kleinere payload dan een PNG.

**Besluit herzien op basis van een echte benchmark** (`design/chart-test/`,
26-09-2026): oorspronkelijk was het plan "eigen SVG primair, uPlot alleen als
fallback voor de Alles-periode". Gemeten build+render-tijd (zelfde
synthetische data, beide implementaties, browser devtools):

| Punten | Eigen SVG (ms) | uPlot (ms) |
|---|---|---|
| 100 | 8.8 | 8.8 |
| 500 | 4.1 | 3.8 |
| 2.000 | 5.2 | 4.7 |
| 10.000 | 10.0 | 7.1 |
| 50.000 | 23.5 | 12.5 |
| 150.000 | 50.2 | 19.1 |

**uPlot wint op elke schaal**, ook bij kleine datasets (dag/week), en loopt
op tot >2,5x sneller bij grote datasets. Gecombineerd met het eerder genoemde
compatibiliteitsvoordeel (uPlot heeft cross-browser-randgevallen — oude
mobiele Safari, embedded WebViews, wall-displays — al uitgekristalliseerd;
een handgeschreven SVG-implementatie moet dat allemaal zelf uitvogelen) is er
geen goede reden meer om de eigen SVG-aanpak als hoofdkeuze te houden.

**Nieuw besluit: uPlot wordt de standaard chart-library voor alle
tijdreeksgrafieken** (dag/week/maand/jaar/alles), niet alleen als fallback.
~51KB is een acceptabele, eenmalige dependency gezien de meetbare winst in
snelheid én betrouwbaarheid.

Afweging t.o.v. alternatieven (waarom niet de rest):

| Library | Licentie | Gewicht | Gebruikt door |
|---|---|---|---|
| ApexCharts | MIT | middel | NeoWX Material (huidige theme) |
| Nivo (React) | MIT, maar React-stack nodig | zwaar | weewx-wdc |
| Highcharts | **commercieel** voor niet-persoonlijk gebruik | middel | weewx-belchertown |
| Apache ECharts | Apache-2.0 | middel | aganetwx, weewx-jas |
| **uPlot** | MIT | **licht (~51KB)** | "Horizon" (in ontwikkeling) — nu gekozen als standaard |

**Windroos en regen-heatmap krijgen geen chart-library** (ook geen uPlot) —
**bevestigd via onderzoek, niet alleen aangenomen**: alle bestaande
windroos-libraries (react-windrose-chart, react-windrose, DevExtreme,
Highcharts polar) vereisen React en/of D3; cal-heatmap (dé bekende
kalender-heatmap-library) vereist zelfs in de nieuwste versie nog steeds
D3.js als harde dependency. Er bestaat dus geen lichtgewicht kant-en-klaar
alternatief — de eigen aanpak hieronder is na onderzoek de beste optie, niet
een compromis:

- **Windroos**: eigen lichtgewicht inline SVG-component — een kompasring
  waarin Vanilla JS een pijl roteert (`transform: rotate(${windDir}deg)`) en
  sectoren kleurt op basis van windkracht. **Let op**: moet echt aan
  `windDir` gekoppeld worden — het huidige designmockup heeft dit nog hard
  gecodeerd op 45°, zie `MOCKUP_REVIEW.md`.
- **Regen-kalenderheatmap**: simpel CSS Grid (12×~31 blokjes) met Vanilla JS
  die `background-color`/opacity zet op basis van neerslaghoeveelheid per dag.
  Geen chart-library nodig.

**Live-updates**: start met **polling**, niet met MQTT/websockets (zoals
Belchertown) — te veel extra infra (broker) voor v1. WeeWX herschrijft elke
archive-interval (2,5–5 min) `day.json`; de browser doet elke minuut een
`fetch()`, met ETag of timestamp om onnodige re-renders te vermijden.
**Architectuur wel MQTT-klaar houden**: de update-functie in JS ontkoppelen van
de databron, bv. één `updateDashboard(data)`-functie die zowel door de
`fetch()`-poller als later door een `mqtt.on('message', ...)`-callback gevoed
kan worden. Zo kan MQTT later toegevoegd worden zonder de renderlogica opnieuw
te bouwen.

**MQTT-broker: geen keuze nodig, protocol is generiek** (uitgezocht, niet
aangenomen). MQTT-over-websockets is een standaard; een browser-client
(MQTT.js) praat tegen élke standaardconforme broker (Mosquitto, EMQX,
HiveMQ) — en ook de serverkant (`weewx-mqtt`-extensie, publiceert via
gewone MQTT-poort 1883) is broker-onafhankelijk via host/poort/gebruiker/
wachtwoord. **Vane hoeft dus geen broker te kiezen**, alleen generiek
configureerbaar te maken: `mqtt_broker_ws_url`, `mqtt_topic`, optionele
`mqtt_username`/`mqtt_password` in `skin.conf`. De enige praktische
voetnoot: een broker moet een websocket-listener hébben — bij Mosquitto staat
die niet altijd standaard aan (vereist een expliciete `listener 9001`-regel
plus `protocol websockets` in `mosquitto.conf`) — dat is een operationele
instructie voor de gebruiker, geen keuze die in de skin-code vastligt.

**Let op bij `data/*.json.tmpl` (Cheetah-valkuil)**: Cheetah-loops genereren
makkelijk een trailing comma, wat `JSON.parse()` in de browser direct laat
breken. Patroon om aan te houden:

```
[
  #for $record in $day.records
  {"t": $record.dateTime.raw, "temp": $record.outTemp.raw}#if not $foreach.last,#end
  #end for
]
```

## Downsampling-strategie (hoeveel punten per periode)

Losstaand van de chart-benchmark (die ging over hoe snel uPlot punten
*rendert*): hier gaat het over hoeveel punten de JSON-generator daadwerkelijk
**wegschrijft**, want dat bepaalt payload-grootte, niet alleen rendertijd. Een
station met jaren aan 5-minuten-archiefdata mag nooit ruwe records voor
"Alles" naar de browser sturen.

**WeeWX kan dit al zelf** via de `.series()`-tag met `aggregate_type`/
`aggregate_interval`, geen eigen aggregatielogica nodig:

```
$month.outTemp.series(aggregate_type='max', aggregate_interval='day').json(time_series='start')
```

`.round(ndigits)` toevoegen voor compactere JSON (minder decimalen).

**Aggregatieregels per periode** (vast te leggen in `data/*.json.tmpl`):

| Periode | Bron | Aggregatie | Circa aantal punten |
|---|---|---|---|
| Dag | ruwe archiefrecords (5 min) | geen | ~288 |
| Week | ruwe records óf uur-aggregatie | `aggregate_interval=hour` | ~168–2000 |
| Maand | uur-aggregatie | `aggregate_interval=hour` | ~720 |
| Jaar | dag-aggregatie | `aggregate_interval=day` | ~365 |
| Alles | dag- of week-aggregatie, afhankelijk van tijdspanne | `aggregate_interval=day` (of `week` bij >5 jaar) | ~365–3650 |

Zo blijft élke periode ruim onder de aantallen die in de uPlot-benchmark al
snel bleken (tienduizenden+), ongeacht hoeveel jaar historie een station
heeft — de benchmark-resultaten worden dus een marge, niet een aanname die
je moet opzoeken bij elk nieuw station.

## Dev/test-workflow (WSL Ubuntu, geen FTP nodig tijdens bouwen)

Itereren op de skin hoeft niet via de live server. WeeWX draait volledig
binnen WSL Ubuntu met de ingebouwde **`Simulator`**-driver (`weewx.drivers.
simulator`, staat al als voorbeeld in `weewx.conf`) — genereert nepweerdata
zonder echte hardware:

- **`mode = generator`**: stoot LOOP-pakketten zo snel mogelijk uit (i.p.v.
  te wachten op het echte interval) — vult een testdatabase met maanden/jaren
  aan data binnen minuten, ideaal om de downsampling-aggregaties en
  "Alles"-periode meteen met realistische volumes te testen.
- **`mode = simulator`**: realtime tempo, handiger om live-updates/polling
  te testen zoals het in productie aanvoelt.
- Installatie via WeeWX's eigen apt-repository (`weewx.com/apt/`) — een
  losstaande WeeWX-installatie in WSL, los van de productie-installatie op
  de live server, dus niets kan daar per ongeluk overschrijven.
- Gegenereerde HTML bekijken: simpelweg `python3 -m http.server` in de
  `HTML_ROOT`-map van de WSL-testinstallatie, of direct het bestand openen —
  geen FTP nodig totdat je daadwerkelijk naar productie deployt.

## `#errorCatcher Echo` is verplicht, geen debug-restant (in de praktijk ontdekt)

Zonder `#errorCatcher Echo` bovenaan het template faalt Cheetah's
**compile-time** naamresolutie met `Reason: cannot find 'format'` zodra een
template dynamische/optionele constructies bevat — in Vane's geval de
`has_data`-checks op niet-overal-aanwezige observaties (`luminosity`,
`lightning_strikes`) en de Python-helperaanroepen (`$vane_sparkline_path()`).
Dit is geen bug in onze code: Cheetah's standaard NameMapper probeert zulke
ketens vooraf statisch te verifiëren en geeft daar soms terecht/onterecht
foutmeldingen op, en de officiële foutmelding zelf verwijst naar deze
directive als oplossing. **Geverifieerd** (WSL-testinstallatie): met
`#errorCatcher Echo` genereert de pagina foutloos — de output is doorzocht op
ingebedde foutteksten (`error`/`exception`/`traceback`/`cannot find`), geen
treffers. Blijft dus permanent in élk Vane-template, niet alleen tijdens
ontwikkelen.

## Front-end stack

- **Geen build-stap, geen framework** — vanilla JS + CSS custom properties.
  Past bij hoe WeeWX zelf werkt (static generatie) en scheelt onderhoud.
- CSS: custom properties voor het kleursysteem uit `DESIGN_PLAN.md`,
  `prefers-color-scheme` + handmatige toggle, `localStorage` voor voorkeur.
- JS: kleine modules — theme-toggle, taal-toggle, uPlot-wrapper per
  grafiektype, JSON-poller voor live-data.

## PWA/favicon-set (minimale, actuele set — 2026-praktijk)

Geen 8+ losse PNG-formaten meer nodig zoals oude checklists suggereren.
Concreet benodigd:

- **`favicon.svg`** — schaalt oneindig, werkt in alle moderne browsers.
  Kies een neutrale basiskleur die op zowel licht als donker afsteekt
  (Safari negeert dark-mode media queries in SVG-favicons).
- **`favicon.ico`** — multi-size fallback-container, voor oudere/overige
  browsers die geen SVG-favicon ondersteunen.
- **`apple-touch-icon.png`** (180×180) — vereist voor iOS-homescreen;
  zonder deze specifieke tag krijgt een toegevoegde bookmark een generieke
  schermafbeelding i.p.v. het logo.
- **`manifest.json`** met **192×192 en 512×512 PNG** (geen SVG — Android
  vereist raster-afbeeldingen voor manifest-iconen) + een **maskable**
  variant: extra padding rond het icoon zodat launchers 'm veilig cirkelvormig
  kunnen bijsnijden (veilige kernzone: cirkel van 409×409 binnen het 512-canvas).

## Toegankelijkheid: focus-indicator (design-token, niet optioneel)

Uit `MOCKUP_REVIEW.md`: de `all:unset`-knoppen in het designmockup hebben
geen zichtbare focus-state. WCAG 2.2 (Focus Appearance, SC 2.4.13) geeft
concrete minimumeisen: een focus-indicator van minstens 2 CSS-pixels dik,
met een contrastverhouding van minstens 3:1 t.o.v. zowel de niet-gefocuste
component als de achtergrond. Vast te leggen als CSS-variabele in
`DESIGN_PLAN.md`, toegepast via `:focus-visible` (niet `:focus`, dat toont
ook een ring bij een muisklik — niet gewenst):

```css
:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}
```

## Meertaligheid (i18n)

WeeWX heeft dit ingebouwd, geen gettext/PO nodig:
- `lang/en.conf` als basis, `lang/nl.conf` etc. met een `[Texts]`-sectie
  (key → vertaling)
- Taalkeuze via `lang = nl` in `[StdReport]` in `weewx.conf`
- Bron: [Localization - WeeWX 5.3](https://www.weewx.com/docs/5.3/custom/localization/)

Starttalen: **NL** (primair), **EN** (voor eventueel delen/publiceren).

## Dark/light + accentkleur

- Basis: 1 systeem, automatisch via `prefers-color-scheme`, override via
  data-attribute + localStorage (zie `DESIGN_PLAN.md`)
- Instelbare accentkleur via een `skin.conf`-optie (bv. `accent_color = #2f8bff`)
  die bij het genereren in een `:root { --accent-primary: ... }`-regel wordt
  geschreven — géén 19 losse vooraf gebakken thema's zoals NeoWX.

## Mapstructuur (geverifieerd tegen een echte WeeWX-run, WSL)

**Belangrijke, in de praktijk ontdekte regel**: WeeWX's `CheetahGenerator`
spiegelt het pad van een template 1-op-1 naar de output-locatie onder
`HTML_ROOT` (`D/F.E.tmpl` → `HTML_ROOT/D/F.E`, letterlijk zoals de officiële
docs het ook zeggen). Een `templates/`-submap voor overzicht leek logisch,
maar zorgt er zo voor dat elke pagina op `HTML_ROOT/templates/index.html`
uitkomt i.p.v. `HTML_ROOT/index.html` — dus **pagina-templates staan plat in
de skin-root** (zelfde patroon als NeoWX Material in `reference/`), een
submap wordt alleen gebruikt waar de output-URL die submap ook echt hoort te
hebben (bv. `data/` voor de JSON-bestanden, dat is bewust wel gewenst).

```
D:\Weewx_Theme\
  README.md
  docs\
    DESIGN_PLAN.md
    THEME_PLAN.md
  skin\                      <- de daadwerkelijke WeeWX-skin
    skin.conf
    index.html.tmpl          <- plat in de root, niet in templates\
    lang\
      en.conf
      nl.conf
    data\                    <- submap is hier wel bewust (HTML_ROOT/data/*.json)
      day.json.tmpl
      month.json.tmpl
      year.json.tmpl
    plugins\                 <- #include-only, nooit als eigen [[[naam]]] pagina
    static\
      css\
      js\
        vendor\
          uPlot.iife.min.js
          uPlot.min.css
      img\
  bin\user\
    vane_extras.py            <- search-list-extension
  install.py                 <- ExtensionInstaller
```

## Pagina's/generators (koppeling met skin.conf)

| Pagina | Template | Generator | Databehoefte |
|---|---|---|---|
| Dashboard | `index.html.tmpl` | CheetahGenerator | `$current`, `$day`, + `has_data`-check per tile |
| Grafieken | `graphs.html.tmpl` + `data/*.json.tmpl` | CheetahGenerator | tijdreeksen per periode, per beschikbare observatie |
| Archief | `archive.html.tmpl` | CheetahGenerator | `$month`, `$year`, NOAA-teksten |
| Telemetrie | `telemetry.html.tmpl` | CheetahGenerator | batterij/signaal-observaties, **per stationstype anders** (zie sensor-agnostische architectuur) |

**`skin.conf` bevat de CORE-configuratie**, niet de templates. Voorstel:

```ini
[Vane]
    [[Tiles]]
        dashboard = outTemp, windSpeed, windGust, outHumidity, barometer, rain, UV, radiation, luminosity
        telemetry = txBatteryStatus, consBatteryVoltage, rssi, rxCheckPercent
    [[Lightning]]
        source = ontladingen        # ontladingen | tempest | none
    [[ExtraSensors]]
        # automatisch gevuld door bin/user/vane_extras.py — dit blok is alleen
        # voor overrides (bv. een kolom bewust uitsluiten)
        exclude =
```

Elke CORE-tile wordt getoetst met `has_data` voordat hij rendert — ontbreekt
een observatie (bv. geen UV-sensor), dan verschijnt de tile simpelweg niet.
Alles wat *niet* in de CORE-lijst staat maar wel data heeft, komt automatisch
in het "Extra sensoren"-paneel via de search-list-extension (zie hierboven).
Zo werkt dezelfde skin ongewijzigd bij een overstap van Tempest naar Ecowitt,
zonder dat `skin.conf` handmatig bijgewerkt hoeft te worden.

## Distributie

- Verpakken als WeeWX-extensie (`ExtensionInstaller` in `install.py`),
  installeerbaar via `weectl extension install`.
- Licentie: voorstel MIT (aansluitend bij de meeste referentie-skins).

## Openstaande beslissingen

- [x] Windroos/regen-heatmap: eigen inline SVG + CSS Grid, geen ECharts nodig
- [x] Live-updates v1: polling (`data/current.json.tmpl` + `static/js/
      dashboard-live.js`, elke 60s), **MQTT nu ook volledig gebouwd**
      (niet alleen "klaar gehouden") — opt-in via `[Vane][[MQTT]]`,
      zelfde `updateDashboard(data)`-functie voor beide paden. Getest
      met een echte lokale broker (amqtt, TCP+websocket-listener) en een
      echte Chromium-browser (Playwright): bericht gepubliceerd over
      MQTT → via websockets ontvangen door de gevendorde `mqtt.min.js`
      → DOM daadwerkelijk bijgewerkt, geen console-errors. Polling-pad
      apart bevestigd (JSON overschreven, browser haalt 'm opnieuw op).
      Uit-by-default, dus geen impact voor wie het niet gebruikt.
- [x] Naam van het theme: **Vane**
- [x] Licentie: **MIT** (zie `LICENSE`)
- [x] Charting-strategie: **herzien na benchmark** (`design/chart-test/`) —
      uPlot wint op elke schaal + is compatibeler, wordt standaard voor alle
      tijdreeksgrafieken (niet alleen als fallback). Windroos/regen-heatmap
      blijven wel eigen SVG/CSS Grid (geen tijdreeks-charts).
- [x] Sensor-afhankelijkheid: **curated CORE-tiles** (`[[Tiles]]` +
      `has_data`-check) + **automatisch ontdekte extra sensoren** via een
      eigen search-list-extension (`bin/user/vane_extras.py`, patroon
      geïnspireerd op aganetwx, niet hun code — GPLv3) — geen `skin.conf`-
      aanpassing nodig bij stationswissel
- [x] Eenheidsstelsel v1: vast via `skin.conf` `[[Units]]`, geen runtime-toggle
- [x] Windroos/regen-heatmap: **onderzoek bevestigt** geen lichtgewicht
      kant-en-klare library bestaat (alles vereist React/D3) — eigen
      SVG/CSS Grid is de beste optie, niet een compromis
- [x] MQTT-broker: **geen keuze nodig** — protocol is generiek
      (websockets-standaard), Vane maakt het configureerbaar
      (`mqtt_broker_ws_url`/`mqtt_topic`/credentials), geen vaste broker in
      de skin-code. Enige operationele check bij invoering: heeft de
      gebruikte broker (bv. grandmasg.nl-infra) een websocket-listener aan?
- [x] Scope Tempest-bliksemdata vs. ontladingen.nl: **herzien, slimmer
      gemaakt** — `[Vane][[Lightning]] source = auto` probeert eerst
      lokale archiefdata (elke sensor die `lightning_strikes` vult, niet
      per se Tempest), valt anders terug op een generiek geconfigureerde
      `api_url` (vast JSON-contract, geen ontladingen.nl-kennis in de
      core — zie "Persoonlijke integraties" hierboven). Getest: lokaal
      pad (kolom ontbreekt in test-db → nette fallback), API-pad (nep-
      server → tegel toont de opgehaalde waarden correct).
