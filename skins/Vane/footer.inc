#*
  Shared page footer — included (not templated as its own [[[name]]]
  page, see skin.conf [CopyGenerator]/[CheetahGenerator] comments and
  THEME_PLAN.md "plugins/ <- #include-only") on every Vane page so it's
  identical everywhere instead of copy-pasted 5x. Wrapped in
  .vane-footer-sticky so it sits at the bottom of the viewport on
  short-content pages (e.g. Almanac) instead of floating awkwardly
  halfway up, but scrolls normally once page content is tall enough to
  push it down on its own — see .vane-container/.vane-footer-sticky in
  vane.css.

  "About" (station facts, all already available via $station) + "Links".
  Windy needs zero config (built straight from
  $station.latitude_f/longitude_f, works for any install); anything more
  personal (e.g. a local lightning map) belongs in the existing
  dashboard_plugins slot, not hardcoded here — see THEME_PLAN.md
  "Personal integrations are a separate plugin".
*#
<footer class="vane-footer-sticky">
  <div class="vane-footer-wide">
    <div class="footer-col">
      <span class="uppercase-label">$gettext("About")</span>
      <div class="footer-lines">
        <span>$gettext("Hardware"): $station.hardware</span>
        <span>$gettext("Altitude"): $station.altitude.format(add_label=True)</span>
        <a href="telemetry.html">$gettext("Telemetry")</a>
        #if $station.station_url
        <a href="$station.station_url" target="_blank" rel="noopener">$station.location</a>
        #end if
      </div>
    </div>
    <div class="footer-col">
      <span class="uppercase-label">$gettext("Links")</span>
      <div class="footer-lines">
        <a href="https://weewx.com/" target="_blank" rel="noopener">WeeWX</a>
        <a href="https://www.windy.com/?${station.latitude_f},${station.longitude_f},10" target="_blank" rel="noopener">Windy</a>
      </div>
    </div>
  </div>

  <div class="vane-footer">
    <span><a href="https://weewx.com/" target="_blank" rel="noopener">WeeWX $station.version</a> &middot; $station.hardware</span>
    <span><a href="https://github.com/Grandmasg/weewx-vane" target="_blank" rel="noopener">Vane v$vane_version</a></span>
  </div>
</footer>
