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

  // Same idea as chartLabel() below, for the texts not tied to one chart:
  // translated by the template, on the status element.
  function statusText(key, fallback) {
    var el = document.getElementById("vane-graph-status");
    return (el && el.dataset[key]) || fallback;
  }

  var charts = {};

  function baseAxes() {
    var muted = cssVar("--text-muted", "#94a3b8");
    var grid = cssVar("--grid", "rgba(148,163,184,.12)");
    return [
      { stroke: muted, grid: { stroke: grid }, values: fmtAxisTime },
      { stroke: muted, grid: { stroke: grid } }
    ];
  }

  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  // The page's own language (<html lang>), so the browser formats dates
  // and month names correctly for any language without a table here.
  var LOCALE = document.documentElement.lang || undefined;

  // uPlot's default time axis is always English/US ("3pm", "11/6/26").
  function fmtAxisTime(u, splits, axisIdx, foundSpace, foundIncr) {
    var prevDay = null;
    return splits.map(function (s) {
      var d = new Date(s * 1000);
      if (foundIncr >= 28 * 86400) {
        return d.toLocaleDateString(LOCALE, { month: "short", year: "numeric" });
      }
      if (foundIncr >= 86400) {
        return d.toLocaleDateString(LOCALE, { day: "numeric", month: "short" });
      }
      var day = d.toDateString();
      var text = pad2(d.getHours()) + ":" + pad2(d.getMinutes());
      // Below the time, at the first tick and wherever a new day starts.
      if (day !== prevDay) {
        text += "\n" + d.toLocaleDateString(LOCALE, { day: "numeric", month: "short" });
        prevDay = day;
      }
      return text;
    });
  }

  // uPlot's own default legend formatting is locale-agnostic raw
  // numbers (e.g. "20.294...") and a 12-hour AM/PM time — neither
  // matches the NL 24-hour convention used everywhere else in Vane
  // (see e.g. "Bijgewerkt 18:15:08" on the Dashboard), so both get an
  // explicit formatter instead of trusting the uPlot/browser default.
  function fmtLegendTime(u, v) {
    if (v == null) return "--";
    var d = new Date(v * 1000);
    return d.toLocaleDateString(LOCALE) + " " + pad2(d.getHours()) + ":" + pad2(d.getMinutes());
  }

  // data-decimals on the chart host: inch and inHg need two decimals,
  // otherwise 0.03 in of rain shows as "0.0".
  function legendValueFormatter(decimals) {
    return function (u, v) {
      return v == null ? "--" : v.toFixed(decimals);
    };
  }

  function renderLineChart(key, hostId, series) {
    var host = document.getElementById(hostId);
    if (!host || typeof uPlot !== "function") return;
    if (!series.length || !series[0][0] || !series[0][0].length) return;
    var decimals = parseInt(host.dataset.decimals, 10);
    if (isNaN(decimals)) decimals = 1;

    var opts = {
      width: host.clientWidth || 560,
      height: 220,
      scales: { x: { time: true } },
      axes: baseAxes(),
      series: [{ label: statusText("time", "Time"), value: fmtLegendTime }].concat(series.map(function (s) {
        var o = s[1];
        if (o.value === undefined) o.value = legendValueFormatter(decimals);
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

  // Series labels are translated server-side by the template (see the
  // data-label-* attributes on each chart host in graphs.html.tmpl), so a
  // new language only needs its lang/*.conf entries — never a JS change.
  // The English fallbacks here only matter if a template is missing one.
  function chartLabel(hostId, key, fallback) {
    var host = document.getElementById(hostId);
    if (!host) return fallback;
    return host.dataset["label" + key.charAt(0).toUpperCase() + key.slice(1)] || fallback;
  }

  // Must match the aggregate_interval of "rain" in data/*.json.tmpl.
  function rainLabel() {
    if (currentPeriod === "day") return chartLabel("vane-rain-chart", "rain30m", "Rain per 30 min");
    if (currentPeriod === "year" || currentPeriod === "all") return chartLabel("vane-rain-chart", "rainDay", "Rain per day");
    return chartLabel("vane-rain-chart", "rainHour", "Rain per hour");
  }

  function renderAll(json) {
    var accent = cssVar("--accent-primary", "#2f8bff");
    var wind = cssVar("--accent-wind", "#fb923c");
    var storm = cssVar("--accent-storm", "#7c5cff");
    var muted = cssVar("--text-muted", "#94a3b8");

    renderLineChart("temp", "vane-temp-chart", [
      seriesDef(json.temp, { label: chartLabel("vane-temp-chart", "temp", "Outdoor"), stroke: accent, width: 2, fill: accent + "26" }),
      seriesDef(json.dewpoint, { label: chartLabel("vane-temp-chart", "dewpoint", "Dew point"), stroke: muted, width: 1.5, dash: [4, 4], points: { show: false } })
    ]);

    renderLineChart("pressure", "vane-pressure-chart", [
      seriesDef(json.barometer, { label: chartLabel("vane-pressure-chart", "barometer", "Pressure"), stroke: accent, width: 2, fill: accent + "1a", points: { show: false } })
    ]);

    renderLineChart("wind", "vane-wind-chart", [
      seriesDef(json.windSpeed, { label: chartLabel("vane-wind-chart", "windSpeed", "Average"), stroke: wind, width: 2, points: { show: false } }),
      seriesDef(json.windGust, { label: chartLabel("vane-wind-chart", "windGust", "Gusts"), stroke: wind, width: 1.5, dash: [4, 4], points: { show: false } })
    ]);

    renderLineChart("rain", "vane-rain-chart", [
      seriesDef(json.rain, { label: rainLabel(), stroke: storm, width: 2, fill: storm + "33", points: { show: false } })
    ]);

    renderLineChart("humidity", "vane-humidity-chart", [
      seriesDef(json.humidity, { label: chartLabel("vane-humidity-chart", "humidity", "Humidity"), stroke: accent, width: 2, fill: accent + "1a", points: { show: false } })
    ]);

    // Not combined with radiation here on purpose: UV (0-11ish) and
    // radiation (0-1000+ W/m²) are wildly different scales — plotted on
    // the same y-axis, UV would flatten to an invisible line at the
    // bottom. Radiation is still in the JSON (data/*.json.tmpl) for a
    // future dedicated chart, just not paired with UV on this one.
    renderLineChart("uv", "vane-uv-chart", [
      seriesDef(json.uv, { label: chartLabel("vane-uv-chart", "uv", "UV index"), stroke: wind, width: 2, points: { show: false } })
    ]);

    renderLineChart("radiation", "vane-radiation-chart", [
      seriesDef(json.radiation, { label: chartLabel("vane-radiation-chart", "radiation", "Radiation"), stroke: wind, width: 2, fill: wind + "1a", points: { show: false } })
    ]);

    renderLineChart("cloudbase", "vane-cloudbase-chart", [
      seriesDef(json.cloudbase, { label: chartLabel("vane-cloudbase-chart", "cloudbase", "Cloud base"), stroke: muted, width: 2, points: { show: false } })
    ]);

    renderLineChart("et", "vane-et-chart", [
      seriesDef(json.et, { label: chartLabel("vane-et-chart", "et", "Evapotranspiration"), stroke: storm, width: 2, fill: storm + "33", points: { show: false } })
    ]);
  }

  var currentPeriod = "day";
  var currentFile = "data/day.json";
  var pollTimer = null;
  var lastJson = null;

  function load() {
    var file = currentFile;
    setStatus(statusText("loading", "Loading…"));
    fetch(file, { cache: "no-store" })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (json) {
        lastJson = json;
        renderAll(json);
        var now = new Date();
        setStatus(statusText("updated", "Updated") + " " + pad2(now.getHours()) + ":" +
          pad2(now.getMinutes()) + ":" + pad2(now.getSeconds()));
      })
      .catch(function (err) {
        setStatus(statusText("loadError", "Could not load {file}").replace("{file}", file) +
          " (" + err.message + ")");
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

  // Charts get a fixed pixel width when drawn, so they must follow the
  // card when the window changes or a phone is rotated: otherwise a chart
  // drawn in landscape sticks out of its card in portrait.
  function initResize() {
    var timer = null;
    window.addEventListener("resize", function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        Object.keys(charts).forEach(function (key) {
          var host = charts[key].root.parentNode;
          if (host && host.clientWidth) {
            charts[key].setSize({ width: host.clientWidth, height: charts[key].height });
          }
        });
      }, 150);
    });
  }

  function init() {
    initResize();
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
