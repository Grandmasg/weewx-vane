# Station Notes — bevindingen uit het echte `weewx.conf`

Gebaseerd op `reference/weewx-conf/weewx.conf` (actief, WeatherFlow Tempest) en
`reference/neowx-material/skin.conf`. Doel: Vane's `[[Tiles]]`-config en
templates baseren op wat er *echt* binnenkomt, niet op aannames uit de
designmockup (die op een Davis Vantage-vocabulaire lijkt te zijn gebaseerd).

## Opgehelderd via de officiële [Tempest UDP API](https://weatherflow.github.io/Tempest/api/udp/v143/)

Het `obs_st`-pakket bevat 18 velden in vaste volgorde, o.a.: wind lull, wind
avg, **wind gust**, wind direction (één, niet apart voor gust), station
pressure, air temp, humidity, **illuminance**, UV, solar radiation, rain/min,
precipitatietype, lightning avg distance, lightning count, battery, report
interval.

1. **`luxXXX = illuminance.ST-00018664.obs_st`** — het brondata-pad
   (`illuminance...`) is correct en bestaat echt in `obs_st` (veld 10/18).
   Alleen de WeeWX-kant naam `luxXXX` is een ongebruikte placeholder —
   voorstel: hernoemen naar `luminosity` of `illuminance`.
2. **`windGust` ontbreekt, maar is wel beschikbaar** (veld 4/18). Vermoedelijke
   toe te voegen regel, naar analogie van de bestaande `wind_speed`/
   `wind_direction`-namen uit `rapid_wind`:

   ```ini
   windGust = wind_gust.ST-00018664.obs_st
   ```

   Verifieer het exacte veldpad in de weewx-log (`log_raw_packets = True`
   staat al aan) voordat je 'm vastzet.
3. **`windGustDir` bestaat niet apart bij Tempest** — er is maar één
   winddichting-veld per `obs_st`-rapport (geen aparte gust-richting zoals bij
   Davis). Het designmockup toont dit gescheiden; voor Tempest-stations laat
   Vane deze widget dus gewoon weg i.p.v. 'm te vervalsen met dezelfde waarde
   als `windDir`.

## Wat dit betekent voor Vane's tegel-configuratie

- **`pressure` wordt geleverd, `barometer` niet direct** — maar
  `StdWXCalculate` staat op `prefer_hardware` voor `barometer`, dus WeeWX
  berekent 'm zelf in software. `$current.barometer` werkt dus gewoon, geen
  actie nodig.
- **Alle "gevoelstemperatuur"-afgeleiden werken al**: `dewpoint`, `windchill`,
  `heatindex`, `appTemp`, `cloudbase`, `ET` staan allemaal op
  `prefer_hardware` in `[StdWXCalculate]` → software-fallback actief. Dus de
  in `MOCKUP_REVIEW.md` genoemde windchill/heatindex-splitsing kan gewoon.
- **Bliksem wordt al opgevangen**: `lightning_strikes` en `avg_distance` zijn
  gemapt vanuit de Tempest zelf (naast de aparte ontladingen.nl-bron uit
  `THEME_PLAN.md`). **Nog te verifiëren**: dit zijn geen standaard
  WeeWX-kolomnamen uit `schemas.wview_extended` — check of ze daadwerkelijk in
  `weewx.sdb` belanden, anders moet het schema hiervoor uitgebreid worden.
- **Eén batterij, niet twee**: `outTempBatteryStatus` én `windBatteryStatus`
  wijzen naar hetzelfde Tempest-batterijveld (één geïntegreerde sensorunit).
  De Telemetrie-tegels uit het mockup ("Zenderbatterij" + "Consolebatterij"
  apart) zijn Davis-specifiek — voor dit station wordt dat één "Batterij
  buitenunit"-tegel.
- **Geen signaal-/ontvangstpercentage gemapt** — het mockup toont
  "Ontvangst 98,4%" (Davis' `rxCheckPercent`), maar daar is voor deze
  WeatherFlow-config geen equivalent voor. Telemetrie-pagina toont deze tegel
  dus niet voor dit station (bevestigt de sensor-agnostische aanpak uit
  `THEME_PLAN.md` — dit is precies zo'n geval).

## Wat bevestigd is (geen wijziging nodig)

- `unit_system = metric` en `lang = nl` staan al goed in `weewx.conf`,
  overeenkomstig `THEME_PLAN.md`'s keuze voor een vast eenheidsstelsel.
- Database: single-station SQLite (`weewx.sdb`), schema `wview_extended`.
- Deploy-pad is al ingericht: FTPS naar `weerstationlangezwaag.nl` (zie
  `[[FTP]]` in `weewx.conf`) — Vane hoeft dus geen nieuwe deploy-methode te
  verzinnen, alleen straks als extra/vervangende `[[VaneReport]]`-stanza in
  `[StdReport]` worden toegevoegd naast (of i.p.v.) `StandardReport`.
- **NeoWX Material doet géén sensor-detectie** — het `[Extras]`-blok in
  `skin.conf` is puur handmatige yes/no-toggles (bv. `show_almanac = yes`),
  geen `has_data`-check. Bevestigt dat Vane's `has_data`-gedreven
  `[[Tiles]]`-aanpak een echte verbetering is, niet iets dat al elders is
  opgelost.
- Geen `ImageGenerator` in NeoWX's `skin.conf` — bevestigt dat ook het huidige
  theme al puur client-side rendert, geen server-PNG's. Sluit aan bij Vane's
  eigen datastrategie.
