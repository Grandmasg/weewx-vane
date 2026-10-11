#!/usr/bin/env python3
"""Converts Vane's animated SVG icons into Lottie JSON.

The hand-made SVGs in skins/Vane/static/img/icons/ are the single source of
truth: same shapes, same gradients, same SMIL motion. This script derives the
Lottie files in skins/Vane/static/lottie/ from them, so the two can never
drift apart in style again (they did once: line-style Lottie on top of the
filled SVG set).

    pip install lottie          # python-lottie, dev-only dependency
    python tools/svg2lottie.py  # rebuilds every icon listed in ICONS/SEASONS

How it works: python-lottie imports the static shapes/gradients, but its SMIL
support is too limited for these files (no `values=`, no animateTransform).
So we strip the SMIL first, wrap every animated element in its own <g>, let
python-lottie import that, and then write our own keyframes onto the
transform of each wrapper group:

- animateTransform translate/rotate/scale -> position/rotation/scale
- animate opacity                         -> group opacity
- animate r (circle)                      -> scale around the centre
- animate y+height (rect)                 -> vertical scale around the
                                             fixed bottom edge
- animate stroke-dasharray "dash,gap"     -> Trim Paths (draw-on line)
- calcMode="spline" keySplines            -> Lottie bezier easing
- begin= offsets                          -> phase shift inside the loop

- feDropShadow filter                     -> "vaneShadow" key in the JSON,
                                             applied by vane-lottie.js as a
                                             CSS drop-shadow() (lottie_light
                                             can't render SVG filters)

Not converted: <text> (draw letters as paths, see uv-index.svg) and CSS
media queries inside an SVG (barometer's light/dark face — the Lottie keeps
the dark one).
"""

import copy
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction

from lottie.parsers.svg import parse_svg_etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG_DIR = os.path.join(ROOT, "skins", "Vane", "static", "img", "icons")
SEASON_SVG_DIR = os.path.join(ROOT, "skins", "Vane", "static", "img", "seasons")
OUT_ICONS = os.path.join(ROOT, "skins", "Vane", "static", "lottie", "icons")
OUT_SEASONS = os.path.join(ROOT, "skins", "Vane", "static", "lottie", "seasons")

ICONS = [
    "barometer", "clear-day", "clear-night", "cloudy", "drizzle", "fog",
    "hail", "humidity", "overcast", "partly-cloudy-day",
    "partly-cloudy-night", "rain", "raindrops", "sleet", "snow",
    "solar-radiation", "sunrise", "sunset", "thermometer", "thunderstorms",
    "uv-index", "wind",
]
SEASONS = ["spring", "summer", "autumn", "winter"]

FPS = 30
MAX_LOOP_S = 12  # longer common loops get their durations snapped to fit

SVG_NS = "http://www.w3.org/2000/svg"
ANIM_TAGS = ("animate", "animateTransform")


def _tag(el):
    return el.tag.split("}", 1)[-1]


def _floats(s):
    return [float(x) for x in re.split(r"[\s,]+", s.strip()) if x]


def _clock(value):
    """SMIL clock value -> seconds."""
    if not value:
        return 0.0
    value = value.strip()
    if value.endswith("ms"):
        return float(value[:-2]) / 1000
    if value.endswith("s"):
        return float(value[:-1])
    return float(value)


# ---------------------------------------------------------------------------
# 1. Strip SMIL from the SVG, remembering it per wrapper group
# ---------------------------------------------------------------------------

