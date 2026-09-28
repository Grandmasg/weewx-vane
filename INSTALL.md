# Vane installeren / updaten

## 1. De zip bouwen

```bash
python build.py
```

Dit leest de bestandenlijst en het versienummer rechtstreeks uit `install.py`
(via `ast`, niet door het te importeren — `install.py` importeert
`weecfg.extension`, wat alleen binnen een WeeWX-omgeving beschikbaar is) en
faalt hard als `install.py` een bestand noemt dat niet bestaat op schijf.
Resultaat: `dist/vane-<versie>.zip`.

## 2. Welke `weectl` heb je?

WeeWX 5.x kent twee gangbare installatiewijzen, en dat bepaalt alleen **welk
`weectl`-commando** je gebruikt — de rest van deze instructies is voor beide
identiek:

| Installatiewijze | `weectl`-locatie | Herkenningspunt |
|---|---|---|
| **pip/venv-install** (bv. `~/weewx-venv`) | `~/weewx-venv/bin/weectl` | Je hebt zelf een venv aangemaakt en WeeWX erin geïnstalleerd met `pip install weewx` |
| **Pakket-install** (apt/dnf, `weewx.com/apt`) | gewoon `weectl` (staat al op PATH) | Geïnstalleerd via de WeeWX-apt-repository, config staat in `/etc/weewx/` |

Weet je het niet zeker? `which weectl` (pakket-install geeft een pad terug)
of zoek naar een map met `weewx-venv`/`weewx-data` in je home-directory
(pip-install).

## 3. Vers installeren

```bash
# pip/venv-install:
~/weewx-venv/bin/weectl extension install dist/vane-0.2.0.zip --config=/pad/naar/weewx.conf

# pakket-install:
weectl extension install dist/vane-0.2.0.zip
```

`weectl` zet automatisch de `[[Vane]]`- en `[[VaneEN]]`-stanza's in je
`weewx.conf` (zie `install.py`) en kopieert de skin-bestanden naar
`SKIN_ROOT/Vane`. Daarna **de service herstarten**:

```bash
sudo systemctl restart weewx
```

## 4. Updaten naar een nieuwere versie

WeeWX's eigen aanbevolen patroon is **verwijderen, dan opnieuw installeren**
— niet overschrijven:

```bash
weectl extension uninstall Vane
weectl extension install dist/vane-<nieuwe-versie>.zip
sudo systemctl restart weewx
```

`weectl extension uninstall` verwijdert alleen de skin-bestanden en de
`[[Vane]]`/`[[VaneEN]]`-stanza's uit `weewx.conf` — je eigen aanpassingen
elders in `weewx.conf` (station-info, driver, MQTT-instellingen buiten
`[Vane]`, etc.) blijven onaangeroerd.

**Let op — eigen aanpassingen in `[Vane]`-config**: als je zelf dingen hebt
aangepast in de `[[Vane]]`/`[[VaneEN]]`-stanza van je `weewx.conf` (taal,
accentkleur, MQTT, bliksembron, `dashboard_plugins`, ...), noteer die even
vóór je uninstall't — uninstall verwijdert de hele stanza, install zet 'm
terug op de standaardwaarden uit `install.py`. Zie `skins/Vane/skin.conf`
voor alle beschikbare `[Vane][[...]]`-opties.

## 5. Meertaligheid / eigen taal toevoegen

Standaard installeert Vane twee rapporten: `[[Vane]]` (Nederlands) en
`[[VaneEN]]` (Engels), zie `docs/THEME_PLAN.md` voor hoe je een derde taal
toevoegt (kopieer het `[[VaneEN]]`-blok, nieuwe `HTML_ROOT`/`lang`, en een
`lang/<code>.conf`-bestand).

## 6. Persoonlijke integraties horen niet in deze zip

Iets als een eigen bliksemkaart-link of een andere persoonlijke widget hoort
niet in Vane zelf (zie `docs/THEME_PLAN.md` "Persoonlijke integraties zijn
een losse plugin") — dat gaat via `[Vane][[Plugins]] dashboard_plugins` in je
eigen `weewx.conf` plus een los `plugins/<naam>.inc`-bestand dat je zelf in
`SKIN_ROOT/Vane/plugins/` zet, buiten deze installer om.
