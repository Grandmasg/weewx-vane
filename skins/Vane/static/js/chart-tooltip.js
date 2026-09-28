/*
 * Vane — shared hover tooltip for the windrose/wind-vector SVG charts.
 * Native SVG <title> tooltips are slow to appear and unstyled, which
 * reads as "hover does nothing" — this attaches a single floating
 * element to any [data-tooltip] element inside a .windrose-svg and
 * positions it near the cursor instead.
 */
(function () {
  "use strict";

  function init() {
    var svgs = document.querySelectorAll(".windrose-svg");
    if (!svgs.length) return;

    var tip = document.createElement("div");
    tip.className = "vane-chart-tooltip";
    document.body.appendChild(tip);

    function show(e, target) {
      tip.textContent = target.getAttribute("data-tooltip");
      tip.classList.add("visible");
      move(e);
    }

    function move(e) {
      var pad = 14;
      var x = e.clientX + pad;
      var y = e.clientY + pad;
      var rect = tip.getBoundingClientRect();
      if (x + rect.width > window.innerWidth - 8) x = e.clientX - rect.width - pad;
      if (y + rect.height > window.innerHeight - 8) y = e.clientY - rect.height - pad;
      tip.style.left = x + "px";
      tip.style.top = y + "px";
    }

    function hide() {
      tip.classList.remove("visible");
    }

    for (var i = 0; i < svgs.length; i++) {
      var svg = svgs[i];
      svg.addEventListener("pointerover", function (e) {
        var target = e.target.closest("[data-tooltip]");
        if (target) show(e, target);
      });
      svg.addEventListener("pointermove", function (e) {
        var target = e.target.closest("[data-tooltip]");
        if (target) move(e);
      });
      svg.addEventListener("pointerout", function (e) {
        var target = e.target.closest("[data-tooltip]");
        if (target) hide();
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
