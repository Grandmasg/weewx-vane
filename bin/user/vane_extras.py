"""Vane — search-list-extension.

Two responsibilities, both motivated in docs/THEME_PLAN.md:

1. Automatic discovery of "extra sensors": anything a station actually
   reports beyond the curated CORE tile list (skin.conf [Vane][[Tiles]]),
   bundled by category. Pattern inspired by how aganetwx solves this
   (GPLv3) — this implementation is written from scratch, no code taken
   from it.
2. Small helpers that would be awkward/unreadable in plain Cheetah
   templates: building an SVG sparkline path, and translating a weather
   condition into a Meteocons icon name (WeeWX has no observation type of
   its own for this).
"""

import json
import logging
import math
import os
import re
import shutil
import subprocess
import time
import urllib.request

import weewx.almanac
import weewx.cheetahgenerator
import weewx.units

log = logging.getLogger(__name__)

# Cache-busting query string for static/css/js asset URLs (see
# get_extension_list's vane_version) — without this, a browser that
# cached an old vane.css/*.js keeps using it after an update even though
# the generated HTML already has new markup, which can visibly break the
# layout until the user hard-refreshes. Bump this alongside install.py's
# version whenever static/css or static/js changes.
VANE_VERSION = "0.3.2"


# CORE observations get their own designed tile (see DESIGN_PLAN.md) and
# are therefore excluded from the "extra sensors" detection below. Must
# stay in sync with skin.conf [Vane][[Tiles]]'s dashboard list.
CORE_OBSERVATIONS = frozenset([
    "outTemp", "outHumidity", "windSpeed", "windDir", "windGust",
    "windGustDir", "barometer", "pressure", "altimeter", "rain", "rainRate",
    "UV", "radiation", "luminosity", "dewpoint", "windchill", "heatindex",
    "appTemp", "cloudbase", "ET", "dateTime", "usUnits", "interval",
    "lightning_strike_count", "lightning_distance",
    "txBatteryStatus", "consBatteryVoltage", "rxCheckPercent", "signal4",
])

# Native display name for common ISO 639-1 codes — used as the default
# label so adding a common European language only needs a line in
# skin.conf [Vane][[Languages]], no matching [[LanguageNames]] entry.
# skin.conf's [[LanguageNames]] always wins when present (see
# _language_name below), for overriding one of these or adding a code
# that isn't in this table at all.
LANGUAGE_NAMES = {
    "nl": "Nederlands",
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "pl": "Polski",
    "da": "Dansk",
    "sv": "Svenska",
    "no": "Norsk",
    "fi": "Suomi",
    "fy": "Frysk",
}

# Language code -> flag-icons (lipis, MIT, see THIRD-PARTY-LICENSES.md)
# country code, for the custom listbox's flag icons
# (skins/Vane/static/img/flags/<code>.svg). A flag represents a country,
# not a language (Dutch is also spoken in Belgium, English in plenty of
# countries) — this is deliberately just the conventional "most
# recognizable" choice for each, same tradeoff every language switcher
# with flags makes. A language with no entry here simply gets no flag
# icon (falls back to text-only in the template), rather than erroring.
FLAG_CODES = {
    "nl": "nl",
    "en": "gb",
    "de": "de",
    "fr": "fr",
    "es": "es",
    "it": "it",
    "pt": "pt",
    "pl": "pl",
    "da": "dk",
    "sv": "se",
    "no": "no",
    "fi": "fi",
}

# (prefix, group name) — first match wins. Freely extendable without ever
# needing to maintain a fixed sensor list anywhere.
BUCKET_RULES = (
    ("extraTemp", "temperature"),
    ("extraHumid", "temperature"),
    ("soilTemp", "soil"),
    ("soilMoist", "soil"),
    ("leafTemp", "soil"),
    ("leafWet", "soil"),
    ("pm", "air quality"),
    ("co2", "air quality"),
    ("aqi", "air quality"),
    ("battery", "status"),
    ("Battery", "status"),
    ("signal", "status"),
    ("rssi", "status"),
    ("rxCheck", "status"),
)


def _bucket(obs_key):
    for prefix, group in BUCKET_RULES:
        if obs_key.startswith(prefix):
            return group
    return "other"


