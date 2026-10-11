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

   > [!IMPORTANT]
   > **The rule:** every language report lives in a subfolder *of the
   > primary report's `HTML_ROOT`*, named after the code under
   > `[Vane][[Languages]]` in `skin.conf` (`en`, `de`), with
   > `root_href = ../`. The language switcher links to
   > `<primary root>/<code>/`, so `/var/www/html/weewx/vane/de` next to a
   > primary root of `/var/www/html/weewx` gives 404s.
   >
   > Leave the `[[[Units]]]` blocks the installer added to each report as
   > they are (omitted above for brevity).

3. *(WeatherFlow Tempest users)* Check your `[[sensor_map]]` under `[WeatherFlowUDP]`:
   - Map `windGust`: `windGust = wind_gust.ST-XXXXX.obs_st`
   - Map `luminosity` (not `luxXXX`): `luminosity = illuminance.ST-XXXXX.obs_st`

### Restart and generate immediately

```bash
sudo systemctl restart weewx

# Generate immediately without waiting for the next archive interval.
# Package install: run it AS the weewx user (never plain "sudo", which
# leaves root-owned files that weewxd can't overwrite later), from a
# directory that user can enter:
cd /tmp && sudo -u weewx weectl report run
# pip/venv install: run it as the user weewxd runs as:
#   ~/weewx-venv/bin/weectl report run
```


## 4. Updating to a newer version

You can install a newer version directly over the existing installation without uninstalling. This updates all templates and skin assets while preserving your custom settings in `weewx.conf` (such as `HTML_ROOT` or `lang`):

```bash
# Install directly over the existing version (confirm with 'y' or use --yes):
sudo weectl extension install vane-<new-version>.zip --yes

# Restart WeeWX to load updated plugins/templates:
sudo systemctl restart weewx

# Generate immediately (package install; see section 3 for why not plain sudo):
cd /tmp && sudo -u weewx weectl report run
```

> [!NOTE]
> If you ever perform a full `weectl extension uninstall Vane`, WeeWX will remove the `[[Vane]]` stanzas from `weewx.conf`. Reinstalling afterwards resets those stanzas to defaults (`HTML_ROOT = vane`), requiring you to reconfigure your custom `HTML_ROOT = /var/www/html/weewx` and `lang = nl`. Installing directly with `weectl extension install ... --yes` preserves your existing `weewx.conf` stanzas.

### Troubleshooting update issues

> [!WARNING]
> **PermissionError: `[Errno 1] Operation not permitted` (Actie is niet toegestaan) during CopyGenerator:**
> If you previously ran `weectl report run` under your personal user account (e.g. `dietpi`) or as `root` (plain `sudo weectl report run`), files in the web destination (`/var/www/html/weewx`) will be owned by that user. When WeeWX runs as its system service user `weewx`, Linux will reject attempts to overwrite or change permissions (`copymode`) on those files, causing `CopyGenerator` to terminate abruptly and leave the update incomplete.
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
> # 4. Restart WeeWX and regenerate (as the weewx user, from a directory it can enter):
> sudo systemctl restart weewx
> cd /tmp && sudo -u weewx weectl report run
> ```
>
> `PermissionError: [Errno 13] ... '/home/<you>'` from that last command
> means it was started from your home directory, which the `weewx` user
> can't enter — hence the `cd /tmp` first.

> [!TIP]
> **Old version still displayed in browser?**
> Browsers aggressively cache CSS, JS, and HTML templates. Press **Ctrl + F5** (or **Cmd + Shift + R** on macOS) in your browser to perform a hard reload.

> [!WARNING]
> **Moved Vane to your main web directory?** When an update adds a new
> language report (v0.4.0 added `[[VaneDE]]`), the installer gives it the
> default `HTML_ROOT = vane/<code>`. That only matches the default layout.
> After updating, check every `[[Vane..]]` report in `weewx.conf` and set
> new ones next to the others, e.g. `HTML_ROOT = /var/www/html/weewx/de`
> (see the rule in section 3). Existing reports are never changed.

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

## 6. Optional: extra astronomy (Skyfield + Skymap almanac)

Vane works with WeeWX's standard almanac (PyEphem). Two optional
extensions by the same author add more to the **Almanac** page; Vane picks
them up automatically, without any configuration:

- [weewx-skyfield-almanac](https://github.com/roe-dl/weewx-skyfield-almanac)
  replaces PyEphem with up-to-date JPL data and adds:
  - **Moon & Earth**: the constellation the Moon and Sun are in, distance
    to the Moon, solar time, equation of time, the next lunar
    perigee/apogee (with a *Supermoon* badge when a full moon is near
    perigee) and the Earth's perihelion/aphelion;
  - **Planets**: rise/set of Mercury, Venus, Mars, Jupiter and Saturn,
    whether each is above the horizon, and the phase of Venus and Mercury.
- [weewx-skymap-almanac](https://github.com/roe-dl/weewx-skymap-almanac)
  (needs WeeWX 5.3+ and the Skyfield almanac) adds:
  - **Sky now**: a live map of the sky above your station (Sun, Moon,
    planets, and at night stars and constellations), coloured to match Vane;
  - the Moon icon shows the real phase **and tilt** of the crescent as
    seen from your location.

Without them those cards simply don't appear; nothing else changes. Both
are GPL-3.0, so they're installed separately and not bundled in the Vane
zip — Vane contains none of their code.

### Installing

**1. Python packages** — Skyfield (1.47 or newer), NumPy and `requests`.
Install them **before** restarting WeeWX, or `weewxd` fails to load the
extension's service (`requests` in particular is missing from a plain pip
install of WeeWX).

```bash
# pip/venv install
~/weewx-venv/bin/pip install skyfield numpy requests