def extract_animations(tree):
    """Returns {wrapper_id: (element_copy, [anim dicts])} and mutates the tree
    so every animated element sits inside <g id=wrapper_id>."""
    root = tree.getroot()
    parents = {c: p for p in root.iter() for c in p}
    found = {}
    counter = 0
    for el in list(root.iter()):
        anims = [c for c in el if _tag(c) in ANIM_TAGS]
        if not anims:
            continue
        counter += 1
        wid = "vaneanim%d" % counter
        specs = []
        for a in anims:
            spec = dict(a.attrib)
            spec["_tag"] = _tag(a)
            specs.append(spec)
            el.remove(a)
        # animateTransform (additive="replace", the default) REPLACES the
        # element's own transform attribute while it runs.
        if any(s["_tag"] == "animateTransform" and s.get("additive") != "sum"
               for s in specs):
            el.attrib.pop("transform", None)
        parent = parents[el]
        idx = list(parent).index(el)
        wrapper = ET.Element("{%s}g" % SVG_NS, {"id": wid})
        parent.remove(el)
        wrapper.append(el)
        parent.insert(idx, wrapper)
        parents[el] = wrapper
        parents[wrapper] = parent
        found[wid] = (copy.deepcopy(el), specs)
    # python-lottie can't read <style>, and media queries can't map anyway.
    for el in list(root.iter()):
        for c in list(el):
            if _tag(c) == "style":
                el.remove(c)
    return found


# ---------------------------------------------------------------------------
# 2. Timing: one common loop length per icon
# ---------------------------------------------------------------------------

def loop_length(all_specs):
    durs = [_clock(s.get("dur", "0")) for s in all_specs if s.get("dur")]
    if not durs:
        return 3.0
    tenths = [max(1, round(d * 10)) for d in durs]
    lcm = 1
    for t in tenths:
        lcm = lcm * t // math.gcd(lcm, t)
    if lcm / 10 <= MAX_LOOP_S:
        return lcm / 10
    # Too long: use the longest duration, other durations get snapped to an
    # integer number of repeats inside it (see snap_dur).
    return max(durs)


def snap_dur(dur, loop):
    """Duration adjusted so a whole number of cycles fits the loop."""
    n = max(1, round(loop / dur))
    return loop / n


# ---------------------------------------------------------------------------
# 3. SMIL values -> Lottie keyframes
# ---------------------------------------------------------------------------

def parse_track(spec, kind):
    """Returns (values:list[list[float]], keytimes:list[float], easings)."""
    if "values" in spec:
        raw = [v for v in spec["values"].split(";") if v.strip()]
        values = [_floats(v) for v in raw]
    else:
        values = [_floats(spec["from"]), _floats(spec["to"])]
    n = len(values)
    if "keyTimes" in spec:
        keytimes = [float(x) for x in spec["keyTimes"].split(";") if x.strip()]
    else:
        keytimes = [i / (n - 1) for i in range(n)] if n > 1 else [0.0]
    easings = []
    if spec.get("calcMode") == "spline" and "keySplines" in spec:
        for seg in spec["keySplines"].split(";"):
            if seg.strip():
                easings.append(_floats(seg))
    while len(easings) < n - 1:
        easings.append([0, 0, 1, 1])
    return values, keytimes, easings


def keyframes(values, keytimes, easings, dur, begin, loop):
    """Builds Lottie keyframes covering [0, loop] frames, phase-shifted by
    `begin` and repeated every `dur` seconds."""
    kfs = []
    total = loop * FPS
    first_cycle = math.floor(-begin / dur) - 1
    k = first_cycle
    while True:
        start = (begin + k * dur) * FPS
        if start > total:
            break
        for i, v in enumerate(values):
            t = start + keytimes[i] * dur * FPS
            kf = {"t": round(t, 3), "s": v}
            if i < len(values) - 1:
                x1, y1, x2, y2 = easings[i]
                # Scalars, not 1-element lists: lottie-web applies a scalar
                # easing to every dimension, but a 1-element list only to
                # the first — 2-D scale/position then never moved.
                kf["o"] = {"x": x1, "y": y1}
                kf["i"] = {"x": x2, "y": y2}
            else:
                # Hold until the next cycle's first keyframe (same value in
                # these icons, so a seamless loop).
                kf["o"] = {"x": 0, "y": 0}
                kf["i"] = {"x": 1, "y": 1}
            kfs.append(kf)
        k += 1
    # The end of one cycle and the start of the next share a time. Same
    # value (most icons): keep one. Different value (e.g. rotate 0 -> 360):
    # SMIL jumps back instantly, so keep both with the end nudged a hair
    # earlier — collapsing them would wipe out the whole motion.
    out = []
    for kf in kfs:
        if out and abs(out[-1]["t"] - kf["t"]) < 1e-6:
            if out[-1]["s"] == kf["s"]:
                out[-1] = kf
                continue
            out[-1]["t"] = round(out[-1]["t"] - 0.01, 3)
        out.append(kf)
    return out


