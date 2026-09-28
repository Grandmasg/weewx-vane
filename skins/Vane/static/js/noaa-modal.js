/*
 * Vane — NOAA text report modal. Opens NOAA/NOAA-*.txt in a native
 * <dialog> instead of navigating away. Feature-detects <dialog>.showModal;
 * without it, links just fall back to normal navigation (progressive
 * enhancement, no broken state on older browsers).
 */
(function () {
  "use strict";

  function init() {
    var dialog = document.getElementById("vane-noaa-modal");
    if (!dialog || typeof dialog.showModal !== "function") return;

    var titleEl = document.getElementById("vane-noaa-title");
    var bodyEl = document.getElementById("vane-noaa-body");
    var closeBtn = document.getElementById("vane-noaa-close");

    document.querySelectorAll(".noaa-link").forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        var url = link.getAttribute("href");
        titleEl.textContent = link.textContent.trim() + " — " + url;
        bodyEl.textContent = "…";
        dialog.showModal();
        fetch(url, { cache: "no-store" })
          .then(function (r) {
            if (!r.ok) throw new Error("HTTP " + r.status);
            return r.text();
          })
          .then(function (text) { bodyEl.textContent = text; })
          .catch(function (err) { bodyEl.textContent = "Error: " + err.message; });
      });
    });

    closeBtn.addEventListener("click", function () { dialog.close(); });
    dialog.addEventListener("click", function (e) {
      if (e.target === dialog) dialog.close();  // click on the backdrop edge
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
