# Installing / updating Vane

## 1. Build the zip

```bash
python build.py
```

This reads the file list and version number straight out of `install.py`
(via `ast`, not by importing it — `install.py` imports `weecfg.extension`,
which is only available inside a WeeWX environment) and fails hard if
`install.py` names a file that doesn't exist on disk. Result:
`dist/vane-<version>.zip`.

## 2. Which `weectl` do you have?

WeeWX 5.x has two common install methods, and that only determines **which
`weectl` command** you use — the rest of these instructions is identical for
both:

| Install method | `weectl` location | How to recognize it |
|---|---|---|
| **pip/venv install** (e.g. `~/weewx-venv`) | `~/weewx-venv/bin/weectl` | You created a venv yourself and installed WeeWX into it with `pip install weewx` |
| **Package install** (apt/dnf, `weewx.com/apt`) | just `weectl` (already on PATH) | Installed via the WeeWX apt repository, config lives in `/etc/weewx/` |

Not sure which one? `which weectl` (a package install returns a path) or
look for a `weewx-venv`/`weewx-data` folder in your home directory
(pip install).

## 3. Fresh install

```bash
# pip/venv install:
~/weewx-venv/bin/weectl extension install vane-0.4.0.zip --config=/path/to/weewx.conf

# package install:
weectl extension install vane-0.4.0.zip
```

`weectl` automatically adds the `[[Vane]]`, `[[VaneEN]]` and `[[VaneDE]]` stanzas to your
`weewx.conf` (see `install.py`) and copies the skin files to
`SKIN_ROOT/Vane`.

### Set web permissions (avoid PermissionError)

If an existing skin (e.g. Seasons or NeoWX Material) previously wrote files
like `manifest.json` or `favicon.svg` with root ownership, WeeWX will fail with
`PermissionError: [Errno 1] Operation not permitted`. Ensure the `weewx` user
owns the web destination folder:

```bash
sudo chown -R weewx:weewx /var/www/html/weewx
sudo chmod -R 775 /var/www/html/weewx
```

### Making Vane your primary theme in `weewx.conf`

By default, Vane writes to `HTML_ROOT = vane` so it doesn't clobber your existing
theme. When you're ready to make Vane your main site:

1. **Disable your old theme** under `[StdReport]`:
   ```ini
   [[SeasonsReport]]
       enable = false
   [[StandardReport]]
       enable = false
   ```

2. **Set Vane's `HTML_ROOT` to the main web directory**:
   ```ini
   [[Vane]]
       skin = Vane
       enable = true
       HTML_ROOT = /var/www/html/weewx
       lang = nl

   [[VaneEN]]
       skin = Vane
       enable = true
       HTML_ROOT = /var/www/html/weewx/en
       lang = en
       [[[Vane]]]
           root_href = ../

   [[VaneDE]]
       skin = Vane
       enable = true
       HTML_ROOT = /var/www/html/weewx/de
       lang = de
       [[[Vane]]]
           root_href = ../
   ```

3. *(WeatherFlow Tempest users)* Check your `[[sensor_map]]` under `[WeatherFlowUDP]`:
   - Map `windGust`: `windGust = wind_gust.ST-XXXXX.obs_st`
   - Map `luminosity` (not `luxXXX`): `luminosity = illuminance.ST-XXXXX.obs_st`

### Restart and generate immediately

```bash
sudo systemctl restart weewx

# Generate immediately without waiting for the next archive interval:
sudo weectl report run
```


## 4. Updating to a newer version

You can install a newer version directly over the existing installation without uninstalling. This updates all templates and skin assets while preserving your custom settings in `weewx.conf` (such as `HTML_ROOT` or `lang`):

```bash
# Install directly over the existing version (confirm with 'y' or use --yes):
sudo weectl extension install vane-<new-version>.zip --yes

# Restart WeeWX to load updated plugins/templates:
sudo systemctl restart weewx

# Generate immediately:
sudo weectl report run
```

> [!NOTE]
> If you ever perform a full `weectl extension uninstall Vane`, WeeWX will remove the `[[Vane]]` stanzas from `weewx.conf`. Reinstalling afterwards resets those stanzas to defaults (`HTML_ROOT = vane`), requiring you to reconfigure your custom `HTML_ROOT = /var/www/html/weewx` and `lang = nl`. Installing directly with `weectl extension install ... --yes` preserves your existing `weewx.conf` stanzas.

### Troubleshooting update issues

