/*
 * Vane — Dashboard live updates. One updateDashboard(data) function fed by
 * either a fetch() poller (always on) or an MQTT subscription (opt-in, see
 * skin.conf [Vane][[MQTT]]) — this is the "MQTT-ready" architecture from
 * THEME_PLAN.md: adding MQTT later never meant touching the render logic,
 * only wiring a second caller of the same function.
 *
 * Contract: both the poller's data/current.json and any configured MQTT
 * topic must publish the same flat, pre-formatted JSON shape (see
 * vane_extras.py _current_conditions_json — e.g. {"outTemp": "21.4", ...}).
 * Vane's core never assumes a specific MQTT payload shape beyond this; a
 * weewx-mqtt setup publishing something else needs its own small adapter,
 * same "generic contract" pattern as skin.conf [Vane][[Lightning]] api_url.
 */
(function () {
  "use strict";

  function updateDashboard(data) {
    if (!data) return;
    var nodes = document.querySelectorAll("[data-live]");
    for (var i = 0; i < nodes.length; i++) {
      var key = nodes[i].getAttribute("data-live");
      var val = data[key];
      if (val !== null && val !== undefined) {
        nodes[i].textContent = val;
      }
    }
  }

  function startPolling(intervalMs) {
    function poll() {
      fetch("data/current.json", { cache: "no-store" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(updateDashboard)
        .catch(function () { /* next poll will retry, no user-facing error */ });
    }
    poll();
    setInterval(poll, intervalMs);
  }

  function startMqtt(cfg) {
    if (typeof mqtt === "undefined") return;
    var options = { protocolVersion: 4 };
    if (cfg.username) options.username = cfg.username;
    if (cfg.password) options.password = cfg.password;

    var client = mqtt.connect(cfg.brokerWsUrl, options);
    client.on("connect", function () { client.subscribe(cfg.topic); });
    client.on("message", function (topic, message) {
      try {
        updateDashboard(JSON.parse(message.toString()));
      } catch (e) {
        /* malformed payload from the broker side — ignore this message,
           keep the connection (and the next poll) alive */
      }
    });
  }

  function init() {
    startPolling(60000);

    var cfg = window.VANE_MQTT;
    if (cfg && cfg.enable && cfg.brokerWsUrl && cfg.topic) {
      startMqtt(cfg);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
