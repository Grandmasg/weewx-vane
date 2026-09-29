/*
 * Vane — language switcher. Custom listbox (WAI-ARIA "select-only
 * combobox" / listbox-button pattern), not a native <select> — a native
 * <select>'s <option> can never contain an <img>, and real SVG flag
 * icons (see FLAG_CODES/THIRD-PARTY-LICENSES.md in vane_extras.py) need
 * one. This reimplements the keyboard/ARIA behavior a native select gives
 * for free: Enter/Space/Arrow keys open it, Up/Down/Home/End move
 * through options, Enter/Space selects, Escape or a click outside closes
 * it. Each option's data-href is the target URL; the current language's
 * option has none (selecting it again is a no-op).
 */
(function () {
  "use strict";

  function closeListbox(combo) {
    var button = combo.querySelector(".lang-trigger");
    var listbox = combo.querySelector(".lang-listbox");
    listbox.hidden = true;
    button.setAttribute("aria-expanded", "false");
  }

  function openListbox(combo) {
    var button = combo.querySelector(".lang-trigger");
    var listbox = combo.querySelector(".lang-listbox");
    listbox.hidden = false;
    button.setAttribute("aria-expanded", "true");
    var options = listbox.querySelectorAll(".lang-option");
    var target = listbox.querySelector('.lang-option[aria-selected="true"]') || options[0];
    if (target) focusOption(listbox, target);
  }

  function focusOption(listbox, option) {
    var options = listbox.querySelectorAll(".lang-option");
    for (var i = 0; i < options.length; i++) {
      options[i].tabIndex = options[i] === option ? 0 : -1;
    }
    option.focus();
  }

  function selectOption(combo, option) {
    var href = option.getAttribute("data-href");
    closeListbox(combo);
    combo.querySelector(".lang-trigger").focus();
    if (href) location.href = href;
  }

  function initCombo(combo) {
    var button = combo.querySelector(".lang-trigger");
    var listbox = combo.querySelector(".lang-listbox");
    var options = Array.prototype.slice.call(listbox.querySelectorAll(".lang-option"));

    button.addEventListener("click", function () {
      if (listbox.hidden) openListbox(combo); else closeListbox(combo);
    });

    button.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openListbox(combo);
      }
    });

    options.forEach(function (option, i) {
      option.addEventListener("click", function () { selectOption(combo, option); });
      option.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectOption(combo, option);
        } else if (e.key === "ArrowDown") {
          e.preventDefault();
          focusOption(listbox, options[Math.min(i + 1, options.length - 1)]);
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          focusOption(listbox, options[Math.max(i - 1, 0)]);
        } else if (e.key === "Home") {
          e.preventDefault();
          focusOption(listbox, options[0]);
        } else if (e.key === "End") {
          e.preventDefault();
          focusOption(listbox, options[options.length - 1]);
        } else if (e.key === "Escape") {
          e.preventDefault();
          closeListbox(combo);
          button.focus();
        } else if (e.key === "Tab") {
          closeListbox(combo);
        }
      });
    });

    document.addEventListener("click", function (e) {
      if (!listbox.hidden && !combo.contains(e.target)) closeListbox(combo);
    });
  }

  function init() {
    var combos = document.querySelectorAll(".lang-combo");
    for (var i = 0; i < combos.length; i++) initCombo(combos[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
