/*
 * Vane — Graphs page: fetches data/*.json and renders it with uPlot.
 * Colors are read at runtime from the CSS custom properties (not
 * hardcoded), so theme/accent color are followed automatically.
 */
(function () {
  "use strict";

  function cssVar(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function setStatus(msg) {
    var el = document.getElementById("vane-graph-status");
    if (el) el.textContent = msg;
  }

  var charts = {};

  function baseAxes() {
    var muted = cssVar("--text-muted", "#94a3b8");
    var grid = cssVar("--grid", "rgba(148,163,184,.12)");
    return [
      { stroke: muted, grid: { stroke: grid } },
      { stroke: muted, grid: { stroke: grid } }
    ];
  }

  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  // uPlot's own default legend formatting is locale-agnostic raw
  // numbers (e.g. "20.294...") and a 12-hour AM/PM time — neither
  // matches the NL 24-hour convention used everywhere else in Vane
  // (see e.g. "Bijgewerkt 18:15:08" on the Dashboard), so both get an
  // explicit formatter instead of trusting the uPlot/browser default.
  function fmtLegendTime(u, v) {
    if (v == null) return "--";
    var d = new Date(v * 1000);
    return pad2(d.getDate()) + "-" + pad2(d.getMonth() + 1) + "-" + d.getFullYear() +
      " " + pad2(d.getHours()) + ":" + pad2(d.getMinutes());
  }

  function fmtLegendValue(u, v) {
    return v == null ? "--" : v.toFixed(1);
  }

  function renderLineChart(key, hostId, series) {
    var host = document.getElementById(hostId);
    if (!host || typeof uPlot !== "function") return;
    if (!series.length || !series[0][0] || !series[0][0].length) return;

    var opts = {
      width: host.clientWidth || 560,
      height: 220,
      scales: { x: { time: true } },
      axes: baseAxes(),
      series: [{ value: fmtLegendTime }].concat(series.map(function (s) {
        var o = s[1];
        if (o.value === undefined) o.value = fmtLegendValue;
        return o;
      }))
    };
    var data = [series[0][0][0]].concat(series.map(function (s) { return s[0][1]; }));

    if (charts[key]) { try { charts[key].destroy(); } catch (e) {} }
    charts[key] = new uPlot(opts, data, host);
  }

  function seriesDef(xy, opts) {
    return [xy, opts];
  }

  function renderAll(json) {
    var accent = cssVar("--accent-primary", "#2f8bff");
    var wind = cssVar("--accent-wind", "#fb923c");
    var storm = cssVar("--accent-storm", "#7c5cff");
    var muted = cssVar("--text-muted", "#94a3b8");

    renderLineChart("temp", "vane-temp-chart", [
      seriesDef(json.temp, { label: "Buiten", stroke: accent, width: 2, fill: accent + "26" }),
      seriesDef(json.dewpoint, { label: "Dauwpunt", stroke: muted, width: 1.5, dash: [4, 4], points: { show: false } })
    ]);

    renderLineChart("pressure", "vane-pressure-chart", [
      seriesDef(json.barometer, { label: "Luchtdruk", stroke: accent, width: 2, fill: accent + "1a", points: { show: false } })
    ]);

    renderLineChart("wind", "vane-wind-chart", [
      seriesDef(json.windSpeed, { label: "Gemiddeld", stroke: wind, width: 2, points: { show: false } }),
      seriesDef(json.windGust, { label: "Stoten", stroke: wind, width: 1.5, dash: [4, 4], points: { show: false } })
    ]);

    renderLineChart("rain", "vane-rain-chart", [
      seriesDef(json.rain, { label: "Neerslag (30 min)", stroke: storm, width: 2, fill: storm + "33", points: { show: false } })
    ]);

    renderLineChart("humidity", "vane-humidity-chart", [
      seriesDef(json.humidity, { label: "Vocht", stroke: accent, width: 2, fill: accent + "1a", points: { show: false } })
    ]);

    // Not combined with radiation here on purpose: UV (0-11ish) and
    // radiation (0-1000+ W/m²) are wildly different scales — plotted on
    // the same y-axis, UV would flatten to an invisible line at the
    // bottom. Radiation is still in the JSON (data/*.json.tmpl) for a
    // future dedicated chart, just not paired with UV on this one.
    renderLineChart("uv", "vane-uv-chart", [
      seriesDef(json.uv, { label: "UV-index", stroke: wind, width: 2, points: { show: false } })
    ]);

    renderLineChart("radiation", "vane-radiation-chart", [
      seriesDef(json.radiation, { label: "Straling", stroke: wind, width: 2, fill: wind + "1a", points: { show: false } })
    ]);

    renderLineChart("cloudbase", "vane-cloudbase-chart", [
      seriesDef(json.cloudbase, { label: "Wolkenbasis", stroke: muted, width: 2, points: { show: false } })
    ]);

    renderLineChart("et", "vane-et-chart", [
      seriesDef(json.et, { label: "ET", stroke: storm, width: 2, fill: storm + "33", points: { show: false } })
    ]);
  }

  var currentPeriod = "day";
  var currentFile = "data/day.json";
  var pollTimer = null;
  var lastJson = null;

  // Client-side JS never goes through WeeWX's $gettext() (that's a
  // server-side Cheetah tag) — so the handful of status strings this
  // script shows get their own tiny lookup table instead. The active
  // language code is injected by the template as window.VANE_LANG (see
  // $Vane.lang_code); defaults to English if that's ever missing.
  var LANG = (window.VANE_LANG || "en");
  var LOCALE = LANG === "nl" ? "nl-NL" : "en-US";
  var STRINGS = {
    en: { loading: "Loading…", updated: "Updated ", loadError: "Could not load " },
    nl: { loading: "Laden…", updated: "Bijgewerkt ", loadError: "Kon " }
  }[LANG] || { loading: "Loading…", updated: "Updated ", loadError: "Could not load " };

  function load() {
    var file = currentFile;
    setStatus(STRINGS.loading);
    fetch(file, { cache: "no-store" })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (json) {
        lastJson = json;
        renderAll(json);
        setStatus(STRINGS.updated + new Date().toLocaleTimeString(LOCALE));
      })
      .catch(function (err) {
        setStatus(STRINGS.loadError + file + " (" + err.message + ")");
      });
  }

  function toCsv(json) {
    var rows = [["metric", "timestamp_utc", "value"]];
    ["temp", "dewpoint", "barometer", "windSpeed", "windGust", "rain"].forEach(function (key) {
      if (!json[key]) return;
      var xs = json[key][0], ys = json[key][1];
      for (var i = 0; i < xs.length; i++) {
        rows.push([key, new Date(xs[i] * 1000).toISOString(), ys[i] === null ? "" : ys[i]]);
      }
    });
    return rows.map(function (r) { return r.join(","); }).join("\n");
  }

  function initCsvExport() {
    var btn = document.getElementById("vane-csv-export");
    if (!btn) return;
    btn.addEventListener("click", function () {
      if (!lastJson) return;
      var blob = new Blob([toCsv(lastJson)], { type: "text/csv;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = "vane-" + (lastJson.period || currentPeriod) + ".csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    });
  }

  function initMonthPicker() {
    var input = document.getElementById("vane-month-picker");
    if (!input) return;
    input.addEventListener("change", function () {
      if (!input.value) return;
      document.querySelectorAll(".period-btn").forEach(function (b) { b.classList.remove("active"); });
      currentPeriod = "archive-month";
      currentFile = "data/archive/" + input.value + ".json";
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
      load();
    });
  }

  function schedulePoll() {
    if (pollTimer) clearInterval(pollTimer);
    // Only the day period is "live" enough to refresh every minute;
    // week/month/year/all change too little to keep reloading.
    if (currentPeriod === "day") pollTimer = setInterval(load, 60000);
  }

  function initPeriodSelector() {
    var btns = document.querySelectorAll(".period-btn");
    btns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        btns.forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        currentPeriod = btn.dataset.period;
        currentFile = "data/" + currentPeriod + ".json";
        var picker = document.getElementById("vane-month-picker");
        if (picker) picker.value = "";
        load();
        schedulePoll();
      });
    });
  }

  function init() {
    initPeriodSelector();
    initMonthPicker();
    initCsvExport();
    load();
    schedulePoll();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