# package install (Debian/Ubuntu/Raspberry Pi OS/DietPi/Armbian)
sudo apt install python3-skyfield python3-numpy python3-requests
python3 -c "import skyfield; print(skyfield.__version__)"   # must be >= 1.47
```

**2. The extensions** — Skyfield first, Skymap builds on it. Use your own
`weectl` (see section 2; `sudo weectl` for a package install):

```bash
wget -O weewx-skyfield-almanac.zip https://github.com/roe-dl/weewx-skyfield-almanac/archive/refs/heads/master.zip
wget -O weewx-skymap-almanac.zip https://github.com/roe-dl/weewx-skymap-almanac/archive/refs/heads/master.zip
weectl extension install weewx-skyfield-almanac.zip --yes
weectl extension install weewx-skymap-almanac.zip --yes   # optional, needs the one above
```

After installing, `weewx.conf` contains an `[Almanac]` section like this
(plus the extensions' services under `[Engine]`, which the installer adds
for you — don't add those by hand):

```ini
[Almanac]
    [[Skyfield]]
        enable = true
        ephemeris = de440.bsp     # or de440s.bsp, see below
        # ... more options the installer adds
    [[Skymap]]
        enable = true
```

**3. Restart and wait for the ephemeris**

```bash
sudo systemctl restart weewx
sudo journalctl -u weewx -f | grep -i -E "skyfield|skymap|error"
```

On first start the Skyfield almanac downloads JPL ephemeris data into the
database directory (`<SQLITE_ROOT>/skyfield`): `de440.bsp`, ~115 MB. On a
small SD card you can set `ephemeris = de440s.bsp` under
`[Almanac][[Skyfield]]` in `weewx.conf` instead (~32 MB, covers
1849–2150). Once the log shows `successfully created Moon reference
frame`, the extra cards appear with the next report cycle.

**Notes**

- On slower hardware (Raspberry Pi, Orange Pi) the first report run of
  each day takes noticeably longer: Vane then computes the day length for
  the whole year with Skyfield. The result is cached for the rest of the
  day.
- To switch the Skyfield almanac off again without uninstalling, set
  `enable = false` under `[Almanac][[Skyfield]]` and restart WeeWX.

## 7. Personal integrations don't belong in this zip

Something like your own lightning-map link or another personal widget
doesn't belong in Vane itself (see `docs/THEME_PLAN.md` "Personal
integrations are a separate plugin") — that goes via
`[Vane][[Plugins]] dashboard_plugins` in your own `weewx.conf` plus a
separate `plugins/<name>.inc` file that you place yourself in
`SKIN_ROOT/Vane/plugins/`, outside of this installer.