def animated(kfs):
    return {"a": 1, "k": kfs}


# ---------------------------------------------------------------------------
# 4. Apply tracks onto the wrapper group's transform
# ---------------------------------------------------------------------------

def find_group(shapes, name):
    for s in shapes:
        if s.get("ty") == "gr":
            if s.get("nm") == name:
                return s
            hit = find_group(s.get("it", []), name)
            if hit:
                return hit
    return None


def group_transform(group):
    for it in group["it"]:
        if it.get("ty") == "tr":
            return it
    tr = {"ty": "tr", "a": {"a": 0, "k": [0, 0]}, "p": {"a": 0, "k": [0, 0]},
          "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0},
          "o": {"a": 0, "k": 100}}
    group["it"].append(tr)
    return tr


def apply(group, element, specs, loop):
    tr = group_transform(group)
    tag = _tag(element)
    origin = None
    for spec in specs:
        to = spec.get("transform-origin")
        if to:
            origin = _floats(to)

    for spec in specs:
        dur = snap_dur(_clock(spec.get("dur", "1s")), loop)
        begin = _clock(spec.get("begin", "0s"))
        att = spec.get("attributeName")
        values, keytimes, easings = parse_track(spec, att)

        if spec["_tag"] == "animateTransform":
            kind = spec.get("type", "translate")
            if kind == "translate":
                vals = [[v[0], v[1] if len(v) > 1 else 0.0] for v in values]
                tr["p"] = animated(keyframes(vals, keytimes, easings, dur, begin, loop))
            elif kind == "rotate":
                cx, cy = (values[0][1], values[0][2]) if len(values[0]) >= 3 else (0, 0)
                tr["a"] = {"a": 0, "k": [cx, cy]}
                tr["p"] = {"a": 0, "k": [cx, cy]}
                vals = [[v[0]] for v in values]
                tr["r"] = animated(keyframes(vals, keytimes, easings, dur, begin, loop))
            elif kind == "scale":
                ox, oy = origin or (0, 0)
                tr["a"] = {"a": 0, "k": [ox, oy]}
                tr["p"] = {"a": 0, "k": [ox, oy]}
                vals = [[v[0] * 100, (v[1] if len(v) > 1 else v[0]) * 100] for v in values]
                tr["s"] = animated(keyframes(vals, keytimes, easings, dur, begin, loop))
        elif att == "opacity":
            vals = [[v[0] * 100] for v in values]
            tr["o"] = animated(keyframes(vals, keytimes, easings, dur, begin, loop))
        elif att == "r" and tag == "circle":
            r0 = float(element.get("r"))
            cx, cy = float(element.get("cx", 0)), float(element.get("cy", 0))
            tr["a"] = {"a": 0, "k": [cx, cy]}
            tr["p"] = {"a": 0, "k": [cx, cy]}
            vals = [[v[0] / r0 * 100, v[0] / r0 * 100] for v in values]
            tr["s"] = animated(keyframes(vals, keytimes, easings, dur, begin, loop))
        elif att == "height" and tag == "rect":
            # Paired with an inverse `y` animation in our icons (a column
            # growing from a fixed bottom edge) -> vertical scale about it.
            y0, h0 = float(element.get("y")), float(element.get("height"))
            x0, w0 = float(element.get("x", 0)), float(element.get("width", 0))
            bottom = y0 + h0
            tr["a"] = {"a": 0, "k": [x0 + w0 / 2, bottom]}
            tr["p"] = {"a": 0, "k": [x0 + w0 / 2, bottom]}
            vals = [[100, v[0] / h0 * 100] for v in values]
            tr["s"] = animated(keyframes(vals, keytimes, easings, dur, begin, loop))
        elif att == "y" and tag == "rect":
            pass  # covered by the height track above
        elif att == "stroke-dasharray":
            # "dash,gap" with dash+gap ~ path length is a draw-on line ->
            # Lottie Trim Paths, end = visible fraction. A trim modifier
            # acts on the shapes BEFORE it in the group, so it goes just
            # before the group's transform.
            vals = [[v[0] / (v[0] + v[1]) * 100 if (v[0] + v[1]) else 0] for v in values]
            trim = {"ty": "tm", "s": {"a": 0, "k": 0}, "o": {"a": 0, "k": 0}, "m": 1,
                    "e": animated(keyframes(vals, keytimes, easings, dur, begin, loop))}
            group["it"].insert(group["it"].index(tr), trim)
        else:
            print("    skipped: %s %s" % (spec["_tag"], att))


