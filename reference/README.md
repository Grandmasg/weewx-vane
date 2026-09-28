# Reference — invoermateriaal, geen onderdeel van Vane

Deze map bevat materiaal dat we gebruiken *als input/vergelijking*, maar dat
zelf geen onderdeel van het Vane-theme is en niet meegepubliceerd wordt.
Zie de root-`.gitignore` — een deel hiervan wordt bewust genegeerd door git.

## `weewx-conf/`

- **`weewx.conf`** — het actieve, live `weewx.conf` van het Grandmasg-station
  (WeatherFlow Tempest). Bevat wachtwoorden/API-keys voor uploads (WOW,
  Wunderground, MQTT, etc.) — **git-ignored, nooit committen**. Gebruikt om te
  verifiëren welke `[StdReport]`/`[Station]`-instellingen en welke
  observatietypes er in de praktijk beschikbaar zijn.
- **`weewx.conf-5.5.0.dist`** — een schone, ongewijzigde WeeWX 5.5.0
  standaardconfiguratie. Veilig te committen; gebruiken om te zien wat
  standaard vs. aangepast is in het actieve bestand hierboven.

## `neowx-material/`

Volledige broncode van het huidige, actieve theme (NeoWX Material) — 346
bestanden, inclusief echte Cheetah-templates (`.tmpl`/`.inc`), `skin.conf`,
CSS/JS. Waardevol als **echt werkend voorbeeld** van WeeWX-Cheetah-syntax in
de praktijk (verder dan de marketingpagina), maar dit is code van Neoground
met een eigen licentie — **git-ignored**, blijft lokaal, wordt niet
overgenomen 1-op-1 in Vane (zie ook de handoff-instructies in
`design/mockup-handoff/.../README.md`: hetzelfde principe — ter inspiratie
lezen, niet kopiëren).
