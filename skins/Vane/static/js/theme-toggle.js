/*
 * Vane — theme toggle (light/dark).
 * Preference is remembered in localStorage; if there is none, the page
 * automatically follows the system preference via CSS
 * (prefers-color-scheme) — this script only forces an explicit choice via
 * data-theme.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "vane-theme";
  var root = document.documentElement;

  function readStored() {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      return v === "light" || v === "dark" ? v : null;
    } catch (e) {
      return null;
    }
  }

  function apply(theme) {
    if (theme) {
      root.setAttribute("data-theme", theme);
    } else {
      root.removeAttribute("data-theme");
    }
  }

  function currentEffective() {
    var explicit = root.getAttribute("data-theme");
    if (explicit === "light" || explicit === "dark") return explicit;
    var prefersLight = window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: light)").matches;
    return prefersLight ? "light" : "dark";
  }

  apply(readStored());

  function initToggle() {
    var btn = document.querySelector("[data-vane-theme-toggle]");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var next = currentEffective() === "dark" ? "light" : "dark";
      apply(next);
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch (e) {
        /* private window / site data blocked — ignore, still works for this session */
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initToggle);
  } else {
    initToggle();
  }
})();
