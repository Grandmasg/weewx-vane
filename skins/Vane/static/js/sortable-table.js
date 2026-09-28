/*
 * Vane — generic sortable table.
 * Any <th data-sort-col="N"> makes column N sortable. Any <td> in that
 * column may carry a data-value attribute with the raw sort value (a
 * number or ISO time); if absent, the visible text is used instead.
 * No framework, works on any table with class="sortable-table".
 */
(function () {
  "use strict";

  function cellValue(td) {
    if (!td) return "";
    if (td.hasAttribute("data-value")) {
      var v = td.getAttribute("data-value");
      var n = parseFloat(v);
      return isNaN(n) ? v : n;
    }
    var text = td.textContent.trim();
    var n2 = parseFloat(text.replace(",", "."));
    return isNaN(n2) ? text : n2;
  }

  function sortTable(table, colIndex, ascending) {
    var tbody = table.tBodies[0];
    if (!tbody) return;
    var rows = Array.prototype.slice.call(tbody.rows);
    rows.sort(function (a, b) {
      var va = cellValue(a.cells[colIndex]);
      var vb = cellValue(b.cells[colIndex]);
      if (va < vb) return ascending ? -1 : 1;
      if (va > vb) return ascending ? 1 : -1;
      return 0;
    });
    rows.forEach(function (r) { tbody.appendChild(r); });
  }

  function clearIndicators(table) {
    table.querySelectorAll("[data-sort-col] .sort-indicator").forEach(function (el) {
      el.textContent = "";
    });
  }

  function initTable(table) {
    var headers = table.querySelectorAll("th[data-sort-col]");
    headers.forEach(function (th) {
      var indicator = document.createElement("span");
      indicator.className = "sort-indicator";
      indicator.style.marginLeft = "4px";
      indicator.style.display = "inline-block";
      indicator.style.width = "10px";
      th.appendChild(indicator);
      th.style.cursor = "pointer";
      th.style.userSelect = "none";

      th.addEventListener("click", function () {
        var col = parseInt(th.getAttribute("data-sort-col"), 10);
        var ascending = th.getAttribute("data-sort-dir") !== "asc";
        headers.forEach(function (h) { h.removeAttribute("data-sort-dir"); });
        th.setAttribute("data-sort-dir", ascending ? "asc" : "desc");
        clearIndicators(table);
        indicator.textContent = ascending ? "▲" : "▼";
        sortTable(table, col, ascending);
      });
    });
  }

  function init() {
    document.querySelectorAll("table.sortable-table").forEach(initTable);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
