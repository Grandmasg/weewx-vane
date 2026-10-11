/**
 * Vane - Lottie & Interactive Micro-Animations Engine
 *
 * Provides smooth, performant vector micro-animations on hover for dashboard
 * tiles and continuous ambient animations for current weather conditions.
 *
 * Gracefully falls back to SVG + CSS animations if Lottie files are absent
 * or if the user prefers reduced motion.
 */
(function () {
  'use strict';

  // Tiles that use dedicated Lottie animations (others like barometer, wind, ET, cloudbase, rain use custom reactive SVGs)
  var SENSOR_TO_ICON = {
    humidity: 'humidity',
    outHumidity: 'humidity',
    radiation: 'solar-radiation',
    luminosity: 'solar-radiation',
    UV: 'uv-index',
    outTemp: 'thermometer',
    dewpoint: 'thermometer',
    appTemp: 'thermometer',
    lightning: 'thunderstorms'
  };

  var prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Inline SVG icons for tiles so CSS hover can target internal elements (.wind-rotor, .baro-needle, .baro-face, etc.)
  function inlineSvgs() {
    // With reduced motion the hero/season icons stay SVG for good, so they
    // are inlined too: SMIL inside an <img> can't be paused, inline it can.
    var sel = 'img.tile-icon, img.logo' +
      (prefersReducedMotion ? ', img.hero-condition-icon, img.season-icon' : '');
    var imgs = document.querySelectorAll(sel);
    imgs.forEach(function (img) {
      var src = img.getAttribute('src');
      if (!src || src.indexOf('.svg') === -1) return;
      fetch(src)
        .then(function (res) {
          if (!res.ok) throw new Error('Network error');
          return res.text();
        })
        .then(function (svgText) {
          var parser = new DOMParser();
          var doc = parser.parseFromString(svgText, 'image/svg+xml');
          var svg = doc.querySelector('svg');
          if (svg) {
            svg.setAttribute('class', (img.getAttribute('class') || ''));
            svg.setAttribute('width', img.getAttribute('width') || '40');
            svg.setAttribute('height', img.getAttribute('height') || '40');
            // Keep it hidden if a Lottie animation already took its place.
            if (img.style.display === 'none') svg.style.display = 'none';
            if (img.getAttribute('alt')) {
              svg.setAttribute('aria-label', img.getAttribute('alt'));
            }
            if (img.parentNode) {
              img.parentNode.replaceChild(svg, img);
              if (prefersReducedMotion && svg.pauseAnimations) {
                svg.pauseAnimations();
                svg.setCurrentTime(0);
              }
            }
          }
        })
        .catch(function () {});
    });
  }

  // Loads static/lottie/<path>.json into a new <span> placed right after
  // `fallback` (the static <img>/<svg>). The fallback stays visible until
  // the animation has actually rendered, and stays for good if the JSON is
  // missing — that's what makes "drop your own wind.json in icons/" work.
  function mountLottie(fallback, path, opts) {
    var w = fallback.getAttribute('width') || '28';
    var h = fallback.getAttribute('height') || w;
    var host = document.createElement('span');
    host.className = 'lottie-icon';
    host.setAttribute('aria-hidden', 'true');
    host.style.width = w + 'px';
    host.style.height = h + 'px';
    host.hidden = true;
    fallback.parentNode.insertBefore(host, fallback.nextSibling);

    var anim = window.lottie.loadAnimation({
      container: host,
      renderer: 'svg',
      loop: !!opts.loop,
      autoplay: !!opts.autoplay,
      path: 'static/lottie/' + path + '.json'
    });
    anim.addEventListener('DOMLoaded', function () {
      applyShadow(host, anim.animationData && anim.animationData.vaneShadow, parseFloat(w));
      if (opts.hiddenUntilShown) return;
      host.hidden = false;
      fallback.style.display = 'none';
    });
    anim.addEventListener('data_failed', function () {
      anim.destroy();
      if (host.parentNode) host.parentNode.removeChild(host);
    });
    anim.vaneHost = host;
    return anim;
  }

  // tools/svg2lottie.py copies the SVG's feDropShadow into the JSON as
  // "vaneShadow" (lottie_light can't render SVG filters); re-create it as a
  // CSS drop-shadow, scaled from viewBox units to the rendered size.
  function applyShadow(host, sh, size) {
    if (!sh) return;
    var k = size / (sh.viewbox || 64);
    var hex = (sh.color || '#000').replace('#', '');
    if (hex.length === 3) hex = hex.replace(/./g, '$&$&');
    var n = parseInt(hex, 16);
    var rgba = 'rgba(' + (n >> 16 & 255) + ',' + (n >> 8 & 255) + ',' + (n & 255) + ',' + sh.opacity + ')';
    host.style.filter = 'drop-shadow(' + (sh.dx * k) + 'px ' + (sh.dy * k) + 'px ' +
      (sh.blur * k) + 'px ' + rgba + ')';
  }

  // Current-conditions icon: continuous ambient loop.
  function initHero() {
    var hero = document.querySelector('[data-lottie-hero]');
    if (!hero) return;
    var img = hero.querySelector('.hero-condition-icon');
    var name = hero.getAttribute('data-lottie-hero');
    if (img && name) mountLottie(img, 'icons/' + name, { loop: true, autoplay: true });
  }

  // Tiles: the Lottie loops only while the tile is hovered; on leave the
  // SVG comes back. The SVG animates continuously on its own, so leaving
  // the (paused) Lottie in its place after a hover froze the icon.
  // The JSON is fetched lazily on the first hover.
  function initTiles() {
    document.querySelectorAll('.tile[data-sensor]').forEach(function (tile) {
      var name = SENSOR_TO_ICON[tile.getAttribute('data-sensor')];
      if (!name) return;
      var anim = null, icon = null, ready = false, hovering = false;
      function show(on) {
        if (!ready) return;
        anim.vaneHost.hidden = !on;
        // Re-query: inlineSvgs() may have replaced the <img> since.
        var cur = tile.querySelector('.tile-icon');
        if (cur) cur.style.display = on ? 'none' : '';
        if (on) anim.goToAndPlay(0, true); else anim.stop();
      }
      tile.addEventListener('mouseenter', function () {
        hovering = true;
        if (anim) { show(true); return; }
        // Looked up now, not at init: inlineSvgs() may have swapped the
        // <img> for an inline <svg> in the meantime.
        icon = tile.querySelector('.tile-icon');
        if (!icon) return;
        anim = mountLottie(icon, 'icons/' + name,
          { loop: true, autoplay: false, hiddenUntilShown: true });
        anim.addEventListener('DOMLoaded', function () {
          ready = true;
          show(hovering);
        });
      });
      tile.addEventListener('mouseleave', function () {
        hovering = false;
        show(false);
      });
    });
  }

  // Season pill: play once on load, replay on hover.
  function initSeason() {
    var pill = document.querySelector('.season-pill[data-season]');
    var icon = pill && pill.querySelector('.season-icon');
    if (!icon) return;
    var anim = mountLottie(icon, 'seasons/' + pill.getAttribute('data-season'),
      { loop: false, autoplay: true });
    pill.addEventListener('mouseenter', function () {
      anim.goToAndPlay(0, true);
    });
  }

  function initLottie() {
    inlineSvgs();
    if (prefersReducedMotion || !window.lottie) return;
    initHero();
    initTiles();
    initSeason();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLottie);
  } else {
    initLottie();
  }
})();
