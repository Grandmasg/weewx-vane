"""Vane — WeeWX ExtensionInstaller.

Install with: weectl extension install /path/to/vane
See docs/THEME_PLAN.md for the full architectural reasoning.
"""

from weecfg.extension import ExtensionInstaller


def loader():
    return VaneInstaller()


class VaneInstaller(ExtensionInstaller):
    def __init__(self):
        super(VaneInstaller, self).__init__(
            version="0.4.1",
            name="Vane",
            description="Modern, sensor-agnostic WeeWX dashboard theme.",
            author="Grandmasg",
            author_email="info@cleanos.grandmasg.nl",
            config={
                "StdReport": {
                    "Vane": {
                        "skin": "Vane",
                        "enable": "true",
                        "HTML_ROOT": "vane",
                        # Deliberately no unit_system key here: none of
                        # WeeWX's us/metric/metricwx presets match our
                        # exact wanted combination (mm rain, hPa pressure,
                        # km/h wind, degree_C temp) — metricwx is closest
                        # but gives meter_per_second wind and mbar
                        # pressure. Instead, [Units][[Groups]] below is
                        # merged directly into this report's stanza, which
                        # reportengine.py's build_skin_dict() applies LAST
                        # (after skin.conf's own [Units][[Groups]] AND
                        # after any global [StdReport][[Defaults]]
                        # unit_system in the installing user's own
                        # weewx.conf, which would otherwise silently
                        # clobber our units — found during WSL testing,
                        # where a pre-existing Defaults unit_system=metric
                        # overrode skin.conf's pressure/rain groups while
                        # speed/temp/altitude coincidentally matched
                        # "metric"'s own defaults). This makes Vane's units
                        # independent of whatever the end user's weewx.conf
                        # Defaults section happens to set.
                        "Units": {
                            "Groups": {
                                "group_altitude": "meter",
                                "group_pressure": "hPa",
                                "group_rain": "mm",
                                "group_rainrate": "mm_per_hour",
                                "group_speed": "km_per_hour",
                                "group_temperature": "degree_C",
                            },
                        },
                        # lang not set explicitly here: for Dutch-language
                        # use, set this to 'nl' yourself in weewx.conf (or
                        # leave it unset for the publishable English base,
                        # see THEME_PLAN.md i18n section).
                    },
                    "VaneEN": {
                        # Same skin, same data — only the language + output
                        # dir + lang_code/root_href in [[[Vane]]] differ.
                        # Two complete, separately generated reports instead
                        # of a client-side toggle (that's not possible, see
                        # THEME_PLAN.md language-switch section).
                        #
                        # Adding another language (e.g. French) = copy this
                        # block to "VaneFR": HTML_ROOT="vane/fr", lang="fr",
                        # Vane.root_href="../", add "fr = fr" to
                        # [Vane][[Languages]] in skin.conf, and add a
                        # lang/fr.conf with the French [Texts] (+ any
                        # locale-specific [Labels]/[Units][[Ordinates]]/
                        # [Almanac] overrides, see lang/nl.conf). Templates
                        # need no changes — they use the builtin $lang tag
                        # and simply loop over the Languages list.
                        "skin": "Vane",
                        "enable": "true",
                        "HTML_ROOT": "vane/en",
                        "lang": "en",
                        "Units": {
                            "Groups": {
                                "group_altitude": "meter",
                                "group_pressure": "hPa",
                                "group_rain": "mm",
                                "group_rainrate": "mm_per_hour",
                                "group_speed": "km_per_hour",
                                "group_temperature": "degree_C",
                            },
                        },
                        "Vane": {
                            "root_href": "../",
                        },
                    },
                    "VaneDE": {
                        # Same as VaneEN, see the comment there.
                        "skin": "Vane",
                        "enable": "true",
                        "HTML_ROOT": "vane/de",
                        "lang": "de",
                        "Units": {
                            "Groups": {
                                "group_altitude": "meter",
                                "group_pressure": "hPa",
                                "group_rain": "mm",
                                "group_rainrate": "mm_per_hour",
                                "group_speed": "km_per_hour",
                                "group_temperature": "degree_C",
                            },
                        },
                        "Vane": {
                            "root_href": "../",
                        },
                    },
                }
            },
            files=[
                ("bin/user", [
                    "bin/user/vane_extras.py",
                ]),
                ("skins/Vane", [
                    "skins/Vane/skin.conf",
                    "skins/Vane/index.html.tmpl",
                    "skins/Vane/graphs.html.tmpl",
                    "skins/Vane/archive.html.tmpl",
                    "skins/Vane/archive-%Y-%m.html.tmpl",
                    "skins/Vane/telemetry.html.tmpl",
                    "skins/Vane/almanac.html.tmpl",
                    "skins/Vane/footer.inc",
                    "skins/Vane/favicon.svg",
                    "skins/Vane/apple-touch-icon.png",
                    "skins/Vane/manifest.json",
                ]),
                ("skins/Vane/data", [
                    "skins/Vane/data/current.json.tmpl",
                    "skins/Vane/data/day.json.tmpl",
                    "skins/Vane/data/week.json.tmpl",
                    "skins/Vane/data/month.json.tmpl",
                    "skins/Vane/data/year.json.tmpl",
                    "skins/Vane/data/all.json.tmpl",
                ]),
                ("skins/Vane/data/archive", [
                    "skins/Vane/data/archive/%Y-%m.json.tmpl",
                ]),
                ("skins/Vane/NOAA", [
                    "skins/Vane/NOAA/NOAA-%Y-%m.txt.tmpl",
                    "skins/Vane/NOAA/NOAA-%Y.txt.tmpl",
                ]),
                ("skins/Vane/lang", [
                    "skins/Vane/lang/en.conf",
                    "skins/Vane/lang/nl.conf",
                    "skins/Vane/lang/de.conf",
                ]),
                ("skins/Vane/static/css", [
                    "skins/Vane/static/css/vane.css",
                ]),
                ("skins/Vane/static/js", [
                    "skins/Vane/static/js/theme-toggle.js",
                    "skins/Vane/static/js/lang-select.js",
                    "skins/Vane/static/js/chart-tooltip.js",
                    "skins/Vane/static/js/graphs.js",
                    "skins/Vane/static/js/sortable-table.js",
                    "skins/Vane/static/js/noaa-modal.js",
                    "skins/Vane/static/js/dashboard-live.js",
                    "skins/Vane/static/js/vane-lottie.js",
                ]),
                ("skins/Vane/static/js/vendor", [
                    "skins/Vane/static/js/vendor/uPlot.iife.min.js",
                    "skins/Vane/static/js/vendor/uPlot.min.css",
                    "skins/Vane/static/js/vendor/mqtt.min.js",
                    "skins/Vane/static/js/vendor/lottie_light.min.js",
                ]),
                ("skins/Vane/static/img", [
                    "skins/Vane/static/img/logo-mark.svg",
                ]),
                ("skins/Vane/static/img/flags", [
                    "skins/Vane/static/img/flags/nl.svg",
                    "skins/Vane/static/img/flags/gb.svg",
                    "skins/Vane/static/img/flags/de.svg",
                    "skins/Vane/static/img/flags/fr.svg",
                    "skins/Vane/static/img/flags/es.svg",
                    "skins/Vane/static/img/flags/it.svg",
                    "skins/Vane/static/img/flags/pt.svg",
                    "skins/Vane/static/img/flags/pl.svg",
                    "skins/Vane/static/img/flags/dk.svg",
                    "skins/Vane/static/img/flags/se.svg",
                    "skins/Vane/static/img/flags/no.svg",
                    "skins/Vane/static/img/flags/fi.svg",
                ]),
                ("skins/Vane/static/img/icons", [
                    "skins/Vane/static/img/icons/clear-day.svg",
                    "skins/Vane/static/img/icons/clear-night.svg",
                    "skins/Vane/static/img/icons/partly-cloudy-day.svg",
                    "skins/Vane/static/img/icons/partly-cloudy-night.svg",
                    "skins/Vane/static/img/icons/cloudy.svg",
                    "skins/Vane/static/img/icons/overcast.svg",
                    "skins/Vane/static/img/icons/fog.svg",
                    "skins/Vane/static/img/icons/drizzle.svg",
                    "skins/Vane/static/img/icons/rain.svg",
                    "skins/Vane/static/img/icons/thunderstorms.svg",
                    "skins/Vane/static/img/icons/snow.svg",
                    "skins/Vane/static/img/icons/sleet.svg",
                    "skins/Vane/static/img/icons/hail.svg",
                    "skins/Vane/static/img/icons/sunrise.svg",
                    "skins/Vane/static/img/icons/sunset.svg",
                    "skins/Vane/static/img/icons/humidity.svg",
                    "skins/Vane/static/img/icons/barometer.svg",
                    "skins/Vane/static/img/icons/uv-index.svg",
                    "skins/Vane/static/img/icons/solar-radiation.svg",
                    "skins/Vane/static/img/icons/evapotranspiration.svg",
                    "skins/Vane/static/img/icons/cloudbase.svg",
                    "skins/Vane/static/img/icons/wind.svg",
                    "skins/Vane/static/img/icons/raindrops.svg",
                    "skins/Vane/static/img/icons/thermometer.svg",
                    "skins/Vane/static/img/icons/thermometer-low.svg",
                    "skins/Vane/static/img/icons/thermometer-high.svg",
                    "skins/Vane/static/img/icons/moon-new.svg",
                    "skins/Vane/static/img/icons/moon-waxing-crescent.svg",
                    "skins/Vane/static/img/icons/moon-first-quarter.svg",
                    "skins/Vane/static/img/icons/moon-waxing-gibbous.svg",
                    "skins/Vane/static/img/icons/moon-full.svg",
                    "skins/Vane/static/img/icons/moon-waning-gibbous.svg",
                    "skins/Vane/static/img/icons/moon-last-quarter.svg",
                    "skins/Vane/static/img/icons/moon-waning-crescent.svg",
                    "skins/Vane/static/img/icons/pwa-192.png",
                    "skins/Vane/static/img/icons/pwa-512.png",
                ]),
                ("skins/Vane/static/img/seasons", [
                    "skins/Vane/static/img/seasons/spring.svg",
                    "skins/Vane/static/img/seasons/summer.svg",
                    "skins/Vane/static/img/seasons/autumn.svg",
                    "skins/Vane/static/img/seasons/winter.svg",
                ]),
                ("skins/Vane/static/lottie", [
                    "skins/Vane/static/lottie/README.md",
                ]),
                ("skins/Vane/static/lottie/icons", [
                    "skins/Vane/static/lottie/icons/clear-day.json",
                    "skins/Vane/static/lottie/icons/clear-night.json",
                    "skins/Vane/static/lottie/icons/partly-cloudy-day.json",
                    "skins/Vane/static/lottie/icons/partly-cloudy-night.json",
                    "skins/Vane/static/lottie/icons/cloudy.json",
                    "skins/Vane/static/lottie/icons/overcast.json",
                    "skins/Vane/static/lottie/icons/fog.json",
                    "skins/Vane/static/lottie/icons/drizzle.json",
                    "skins/Vane/static/lottie/icons/rain.json",
                    "skins/Vane/static/lottie/icons/raindrops.json",
                    "skins/Vane/static/lottie/icons/sleet.json",
                    "skins/Vane/static/lottie/icons/thunderstorms.json",
                    "skins/Vane/static/lottie/icons/snow.json",
                    "skins/Vane/static/lottie/icons/hail.json",
                    "skins/Vane/static/lottie/icons/sunrise.json",
                    "skins/Vane/static/lottie/icons/sunset.json",
                    "skins/Vane/static/lottie/icons/humidity.json",
                    "skins/Vane/static/lottie/icons/barometer.json",
                    "skins/Vane/static/lottie/icons/uv-index.json",
                    "skins/Vane/static/lottie/icons/solar-radiation.json",
                    "skins/Vane/static/lottie/icons/wind.json",
                    "skins/Vane/static/lottie/icons/thermometer.json",
                ]),
                ("skins/Vane/static/lottie/seasons", [
                    "skins/Vane/static/lottie/seasons/autumn.json",
                    "skins/Vane/static/lottie/seasons/winter.json",
                    "skins/Vane/static/lottie/seasons/spring.json",
                    "skins/Vane/static/lottie/seasons/summer.json",
                ]),
            ],
        )
