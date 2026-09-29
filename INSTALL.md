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
~/weewx-venv/bin/weectl extension install dist/vane-0.2.0.zip --config=/path/to/weewx.conf

# package install:
weectl extension install dist/vane-0.2.0.zip
```

`weectl` automatically adds the `[[Vane]]` and `[[VaneEN]]` stanzas to your
`weewx.conf` (see `install.py`) and copies the skin files to
`SKIN_ROOT/Vane`. Then **restart the service**:

```bash
sudo systemctl restart weewx
```

## 4. Updating to a newer version

WeeWX's own recommended pattern is **remove, then reinstall** — not
overwrite:

```bash
weectl extension uninstall Vane
weectl extension install dist/vane-<new-version>.zip
sudo systemctl restart weewx
```

`weectl extension uninstall` only removes the skin files and the
`[[Vane]]`/`[[VaneEN]]` stanzas from `weewx.conf` — your own changes
elsewhere in `weewx.conf` (station info, driver, MQTT settings outside
`[Vane]`, etc.) stay untouched.

**Note — your own changes in the `[Vane]` config**: if you've changed
anything yourself in the `[[Vane]]`/`[[VaneEN]]` stanza of your
`weewx.conf` (language, accent color, MQTT, lightning source,
`dashboard_plugins`, ...), write those down before you uninstall — uninstall
removes the whole stanza, install puts it back to the defaults from
`install.py`. See `skins/Vane/skin.conf` for all available
`[Vane][[...]]` options.

## 5. Multilingual support / adding your own language

By default, Vane installs two reports: `[[Vane]]` (Dutch) and `[[VaneEN]]`
(English). Every page shows a language `<select>` (native names, e.g.
"Nederlands"/"English", not codes) driven entirely by `skin.conf` — no
template changes needed to add a language.

To add a third language (e.g. German), 4 things need to agree on the same
code — see `docs/THEME_PLAN.md`'s "Multilingual (i18n)" section for the
full explanation, in short:

1. `skin.conf` `[Vane][[Languages]]`: add `de = de` (code → output subfolder).
2. `skin.conf` `[Vane][[LanguageNames]]`: add `de = 🇩🇪 Deutsch` (what the
   `<select>` shows — this is what makes the new language actually appear
   in the switcher; adding `lang/de.conf` alone does **not** do this).
3. `install.py`: copy the `[[VaneEN]]` `StdReport` stanza to a new
   `[[VaneDE]]` (new `HTML_ROOT`, `lang`, `Vane.root_href`), then rebuild
   the zip (`python build.py`) and reinstall (see section 4 above).
4. `lang/de.conf`: the actual translations — copy `lang/en.conf` and
   translate the `[Texts]` section (plus any locale-specific overrides,
   see `lang/nl.conf` for the pattern).

## 6. Personal integrations don't belong in this zip

Something like your own lightning-map link or another personal widget
doesn't belong in Vane itself (see `docs/THEME_PLAN.md` "Personal
integrations are a separate plugin") — that goes via
`[Vane][[Plugins]] dashboard_plugins` in your own `weewx.conf` plus a
separate `plugins/<name>.inc` file that you place yourself in
`SKIN_ROOT/Vane/plugins/`, outside of this installer.