> [!WARNING]
> **PermissionError: `[Errno 1] Operation not permitted` (Actie is niet toegestaan) during CopyGenerator:**
> If you previously ran `weectl report run` under your personal user account (e.g. `dietpi`) or `root`, files in the web destination (`/var/www/html/weewx`) will be owned by that user. When WeeWX runs as its system service user `weewx`, Linux will reject attempts to overwrite or change permissions (`copymode`) on those files, causing `CopyGenerator` to terminate abruptly and leave the update incomplete.
>
> **Solution:**
> ```bash
> # 1. Restore ownership to weewx and reset permissions:
> sudo chown -R weewx:weewx /var/www/html/weewx
> sudo chmod -R 775 /var/www/html/weewx
>
> # 2. Clear static web assets so WeeWX recopies all new stylesheets, scripts and icons:
> sudo rm -rf /var/www/html/weewx/static
>
> # 3. Clear Python bytecode cache so updated search-list extensions load cleanly:
> sudo rm -rf /etc/weewx/bin/user/__pycache__
>
> # 4. Restart WeeWX and regenerate:
> sudo systemctl restart weewx
> sudo weectl report run Vane
> ```

> [!TIP]
> **Old version still displayed in browser?**
> Browsers aggressively cache CSS, JS, and HTML templates. Press **Ctrl + F5** (or **Cmd + Shift + R** on macOS) in your browser to perform a hard reload.

## 5. Multilingual support / adding your own language

By default, Vane installs three reports: `[[Vane]]` (Dutch), `[[VaneEN]]`
(English) and `[[VaneDE]]` (German). Every page shows a language `<select>`
(native names, e.g. "Nederlands"/"English"/"Deutsch", not codes) driven
entirely by `skin.conf` — no template changes needed to add a language.

To add another language (e.g. French, `fr`), 3 things need to agree on the same
code — see `docs/THEME_PLAN.md`'s "Multilingual (i18n)" section for the
full explanation, in short:

1. `skin.conf` `[Vane][[Languages]]`: add `fr = fr` (code → output
   subfolder). **This alone is enough to make it appear in the `<select>`**
   for common languages — `bin/user/vane_extras.py` has a built-in table of
   native names (German, French, Spanish, ...) it falls back to. Only add
   an entry to `[Vane][[LanguageNames]]` if you want to override that name
   or the code isn't in the built-in table at all.
2. `install.py`: copy the `[[VaneDE]]` `StdReport` stanza to a new
   `[[VaneFR]]` (new `HTML_ROOT`, `lang`, `Vane.root_href`), then rebuild
   the zip (`python build.py`) and reinstall (see section 4 above).
3. `lang/fr.conf`: the actual translations — copy `lang/en.conf` and
   translate the `[Texts]` section (plus any locale-specific overrides,
   see `lang/nl.conf` / `lang/de.conf` for the pattern).

## 6. Optional: Skyfield almanac (extra astronomy)

Vane works with WeeWX's standard almanac (PyEphem). If you also install
[weewx-skyfield-almanac](https://github.com/roe-dl/weewx-skyfield-almanac),
the Almanac page gets two extra cards, without any configuration:

- **Moon & Earth**: the constellation the Moon and Sun are in, distance to
  the Moon, solar time, equation of time, the next lunar perigee/apogee
  (with a *Supermoon* badge when a full moon is near perigee) and the
  Earth's perihelion/aphelion.
- **Planets**: rise/set of Mercury, Venus, Mars, Jupiter and Saturn, whether
  each is above the horizon, and the phase of Venus and Mercury.

Without the extension those cards simply don't appear; nothing else
changes. Notes:

- It also needs `requests`, which a pip install of WeeWX doesn't include.
  Install it **before** restarting WeeWX, or `weewxd` fails to load the
  extension's service:
  ```bash
  ~/weewx-venv/bin/pip install skyfield numpy requests
  weectl extension install weewx-skyfield-almanac.zip
  sudo systemctl restart weewx
  ```
- On first start it downloads JPL ephemeris data (`de440.bsp`, ~115 MB;
  set `ephemeris = de440s.bsp` under `[Almanac][[Skyfield]]` for a ~32 MB
  file covering 1849–2150). The extra cards appear once that has loaded,
  which can take a few archive intervals.
- It is GPL-3.0 licensed, so it is installed separately and not bundled
  in the Vane zip.

On top of that, [weewx-skymap-almanac](https://github.com/roe-dl/weewx-skymap-almanac)
(same author, also GPL-3.0, needs WeeWX 5.3+ and the Skyfield almanac
above) adds:

- a **Sky now** card: a live map of the sky above your station (Sun, Moon,
  planets, and at night stars and constellations), coloured to match Vane;
- the Moon icon on the Almanac page shows the real phase **and tilt** of
  the crescent as seen from your location.

```bash
weectl extension install weewx-skymap-almanac.zip
sudo systemctl restart weewx
```

Vane only uses what these extensions provide when they're present; it
contains none of their code and works without them.

## 7. Personal integrations don't belong in this zip

Something like your own lightning-map link or another personal widget
doesn't belong in Vane itself (see `docs/THEME_PLAN.md` "Personal
integrations are a separate plugin") — that goes via
`[Vane][[Plugins]] dashboard_plugins` in your own `weewx.conf` plus a
separate `plugins/<name>.inc` file that you place yourself in
`SKIN_ROOT/Vane/plugins/`, outside of this installer.