# ---------------------------------------------------------------------------
# 5. Convert one file
# ---------------------------------------------------------------------------

def drop_shadow(tree):
    """First feDropShadow actually referenced by a filter="url(#..)", as a
    dict for vane-lottie.js to apply as a CSS drop-shadow() on the Lottie
    host — lottie_light can't render SVG filters, and without the glow the
    Lottie looked flatter than the SVG it replaces."""
    root = tree.getroot()
    shadows = {}
    for f in root.iter():
        if _tag(f) != "filter":
            continue
        for c in f:
            if _tag(c) == "feDropShadow":
                shadows[f.get("id")] = {
                    "dx": float(c.get("dx", 0)), "dy": float(c.get("dy", 0)),
                    "blur": float(c.get("stdDeviation", 0)),
                    "color": c.get("flood-color", "#000000"),
                    "opacity": float(c.get("flood-opacity", 1)),
                }
    for el in root.iter():
        m = re.match(r"url\(#([^)]+)\)", el.get("filter", ""))
        if m and m.group(1) in shadows:
            return shadows[m.group(1)]
    return None


def convert(svg_path, out_path):
    ET.register_namespace("", SVG_NS)
    tree = ET.parse(svg_path)
    shadow = drop_shadow(tree)
    found = extract_animations(tree)
    all_specs = [s for _, specs in found.values() for s in specs]
    loop = loop_length(all_specs)

    anim = parse_svg_etree(tree)
    data = anim.to_dict()
    data["fr"] = FPS
    data["ip"] = 0
    data["op"] = round(loop * FPS)
    data["nm"] = os.path.splitext(os.path.basename(svg_path))[0]
    if shadow:
        # Not part of the Lottie format (players ignore unknown keys); read
        # by vane-lottie.js. Offsets/blur are in viewBox units.
        vb = _floats(tree.getroot().get("viewBox", "0 0 64 64"))
        shadow["viewbox"] = vb[2]
        data["vaneShadow"] = shadow
    for layer in data["layers"]:
        layer["ip"] = 0
        layer["op"] = data["op"]
        for wid, (element, specs) in found.items():
            group = find_group(layer.get("shapes", []), wid)
            if group is None:
                print("    wrapper %s not found" % wid)
                continue
            apply(group, element, specs, loop)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    return loop, len(found), os.path.getsize(out_path)


def main(names=None):
    jobs = [(os.path.join(SVG_DIR, n + ".svg"), os.path.join(OUT_ICONS, n + ".json"))
            for n in ICONS]
    jobs += [(os.path.join(SEASON_SVG_DIR, n + ".svg"), os.path.join(OUT_SEASONS, n + ".json"))
             for n in SEASONS]
    for src, dst in jobs:
        name = os.path.splitext(os.path.basename(src))[0]
        if names and name not in names:
            continue
        if not os.path.exists(src):
            print("%-22s MISSING %s" % (name, src))
            continue
        loop, n, size = convert(src, dst)
        print("%-22s loop %4.1fs  %2d animated  %6d bytes" % (name, loop, n, size))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