class VaneExtras(weewx.cheetahgenerator.SearchList):
    """Provides `vane_extra_sensors`, `vane_sparkline_path()` and
    `vane_condition_icon()` to all Vane templates."""

    def __init__(self, generator):
        weewx.cheetahgenerator.SearchList.__init__(self, generator)

    def get_extension_list(self, timespan, db_lookup):
        db_manager = db_lookup()

        try:
            sqlkeys = db_manager.sqlkeys
        except AttributeError:
            sqlkeys = []

        record = db_manager.getRecord(timespan.stop)

        present = {}
        if record:
            for key, value in record.items():
                if value is not None:
                    present[key] = value
        else:
            for key in sqlkeys:
                present[key] = None

        excluded = set()
        try:
            skin_dict = self.generator.skin_dict
            raw = skin_dict.get("Vane", {}).get("ExtraSensors", {}).get("exclude", "")
            excluded = {o.strip() for o in raw.split(",") if o.strip()}
        except Exception:
            pass

        buckets = {}
        for key in sorted(present.keys()):
            if key in CORE_OBSERVATIONS or key in excluded:
                continue
            group = _bucket(key)
            buckets.setdefault(group, []).append(key)

        extra_sensors = []
        for group, keys in sorted(buckets.items()):
            group_items = []
            for key in keys:
                # record[key] is guaranteed non-None here (see 'present'
                # above) — no separate has_data check needed, that belongs
                # to the $day.<obs> tag layer (ObservationBinder), not to a
                # bare ValueHelper like this one.
                helper = weewx.units.ValueHelper(
                    weewx.units.as_value_tuple(record, key),
                    context="current",
                    formatter=self.generator.formatter,
                    converter=self.generator.converter,
                )
                label = self.generator.skin_dict.get("Labels", {}).get(
                    "Generic", {}
                ).get(key, key)
                group_items.append({"key": key, "label": label, "value": helper})
            if group_items:
                extra_sensors.append({"group": group, "items": group_items})

        # WeeWX exposes [Extras] as $Extras automatically (hardcoded in
        # weewx.cheetahgenerator), but no other top-level skin.conf block —
        # so we need to pass [Vane] through as $Vane ourselves, otherwise
        # you get 'cannot find Vane' the moment a template uses it.
        vane_config = self.generator.skin_dict.get("Vane", {})

        return [{"Vane": vane_config,
                 "vane_extra_sensors": extra_sensors,
                 "vane_sparkline_path": self._sparkline_path,
                 "vane_condition_icon": self._condition_icon,
                 "vane_moon_icon": self._moon_icon,
                 "vane_temp_color": self._temp_color,
                 "vane_temp_gradient": self._temp_gradient,
                 "vane_windrose": self._windrose_data(timespan, db_manager),
                 "vane_wind_vector": self._wind_vector_data(timespan, db_manager),
                 "vane_rain_color": self._rain_color,
                 "vane_weekday": self._weekday_iso,
                 "vane_lightning_mode": self._lightning_mode(timespan, db_manager),
                 "vane_lightning_api": self._vane_lightning_api,
                 "vane_dashboard_plugins_html": self._dashboard_plugins_html(),
                 "vane_language_name": self._language_name,
                 "vane_language_flag": self._language_flag,
                 "vane_version": VANE_VERSION,
                 "vane_gauge_arc": self._gauge_arc,
                 "vane_gauge_pointer_arc": self._gauge_pointer_arc,
                 "vane_uv_color": self._uv_color,
                 "vane_mqtt_config_json": self._mqtt_config_json(),
                 "vane_current_json": self._current_conditions_json(record),
                 "vane_sun_arc": self._sun_arc_data(timespan),
                 "vane_season_events": self._season_events(timespan),
                 "vane_day_length_year": self._day_length_year_data(timespan),
                 "vane_telemetry_services": self._telemetry_services(),
                 "vane_power_voltage": self._power_voltage(),
                 "vane_storage": self._storage_info(),
                 "vane_record_count": self._record_count(db_manager)}]

    @staticmethod
    def _sparkline_path(values, width=300, height=64):
        """Builds an SVG path (line + filled area) from a list of numbers.
        Returns (line_d, area_d). Empty/single-value input returns empty
        strings (the template then shows the empty-data state, no crash)."""
        clean = [v for v in values if v is not None]
        if len(clean) < 2:
            return "", ""

        lo, hi = min(clean), max(clean)
        if hi - lo < 1e-9:
            hi = lo + 1.0

        n = len(clean)

        def x(i):
            return i / (n - 1) * width

        def y(v):
            return height - (v - lo) / (hi - lo) * height

        points = [(x(i), y(v)) for i, v in enumerate(clean)]
        line_d = "M" + " L".join("%.2f,%.2f" % p for p in points)
        area_d = line_d + " L%.2f,%.2f L0,%.2f Z" % (width, height, height)
        return line_d, area_d

    @staticmethod
    def _condition_icon(radiation, max_solar_rad, rain_rate, is_day=True):
        """Heuristic — WeeWX has no 'condition' tag and no reliable
        cloud-cover observation on most stations (not on Tempest/Simulator
        either). Uses the radiation/maxSolarRad ratio instead (available
        everywhere as a WeeWX xtype) as a cloud-cover proxy during
        daytime. At night that ratio isn't usable (maxSolarRad=0), so only
        rain/clear is distinguished then — no false precision pretended.
        Returns a Meteocons file name (without extension/style path)."""
        if rain_rate and rain_rate > 0:
            return "rain"
        if not is_day or not max_solar_rad:
            return "clear-day" if is_day else "clear-night"
        ratio = (radiation or 0) / max_solar_rad
        if ratio > 0.8:
            return "clear-day"
        if ratio > 0.4:
            return "partly-cloudy-day"
        if ratio > 0.15:
            return "cloudy"
        return "overcast"

    # Shape of the scale (5 relative stops: cold -> cool -> comfortable ->
    # warm -> hot), but the BOUNDS are NOT hardcoded — see _temp_color:
    # that receives lo/hi from the station's own $alltime record, so a
    # desert station or a Scandinavian station automatically gets a
    # different scale, with nothing to configure. -15/+35 below is purely
    # the fallback for a brand-new station without enough history (see the
    # template: only used until the supplied lo/hi have too narrow a
    # spread).
    TEMP_COLOR_SHAPE = [
        (0.00, (37, 99, 235)),    # #2563eb cold
        (0.25, (56, 189, 248)),   # #38bdf8 cool
        (0.50, (74, 222, 128)),   # #4ade80 comfortable
        (0.75, (251, 146, 60)),   # #fb923c warm
        (1.00, (239, 68, 68)),    # #ef4444 hot
    ]
    TEMP_COLOR_FALLBACK_LO = -15.0
    TEMP_COLOR_FALLBACK_HI = 35.0
    TEMP_COLOR_MIN_SPAN = 20.0  # prevents an absurdly sensitive scale on a
                                 # station with only a few days of data so far

    @classmethod
    def _temp_color(cls, temp_c, lo=None, hi=None):
        """Interpolates a temperature (°C, raw value) to a hex color.
        lo/hi are normally this station's own $alltime.outTemp.min/.max
        (climate-agnostic); falls back to a Dutch-ish default if those are
        missing or the spread is too narrow (new station)."""
        if temp_c is None:
            return "#94a3b8"  # --text-muted as a neutral fallback
        if lo is None or hi is None or (hi - lo) < cls.TEMP_COLOR_MIN_SPAN:
            lo, hi = cls.TEMP_COLOR_FALLBACK_LO, cls.TEMP_COLOR_FALLBACK_HI
        span = hi - lo
        frac = max(0.0, min(1.0, (temp_c - lo) / span))
        stops = cls.TEMP_COLOR_SHAPE
        for (f0, c0), (f1, c1) in zip(stops, stops[1:]):
            if f0 <= frac <= f1:
                local = (frac - f0) / (f1 - f0)
                r = round(c0[0] + (c1[0] - c0[0]) * local)
                g = round(c0[1] + (c1[1] - c0[1]) * local)
                b = round(c0[2] + (c1[2] - c0[2]) * local)
                return "#%02x%02x%02x" % (r, g, b)
        return "#94a3b8"

    @classmethod
    def _temp_gradient(cls, t_min, t_max, lo=None, hi=None, steps=5):
        """CSS linear-gradient color list (ready to drop into
        'linear-gradient(90deg, ...)') that samples the full rainbow scale
        between t_min and t_max — instead of a flat 2-color blend that,
        for a wide day range, would go from blue to red through a muddy
        purple without ever showing green/orange."""
        if t_min is None or t_max is None:
            return "#94a3b8"
        if t_max <= t_min:
            return cls._temp_color(t_min, lo, hi)
        colors = []
        for i in range(steps):
            t = t_min + (t_max - t_min) * i / (steps - 1)
            colors.append(cls._temp_color(t, lo, hi))
        return ",".join(colors)

    # Universal (not climate-relative) wind-speed color scale in km/h —
    # wind-force conventions (Beaufort and its equivalents) are the same
    # everywhere, unlike temperature comfort, so this scale has no
    # per-station override (unlike TEMP_COLOR_SHAPE). Built from the
    # theme's own --accent-wind (#fb923c, see DESIGN_PLAN.md's "wind /
    # zon / UV" row) instead of an unrelated blue-green-orange-red scale —
    # calm reads as muted (--text-muted family), ramping into the theme's
    # own wind-orange at typical speeds, topping out red only for genuine
    # gale-force (kept as a distinct alarm color, not --accent-storm,
    # which stays reserved for rain/lightning).
    WIND_COLOR_SHAPE = [
        (0, (100, 116, 139)),   # calm / light air — muted, not eye-catching
        (10, (251, 191, 36)),   # gentle / moderate breeze — light warm tone
        (20, (251, 146, 60)),   # fresh / strong breeze — --accent-wind itself
        (35, (239, 68, 68)),    # near gale and up
    ]

    @classmethod
    def _wind_color(cls, speed_kmh):
        stops = cls.WIND_COLOR_SHAPE
        if speed_kmh <= stops[0][0]:
            return "#%02x%02x%02x" % stops[0][1]
        if speed_kmh >= stops[-1][0]:
            return "#%02x%02x%02x" % stops[-1][1]
        for (v0, c0), (v1, c1) in zip(stops, stops[1:]):
            if v0 <= speed_kmh <= v1:
                local = (speed_kmh - v0) / (v1 - v0)
                r = round(c0[0] + (c1[0] - c0[0]) * local)
                g = round(c0[1] + (c1[1] - c0[1]) * local)
                b = round(c0[2] + (c1[2] - c0[2]) * local)
                return "#%02x%02x%02x" % (r, g, b)
        return "#94a3b8"

    # WHO UV index risk bands (low/moderate/high/very high/extreme) — a
    # universal scale like WIND_COLOR_SHAPE, not climate-relative, so no
    # per-station override. Green->yellow->orange->red->purple, reusing
    # the same hue family as TEMP_COLOR_SHAPE/WIND_COLOR_SHAPE where they
    # overlap (comfortable green, wind-orange) for visual consistency.
    UV_COLOR_SHAPE = [
        (0, (74, 222, 128)),    # low
        (3, (250, 204, 21)),    # moderate
        (6, (251, 146, 60)),    # high
        (8, (239, 68, 68)),     # very high
        (11, (168, 85, 247)),   # extreme
    ]

    @classmethod
    def _uv_color(cls, uv):
        if uv is None:
            return "#94a3b8"
        stops = cls.UV_COLOR_SHAPE
        if uv <= stops[0][0]:
            return "#%02x%02x%02x" % stops[0][1]
        if uv >= stops[-1][0]:
            return "#%02x%02x%02x" % stops[-1][1]
        for (v0, c0), (v1, c1) in zip(stops, stops[1:]):
            if v0 <= uv <= v1:
                local = (uv - v0) / (v1 - v0)
                r = round(c0[0] + (c1[0] - c0[0]) * local)
                g = round(c0[1] + (c1[1] - c0[1]) * local)
                b = round(c0[2] + (c1[2] - c0[2]) * local)
                return "#%02x%02x%02x" % (r, g, b)
        return "#94a3b8"

    WINDROSE_SECTORS = 16

    def _windrose_data(self, timespan, db_manager):
        """Bins raw archive windDir/windSpeed readings for this timespan
        into 16 compass sectors. No built-in WeeWX tag does this (confirmed
        in MOCKUP_REVIEW.md) — $span.wind.series() only gives a time
        series, not a directional histogram, so direct SQL over the
        archive table is the practical way to get per-record
        direction+speed pairs."""
        n = self.WINDROSE_SECTORS
        counts = [0] * n
        speed_sums = [0.0] * n
        calm = 0
        total = 0

        for wind_dir, wind_speed in db_manager.genSql(
                "SELECT windDir, windSpeed FROM %s "
                "WHERE dateTime > ? AND dateTime <= ? "
                "AND windSpeed IS NOT NULL" % db_manager.table_name,
                (timespan.start, timespan.stop)):
            total += 1
            if not wind_speed or wind_dir is None:
                calm += 1
                continue
            sector = int(((wind_dir + 11.25) % 360) // (360.0 / n))
            counts[sector] += 1
            speed_sums[sector] += wind_speed

        if total == 0:
            return {"sectors": [], "calm_pct": 0.0, "has_data": False}

        # Native archive unit -> this report's display unit (e.g. km/h),
        # converted once per sector average rather than per row.
        unit, group = weewx.units.getStandardUnitType(db_manager.std_unit_system, "windSpeed")
        max_count = max(counts) if counts else 0
        directions = self.generator.skin_dict.get("Units", {}).get("Ordinates", {}).get(
            "directions", weewx.units.DEFAULT_ORDINATE_NAMES)

        sectors = []
        for i in range(n):
            avg_speed_native = (speed_sums[i] / counts[i]) if counts[i] else 0.0
            avg_speed = self.generator.converter.convert((avg_speed_native, unit, group))[0]
            radius_frac = (counts[i] / max_count) if max_count else 0.0
            sectors.append({
                "label": directions[i] if i < len(directions) else "",
                "freq_pct": 100.0 * counts[i] / total,
                "avg_speed": avg_speed,
                "color": self._wind_color(avg_speed) if counts[i] else "transparent",
                "path_d": self._wedge_path(i, n, radius_frac),
            })

        # 8 main-compass labels around the rim (N/NE/E/.../NW), same
        # placement math as _wind_vector_data's label_points — kept
        # separate (not shared data) since this rose has 16 sectors but
        # only wants 8 labels for legibility.
        label_points = []
        for i in range(8):
            x, y = self._compass_xy(i * 45.0, 140)
            idx = i * 2
            label_points.append({
                "label": directions[idx] if idx < len(directions) else "",
                "freq_pct": round(sectors[idx]["freq_pct"], 0) if idx < len(sectors) else 0,
                "x": round(x, 1), "y": round(y, 1), "value_y": round(y + 11, 1),
            })

        return {
            "sectors": sectors,
            "label_points": label_points,
            "calm_pct": 100.0 * calm / total,
            "has_data": True,
        }

    @staticmethod
    def _compass_xy(angle_deg, radius, cx=150.0, cy=150.0):
        """x,y for a point at `radius` from center at compass bearing
        `angle_deg` (0=N/up, clockwise) — shared by the windrose labels
        and the wind-vector radar so both use identical geometry."""
        rad = math.radians(angle_deg)
        return cx + radius * math.sin(rad), cy - radius * math.cos(rad)

    @staticmethod
    def _wedge_path(index, n_sectors, radius_frac, cx=150, cy=150, max_r=125, gap_deg=1.5):
        """SVG path for one windrose sector wedge, computed here (not in
        Cheetah, which has no trig) — compass bearing 0=N/up, clockwise,
        matching $obs.ordinal_compass conventions."""
        sector_width = 360.0 / n_sectors
        a0 = index * sector_width - sector_width / 2 + gap_deg / 2
        a1 = index * sector_width + sector_width / 2 - gap_deg / 2
        r = max(4.0, radius_frac * max_r)

        def point(angle_deg, radius):
            rad = math.radians(angle_deg)
            return cx + radius * math.sin(rad), cy - radius * math.cos(rad)

        x0, y0 = point(a0, r)
        x1, y1 = point(a1, r)
        return "M%.2f,%.2f L%.2f,%.2f A%.2f,%.2f 0 0,1 %.2f,%.2f Z" % (
            cx, cy, x0, y0, r, r, x1, y1)

    @staticmethod
    def _gauge_arc(value, lo, hi, cx=60.0, cy=60.0, r=50.0):
        """SVG elliptical-arc 'd' for a semicircular gauge's colored value
        arc — sweeps left-to-right over the top (180 deg at the left point,
        0 deg at the right point), NOT compass-relative like _wedge_path
        (this is a plain min..max dial, not a direction). The matching
        background track is a static path (always the full semicircle) so
        it's just hardcoded in the template, not computed here.

        Returns (path_d, frac) — frac (0..1, clamped) is handed back so the
        template can position the center value/percentage label without
        re-deriving it."""
        frac = 0.0 if hi <= lo else (value - lo) / (hi - lo)
        frac = max(0.0, min(1.0, frac))

        a0 = math.pi
        a1 = math.pi - math.pi * frac
        x0, y0 = cx + r * math.cos(a0), cy - r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy - r * math.sin(a1)
        large_arc = 1 if frac > 0.5 else 0
        # A zero-length arc (frac==0) still needs a valid path so the
        # element doesn't render as a stray dot — draw an explicit
        # zero-length "line" at the start point instead of omitting it.
        if frac <= 0.0:
            return "M%.2f,%.2f L%.2f,%.2f" % (x0, y0, x0, y0), frac
        return ("M%.2f,%.2f A%.2f,%.2f 0 %d,1 %.2f,%.2f" %
                (x0, y0, r, r, large_arc, x1, y1)), frac

    @staticmethod
    def _gauge_pointer_arc(value, lo, hi, half_width=0.04, cx=60.0, cy=60.0, r=50.0):
        """Like _gauge_arc, but for a quantity with no meaningful zero (e.g.
        barometric pressure) — a filled-from-left arc would visually read
        as "37% full", which is meaningless for a position-in-range value.
        Instead draws a short floating segment centered on the value's own
        position, track gray everywhere else, mimicking a classic analog
        gauge needle rather than a progress bar.

        Returns (path_d, frac) — same contract as _gauge_arc."""
        frac = 0.0 if hi <= lo else (value - lo) / (hi - lo)
        frac = max(0.0, min(1.0, frac))

        f0 = max(0.0, frac - half_width)
        f1 = min(1.0, frac + half_width)
        a0 = math.pi - math.pi * f0
        a1 = math.pi - math.pi * f1
        x0, y0 = cx + r * math.cos(a0), cy - r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy - r * math.sin(a1)
        return ("M%.2f,%.2f A%.2f,%.2f 0 0,1 %.2f,%.2f" %
                (x0, y0, r, r, x1, y1)), frac

    def _wind_vector_data(self, timespan, db_manager):
        """8-direction wind vector radar: average windSpeed vs average
        windGust per main compass point, overlaid as two polygons (same
        'no chart-library' approach as _windrose_data — this is a
        magnitude-by-direction view, not the frequency-by-direction view
        the windrose already gives, so it's a genuinely different question
        answered, not a re-skin of the same data)."""
        n = 8
        speed_sums = [0.0] * n
        speed_counts = [0] * n
        gust_sums = [0.0] * n
        gust_counts = [0] * n

        for wind_dir, wind_speed, wind_gust in db_manager.genSql(
                "SELECT windDir, windSpeed, windGust FROM %s "
                "WHERE dateTime > ? AND dateTime <= ? "
                "AND windDir IS NOT NULL" % db_manager.table_name,
                (timespan.start, timespan.stop)):
            sector = int(((wind_dir + 22.5) % 360) // 45)
            if wind_speed is not None:
                speed_sums[sector] += wind_speed
                speed_counts[sector] += 1
            if wind_gust is not None:
                gust_sums[sector] += wind_gust
                gust_counts[sector] += 1

        if not any(speed_counts):
            return {"has_data": False}

        unit, group = weewx.units.getStandardUnitType(db_manager.std_unit_system, "windSpeed")
        convert = self.generator.converter.convert
        avg_speeds = [convert((speed_sums[i] / speed_counts[i], unit, group))[0]
                      if speed_counts[i] else 0.0 for i in range(n)]
        avg_gusts = [convert((gust_sums[i] / gust_counts[i], unit, group))[0]
                     if gust_counts[i] else 0.0 for i in range(n)]

        # Ring scale: round the highest value up to a "nice" number so the
        # outer ring label isn't something like "23.7" (mirrors the
        # freq/avg_speed rounding already done for the windrose tooltip).
        scale_max = max(avg_speeds + avg_gusts + [1.0])
        magnitude = 10 ** math.floor(math.log10(scale_max))
        scale_max = math.ceil(scale_max / magnitude) * magnitude

        directions = self.generator.skin_dict.get("Units", {}).get("Ordinates", {}).get(
            "directions", weewx.units.DEFAULT_ORDINATE_NAMES)
        # The Ordinates list is 16-point (+"N/A" fallback); pick every
        # other one to get the 8 main compass labels for this radar.
        labels = [directions[i * 2] for i in range(n)]

        def point(angle_deg, radius):
            rad = math.radians(angle_deg)
            return 150 + radius * math.sin(rad), 150 - radius * math.cos(rad)

        def polygon(values):
            pts = [point(i * 45.0, (v / scale_max) * 125 if scale_max else 0.0)
                   for i, v in enumerate(values)]
            return " ".join("%.2f,%.2f" % p for p in pts)

        label_points = []
        for i, label in enumerate(labels):
            x, y = point(i * 45.0, 140)
            label_points.append({
                "label": label, "x": round(x, 1), "y": round(y, 1),
                "value_y": round(y + 11, 1),
                "speed": round(avg_speeds[i], 1), "gust": round(avg_gusts[i], 1),
            })

        # Per-direction marker dots (hoverable, unlike the bare polygon
        # outlines) — one pair per compass point so a tooltip can show
        # that direction's exact speed/gust instead of relying on the
        # slow/unstyled native SVG <title> hover.
        markers = []
        for i in range(n):
            sx, sy = point(i * 45.0, (avg_speeds[i] / scale_max) * 125 if scale_max else 0.0)
            gx, gy = point(i * 45.0, (avg_gusts[i] / scale_max) * 125 if scale_max else 0.0)
            markers.append({
                "label": labels[i],
                "speed": round(avg_speeds[i], 1),
                "gust": round(avg_gusts[i], 1),
                "speed_x": round(sx, 1), "speed_y": round(sy, 1),
                "gust_x": round(gx, 1), "gust_y": round(gy, 1),
            })

        return {
            "has_data": True,
            "label_points": label_points,
            "markers": markers,
            "scale_max": round(scale_max, 1),
            "speed_points": polygon(avg_speeds),
            "gust_points": polygon(avg_gusts),
        }

    # Fixed international rainfall-intensity bands (mm/day) — like wind
    # speed, this is an absolute meteorological scale (light/moderate/
    # heavy/violent rain), not climate-relative like temperature, so no
    # per-station override.
    RAIN_COLOR_STOPS = [
        (0.0, "transparent"),
        (0.2, "#1e3a5f"),
        (2.5, "#2f8bff"),
        (10.0, "#38bdf8"),
        (25.0, "#4ade80"),
        (50.0, "#fb923c"),
    ]

    @staticmethod
    def _weekday_iso(dt_raw):
        """Monday=1 .. Sunday=7, for the rain calendar heatmap's grid
        column placement (archive.html.tmpl) — plain date math, kept out
        of Cheetah since it has no time/calendar module access."""
        return time.localtime(dt_raw).tm_wday + 1

    @classmethod
    def _rain_color(cls, mm):
        if mm is None or mm <= 0:
            return "transparent"
        color = cls.RAIN_COLOR_STOPS[1][1]
        for threshold, hex_color in cls.RAIN_COLOR_STOPS:
            if mm >= threshold:
                color = hex_color
        return color

    def _lightning_mode(self, timespan, db_manager):
        """Decides where the dashboard's lightning tile gets its data from
        (skin.conf [Vane][[Lightning]]):
          auto  - local archive data if any station/sensor populated it
                  this timespan, else fall back to api_url if configured
          local - local archive data only, never call api_url
          api   - always call api_url, ignore local data
          none  - tile hidden

        Deliberately generic: Vane's core never hardcodes a specific
        provider (e.g. ontladingen.nl) — see THEME_PLAN.md "Personal
        integrations are a separate plugin". A configured api_url must
        return Vane's fixed minimal JSON shape; adapting a provider's own
        response shape to that is the plugin's job, not this file's.
        Returns 'local' or 'none' for the template to drive via WeeWX's
        own $day.lightning_strike_count tag (proper unit-aware aggregation);
        'api' data (if any) is set on self._vane_lightning_api instead,
        since it doesn't come through WeeWX's unit system at all.
        """
        self._vane_lightning_api = None
        cfg = self.generator.skin_dict.get("Vane", {}).get("Lightning", {})
        source = cfg.get("source", "auto")

        if source == "none":
            return "none"

        if source in ("auto", "local"):
            has_local = False
            try:
                row = db_manager.getSql(
                    "SELECT 1 FROM %s WHERE dateTime > ? AND dateTime <= ? "
                    "AND lightning_strike_count IS NOT NULL LIMIT 1" % db_manager.table_name,
                    (timespan.start, timespan.stop))
                has_local = row is not None
            except Exception as e:
                log.info("Vane: local lightning check failed: %s", e)
            if has_local:
                return "local"
            if source == "local":
                return "none"

        # source == 'api', or 'auto' falling back after no local data
        api_url = (cfg.get("api_url") or "").strip()
        if not api_url:
            return "none"
        self._vane_lightning_api = self._fetch_lightning_api(
            api_url, cfg.get("api_timeout", "5"))
        return "api" if self._vane_lightning_api else "none"

    @staticmethod
    def _fetch_lightning_api(url, timeout):
        """GETs `url` and expects a JSON body of the shape
        {"strikes": <int>, "avg_distance_km": <float or null>} — Vane's
        fixed, provider-agnostic contract (see _lightning_mode)."""
        try:
            with urllib.request.urlopen(url, timeout=float(timeout)) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return {
                "strikes": int(data.get("strikes", 0)),
                "avg_distance_km": data.get("avg_distance_km"),
            }
        except Exception as e:
            log.info("Vane: lightning api_url fetch failed: %s", e)
            return None

    def _mqtt_config_json(self):
        """Builds the window.VANE_MQTT config as a JSON string, so
        broker_ws_url/username/password from skin.conf land in the page
        safely encoded instead of being spliced into a JS string literal
        by Cheetah (which doesn't escape quotes or `</script>`)."""
        vane_config = self.generator.skin_dict.get("Vane", {})
        mqtt_config = vane_config.get("MQTT", {})
        if str(mqtt_config.get("enable", "false")).lower() != "true":
            return None

        payload = {
            "enable": True,
            "brokerWsUrl": mqtt_config.get("broker_ws_url", ""),
            "topic": mqtt_config.get("topic", ""),
            "username": mqtt_config.get("username", ""),
            "password": mqtt_config.get("password", ""),
        }
        # json.dumps doesn't escape '/', so a broker URL or password
        # containing "</script>" could still break out of the <script>
        # block; escape that sequence explicitly.
        return json.dumps(payload).replace("</", "<\\/")

    def _language_name(self, lcode):
        """Display name for the language <select> — skin.conf
        [Vane][[LanguageNames]] wins when it has an entry (override, or a
        code the built-in LANGUAGE_NAMES table doesn't know at all),
        otherwise the built-in table, otherwise just the bare code
        uppercased (still functional, just less pretty) rather than
        erroring out for a language nobody's added a name for yet."""
        vane_config = self.generator.skin_dict.get("Vane", {})
        override = vane_config.get("LanguageNames", {})
        if lcode in override:
            return override[lcode]
        return LANGUAGE_NAMES.get(lcode, lcode.upper())

    @staticmethod
    def _language_flag(lcode):
        """Flag-icons country code for lcode's flag icon (see FLAG_CODES),
        or None if this language has no flag mapping — the template treats
        that as "skip the icon", not an error, so an unmapped custom
        language degrades to text-only rather than breaking."""
        return FLAG_CODES.get(lcode)

    def _dashboard_plugins_html(self):
        """Reads plugins/<name>.inc for each name in skin.conf
        [Vane][[Plugins]] dashboard_plugins, silently skipping any name
        whose file doesn't exist (no error — see THEME_PLAN.md "Personal
        integrations are a separate plugin": Vane's core ships this
        mechanism and an empty slot, never a concrete plugin file).

        Read directly here rather than via Cheetah's #include, which
        can't conditionally include a file based on os.path.exists()
        without extra imports of its own — this keeps the template side
        a single #if/$var pair instead of an untested Cheetah construct.
        """
        vane_config = self.generator.skin_dict.get("Vane", {})
        names_raw = vane_config.get("Plugins", {}).get("dashboard_plugins", "")
        names = [n.strip() for n in names_raw.split(",") if n.strip()]
        if not names:
            return ""

        skin_dir = os.path.join(
            self.generator.config_dict["WEEWX_ROOT"],
            self.generator.config_dict["StdReport"]["SKIN_ROOT"],
            self.generator.skin_dict.get("skin", "Vane"))

        parts = []
        for name in names:
            inc_path = os.path.join(skin_dir, "plugins", "%s.inc" % name)
            try:
                with open(inc_path, "r", encoding="utf-8") as f:
                    parts.append(f.read())
            except OSError:
                log.info("Vane: dashboard plugin '%s' not found (%s), skipping",
                          name, inc_path)
        return "\n".join(parts)

    # Fields covered by the live-update path (dashboard polling/MQTT, see
    # static/js/dashboard-live.js): only genuinely instantaneous readings
    # that a single archive record naturally provides. Daily aggregates
    # (rain today, pressure trend, sun/lightning) deliberately stay on
    # the normal per-archive-interval full-page regeneration instead —
    # they don't need second-level freshness and correctly computing
    # them here would mean re-querying spans that $day/$trend already
    # handle properly in the template.
    _LIVE_FIELDS = [
        ("outTemp", "%.1f"),
        ("appTemp", "%.1f"),
        ("outHumidity", "%.0f"),
        ("barometer", "%.1f"),
        ("windSpeed", "%.0f"),
        ("windGust", "%.0f"),
        ("UV", "%.0f"),
        ("radiation", "%.0f"),
        ("luminosity", "%.0f"),
    ]

    def _current_conditions_json(self, record):
        """Pre-formatted current-conditions values for the dashboard's
        live polling/MQTT update path. Built here (not directly in
        data/current.json.tmpl) so the exact same ValueHelper.format()
        calls run as in index.html.tmpl — a live update must render
        identically to a full page regeneration, not a JS
        reimplementation of the formatting/unit-conversion rules."""
        if not record:
            return "{}"

        out = {"generated": record.get("dateTime")}
        for key, format_string in self._LIVE_FIELDS:
            if record.get(key) is None:
                out[key] = None
                continue
            helper = weewx.units.ValueHelper(
                weewx.units.as_value_tuple(record, key),
                context="current",
                formatter=self.generator.formatter,
                converter=self.generator.converter,
            )
            out[key] = helper.format(add_label=False, format_string=format_string)

        wind_dir = record.get("windDir")
        out["windDirCompass"] = None
        if wind_dir is not None:
            out["windDirCompass"] = weewx.units.ValueHelper(
                (wind_dir, "degree_compass", "group_direction"),
                context="current",
                formatter=self.generator.formatter,
                converter=self.generator.converter,
            ).ordinal_compass()

        return json.dumps(out)

    def _almanac_at(self, ts):
        """A fresh weewx.almanac.Almanac for an arbitrary timestamp — the
        built-in $almanac tag (weewx.cheetahgenerator.Almanac) is always
        pinned to the report's generation time, so anything needing a
        DIFFERENT day (e.g. a full year of day lengths) has to build its
        own instance the same way that class does internally."""
        altitude_m = weewx.units.convert(self.generator.stn_info.altitude_vt, "meter")[0]
        return weewx.almanac.Almanac(
            ts,
            self.generator.stn_info.latitude_f,
            self.generator.stn_info.longitude_f,
            altitude=altitude_m)

    def _sun_arc_data(self, timespan):
        """Real sun-elevation arc for today, sampled between sunrise and
        sunset (not a stylized generic dome — the whole point of this
        card is to show today's *actual* sun path, including where the
        sun genuinely is right now). Cheap enough not to bother thinning:
        365 full days of rise/set benchmarked at ~30ms, ~50 altitude
        samples for one day is negligible in comparison."""
        now = timespan.stop
        alm = self._almanac_at(now)
        rise = alm.sun.rise.raw
        set_ = alm.sun.set.raw
        if rise is None or set_ is None or set_ <= rise:
            return {"has_data": False}

        n = 48
        samples = []
        for i in range(n + 1):
            t = rise + (set_ - rise) * i / n
            samples.append((t, self._almanac_at(t).sun.alt))
        peak_alt = max(alt for _, alt in samples)
        peak_alt = max(peak_alt, 1.0)  # guard against div-by-zero at very low sun angles

        width, height, pad_top = 600.0, 200.0, 20.0
        baseline_y = height - pad_top

        def point(t, alt):
            x = (t - rise) / (set_ - rise) * width
            y = baseline_y - max(alt, 0.0) / peak_alt * (baseline_y - pad_top)
            return x, y

        path_d = "M" + " L".join("%.1f,%.1f" % point(t, a) for t, a in samples)

        dot = None
        if rise <= now <= set_:
            now_alt = self._almanac_at(now).sun.alt
            x, y = point(now, now_alt)
            dot = {"x": round(x, 1), "y": round(y, 1)}

        transit = alm.sun.transit.raw
        peak_altitude = (int(round(self._almanac_at(transit).sun.alt, 0))
                          if transit is not None else None)

        return {
            "has_data": True,
            "path_d": path_d,
            "width": width,
            "height": height,
            "baseline_y": baseline_y,
            "dot": dot,
            "peak_altitude": peak_altitude,
        }

    # (attribute name on Almanac, "started" gettext key, "event name"
    # gettext key) — two separate whole-phrase keys per season since
    # word order/compounding differs by language (Dutch "Winterzonnewende"
    # is one compound word, English "Winter solstice" is two — these
    # can't be built by concatenating a season name with a translated
    # "equinox"/"solstice" word). Northern-hemisphere naming; a Southern-
    # hemisphere station gets correct dates with swapped season names,
    # which is a lang/*.conf labeling concern, not something this code
    # needs to branch on.
    _SEASON_EVENTS = [
        ("vernal_equinox", "Spring started", "Spring equinox"),
        ("summer_solstice", "Summer started", "Summer solstice"),
        ("autumnal_equinox", "Autumn started", "Autumn equinox"),
        ("winter_solstice", "Winter started", "Winter solstice"),
    ]

    def _season_events(self, timespan):
        """Which season most recently started, and which starts next —
        picked generically (closest past / closest future event) rather
        than assuming a specific current season, so this works the same
        in any hemisphere or time of year."""
        alm = self._almanac_at(timespan.stop)
        now = timespan.stop

        past = []
        future = []
        for attr, started_label, event_label in self._SEASON_EVENTS:
            prev_vh = getattr(alm, "previous_" + attr)
            next_vh = getattr(alm, "next_" + attr)
            if prev_vh.raw is not None:
                past.append((prev_vh.raw, started_label))
            if next_vh.raw is not None:
                future.append((next_vh.raw, event_label))

        most_recent_past = max(past, key=lambda p: p[0]) if past else None
        nearest_future = min(future, key=lambda f: f[0]) if future else None

        date_format = self.generator.skin_dict.get("Vane", {}).get(
            "DateFormats", {}).get("archive_day", "%m-%d")

        return {
            "past_date_str": (time.strftime(date_format, time.localtime(most_recent_past[0]))
                               if most_recent_past else None),
            "past_time_str": (time.strftime("%H:%M", time.localtime(most_recent_past[0]))
                               if most_recent_past else None),
            "past_label": most_recent_past[1] if most_recent_past else None,
            "future_date_str": (time.strftime(date_format, time.localtime(nearest_future[0]))
                                 if nearest_future else None),
            "future_time_str": (time.strftime("%H:%M", time.localtime(nearest_future[0]))
                                 if nearest_future else None),
            "future_label": nearest_future[1] if nearest_future else None,
            "future_days": (round((nearest_future[0] - now) / 86400.0)
                             if nearest_future else None),
        }

    def _day_length_year_data(self, timespan):
        """Day length (sunrise to sunset) for every day of the current
        calendar year — the actual informative content of the
        day-length-through-the-year chart, so (unlike the sun-arc's
        decorative dome) this one needs the real per-day computation,
        not a stylized shape. Benchmarked at ~30ms for 365 days
        (weewx.almanac is a thin, fast pyephem wrapper), so no need to
        thin the sampling for performance."""
        now = timespan.stop
        lat = self.generator.stn_info.latitude_f
        lon = self.generator.stn_info.longitude_f
        altitude_m = weewx.units.convert(self.generator.stn_info.altitude_vt, "meter")[0]

        now_local = time.localtime(now)
        year = now_local.tm_year
        is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        n_days = 366 if is_leap else 365
        # Local noon on Jan 1st, so DST transitions later in the year
        # can't shift a given day's index by falling on the wrong side
        # of midnight.
        jan1_noon = time.mktime((year, 1, 1, 12, 0, 0, 0, 0, -1))

        lengths_hours = []
        for i in range(n_days):
            alm = weewx.almanac.Almanac(jan1_noon + i * 86400, lat, lon, altitude=altitude_m)
            rise = alm.sun.rise.raw
            set_ = alm.sun.set.raw
            if rise is not None and set_ is not None and set_ > rise:
                lengths_hours.append((set_ - rise) / 3600.0)
            else:
                # Polar day/night edge case at extreme latitudes — no
                # sunrise/sunset that day.
                lengths_hours.append(0.0)

        max_hours = max(lengths_hours)
        min_hours = min(lengths_hours)
        max_i = lengths_hours.index(max_hours)
        min_i = lengths_hours.index(min_hours)

        today_i = min(now_local.tm_yday - 1, n_days - 1)
        today_hours = lengths_hours[today_i]
        yesterday_hours = lengths_hours[today_i - 1] if today_i > 0 else lengths_hours[-1]
        delta_seconds = (today_hours - yesterday_hours) * 3600.0

        width, height, pad_top = 600.0, 160.0, 12.0
        usable_h = height - pad_top

        def point(i, hours):
            x = i / (n_days - 1) * width
            y = pad_top + usable_h * (1 - hours / max_hours) if max_hours else height
            return x, y

        pts = [point(i, h) for i, h in enumerate(lengths_hours)]
        path_d = "M" + " L".join("%.1f,%.1f" % p for p in pts)
        area_d = path_d + " L%.1f,%.1f L0,%.1f Z" % (width, height, height)
        today_x, today_y = point(today_i, today_hours)

        def hm(hours):
            h = int(hours)
            m = int(round((hours - h) * 60))
            if m == 60:
                h, m = h + 1, 0
            return h, m

        today_h, today_m = hm(today_hours)
        max_h, max_m = hm(max_hours)
        min_h, min_m = hm(min_hours)
        delta_sign = "-" if delta_seconds < 0 else "+"
        delta_m, delta_s = divmod(int(round(abs(delta_seconds))), 60)

        date_format = self.generator.skin_dict.get("Vane", {}).get(
            "DateFormats", {}).get("archive_day", "%m-%d")

        return {
            "path_d": path_d,
            "area_d": area_d,
            "width": width,
            "height": height,
            "today_x": round(today_x, 1),
            "today_y": round(today_y, 1),
            # Percentage position for an HTML (not SVG) marker dot — the
            # chart's SVG uses preserveAspectRatio="none" (fixed height,
            # full-width stretch), which scales x/y non-uniformly and
            # turns an SVG <circle> into a visible ellipse. A plain HTML
            # div positioned by percentage and sized in real pixels stays
            # perfectly round regardless of that stretch.
            "today_x_pct": round(100.0 * today_x / width, 2),
            "today_y_pct": round(100.0 * today_y / height, 2),
            "today_h": today_h,
            "today_m": today_m,
            "delta_sign": delta_sign,
            "delta_m": delta_m,
            "delta_s": delta_s,
            "max_h": max_h,
            "max_m": max_m,
            "max_date_str": time.strftime(date_format, time.localtime(jan1_noon + max_i * 86400)),
            "min_h": min_h,
            "min_m": min_m,
            "min_date_str": time.strftime(date_format, time.localtime(jan1_noon + min_i * 86400)),
        }

    MOON_ICONS = [
        "moon-new", "moon-waxing-crescent", "moon-first-quarter",
        "moon-waxing-gibbous", "moon-full", "moon-waning-gibbous",
        "moon-last-quarter", "moon-waning-crescent",
    ]

    @classmethod
    def _moon_icon(cls, moon_index):
        """moon_index comes from $almanac.moon_index (0-7, language-
        independent — don't parse the translated $almanac.moon_phase
        text)."""
        try:
            return cls.MOON_ICONS[int(moon_index) & 7]
        except (TypeError, ValueError):
            return "moon-full"

    def _run_command(self, cmd, timeout=5):
        """Runs an arbitrary shell command configured in skin.conf and
        returns its stdout, or None on any failure (not configured,
        missing binary, timeout, non-zero exit). Vane's core only ever
        parses the OUTPUT format of these commands, never assumes what
        the command itself is (journalctl, vcgencmd, tail, ...) — same
        provider-agnostic pattern as [Vane][[Lightning]] api_url and
        [Vane][[MQTT]] broker_ws_url: the specific host/OS integration
        is something the installer configures, not something the
        publishable skin hardcodes."""
        if not cmd:
            return None
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                log.info("Vane: telemetry command failed (rc=%s): %s", result.returncode, cmd)
                return None
            return result.stdout
        except Exception as e:
            log.info("Vane: telemetry command error running '%s': %s", cmd, e)
            return None

    # WeeWX's own standard log lines for StdRESTful uploaders (see
    # weewx/restx.py RESTThread — every uploader, WOW/Wunderground/
    # PWSweather/Windy/CWOP/..., logs through this same base class), not
    # a format Vane invents or ties to one specific provider.
    _RESTX_PUBLISHED_RE = re.compile(r'(\S+): Published record\b')
    # Matches weeutil.weeutil.timestamp_to_string()'s exact format
    # ("2026-09-29 03:30:00 CEST (1790645700)") explicitly, rather than
    # a generic "up to the last colon" — the record's own timestamp
    # contains colons too, and so can the failure reason itself (e.g.
    # "HTTP Error 503: Service Unavailable"), so neither the first nor
    # the last colon in the line reliably marks the boundary.
    _RESTX_FAILED_RE = re.compile(
        r'(\S+): Failed to publish record '
        r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \S+ \(\d+\):\s*(.+)$')

    def _telemetry_services(self):
        """Parses recent WeeWX log lines (skin.conf [Vane][[Telemetry]]
        log_command — fully generic, see _run_command) for per-service
        upload status, and keeps the same raw lines for the system-log
        display. Both are simply absent (no error) if log_command isn't
        configured or the command fails."""
        cfg = self.generator.skin_dict.get("Vane", {}).get("Telemetry", {})
        text = self._run_command((cfg.get("log_command") or "").strip())
        if text is None:
            return {"has_data": False, "services": [], "log_lines": []}

        max_lines = int(cfg.get("log_max_lines", 12))
        lines = [l for l in text.splitlines() if l.strip()]

        services = {}
        for line in lines:
            m = self._RESTX_FAILED_RE.search(line)
            if m:
                services[m.group(1)] = {"ok": False, "detail": m.group(2).strip()}
                continue
            m = self._RESTX_PUBLISHED_RE.search(line)
            if m:
                services[m.group(1)] = {"ok": True, "detail": None}

        service_list = [{"name": name, "ok": info["ok"], "detail": info["detail"]}
                         for name, info in sorted(services.items())]

        return {
            "has_data": True,
            "services": service_list,
            "log_lines": lines[-max_lines:] if max_lines > 0 else lines,
        }

    _FIRST_NUMBER_RE = re.compile(r'[-+]?\d*\.?\d+')

    def _power_voltage(self):
        """Reads a single voltage number from skin.conf
        [Vane][[Telemetry]] power_voltage_command output — deliberately
        just 'run this command, extract the first number', not tied to
        any specific board (Raspberry Pi vcgencmd, or anything else the
        installer's own hardware provides)."""
        cfg = self.generator.skin_dict.get("Vane", {}).get("Telemetry", {})
        text = self._run_command((cfg.get("power_voltage_command") or "").strip())
        if text is None:
            return None
        m = self._FIRST_NUMBER_RE.search(text)
        return float(m.group(0)) if m else None

    def _storage_info(self):
        """Database file size + host disk usage — pure Python stdlib
        (os.path/shutil), portable across OSes, unlike the log/power
        commands above. Only meaningful for a SQLite binding (a file);
        gracefully returns None for MySQL/other backends, where a
        single 'database file size' doesn't apply."""
        try:
            config_dict = self.generator.config_dict
            binding = self.generator.skin_dict.get("data_binding", "wx_binding")
            db_key = config_dict["DataBindings"][binding]["database"]
            db_section = config_dict["Databases"][db_key]
            db_type = db_section.get("database_type", "SQLite")
            if "sqlite" not in db_type.lower():
                return None
            sqlite_root = config_dict["DatabaseTypes"][db_type]["SQLITE_ROOT"]
            db_path = os.path.join(config_dict["WEEWX_ROOT"], sqlite_root,
                                    db_section["database_name"])
            size_mb = os.path.getsize(db_path) / (1024.0 * 1024.0)
            total, used, _free = shutil.disk_usage(os.path.dirname(db_path))
            return {
                "db_size_mb": size_mb,
                "disk_total_gb": total / (1024.0 ** 3),
                "disk_used_pct": (used / total * 100.0) if total else None,
            }
        except Exception as e:
            log.info("Vane: storage info unavailable: %s", e)
            return None

    @staticmethod
    def _record_count(db_manager):
        try:
            row = db_manager.getSql("SELECT COUNT(*) FROM %s" % db_manager.table_name)
            return row[0] if row else None
        except Exception:
            return None
