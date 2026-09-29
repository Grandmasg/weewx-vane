/*
 * Vane — language switcher. A native <select> (not a custom dropdown) on
 * purpose: built-in keyboard nav + screen-reader support, no ARIA to get
 * wrong, and its closed-state chrome is fully CSS-stylable (see .lang-select
 * in vane.css) while the open popup follows the page's color-scheme
 * automatically (see the color-scheme fix in vane.css). Each <option>'s
 * value is the target URL; the current language's option has an empty
 * value so selecting it again is a no-op.
 */
(function () {
  "use strict";

  function init() {
    var selects = document.querySelectorAll(".lang-select");
    for (var i = 0; i < selects.length; i++) {
      selects[i].addEventListener("change", function (e) {
        var url = e.target.value;
        if (url) location.href = url;
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
