# Third-party licenses

Vane's own code is MIT-licensed (see [`LICENSE`](LICENSE)). It also bundles
a small number of third-party components, listed here with their own
licenses, per those licenses' own requirement to retain the copyright
notice in redistributed copies.

## Meteocons (weather condition icons)

- **Files**: `skins/Vane/static/img/icons/*.svg` — Vane's weather icon set
  was originally based on Meteocons (`line` style). The current set
  (filled style, incl. `static/img/seasons/*.svg` and the Lottie files
  generated from them in `static/lottie/`) has been redrawn for Vane; the
  notice below is kept for the original derivation. `logo-mark.svg`,
  `favicon.svg`, `apple-touch-icon.png` and `pwa-*.png` are Vane's own
  original artwork.
- **Source**: [basmilius/meteocons](https://github.com/basmilius/meteocons),
  npm package `@meteocons/svg`.
- **License**: MIT, Copyright (c) Bas Milius.

## uPlot

- **Files**: `skins/Vane/static/js/vendor/uPlot.iife.min.js`,
  `skins/Vane/static/js/vendor/uPlot.min.css`.
- **Source**: [leeoniya/uPlot](https://github.com/leeoniya/uPlot).
- **License**: MIT, Copyright (c) Leon Sorokin.

## lottie-web (light build)

- **Files**: `skins/Vane/static/js/vendor/lottie_light.min.js` (5.13.0,
  SVG renderer only).
- **Source**: [airbnb/lottie-web](https://github.com/airbnb/lottie-web).
- **License**: MIT, Copyright (c) 2015 Airbnb, Inc.

## flag-icons (language switcher flags)

- **Files**: `skins/Vane/static/img/flags/*.svg`.
- **Source**: [lipis/flag-icons](https://github.com/lipis/flag-icons).
- **License**: MIT, Copyright (c) 2013 Panayiotis Lipiridis.

## MQTT.js

- **Files**: `skins/Vane/static/js/vendor/mqtt.min.js` — only loaded/used
  when `[Vane][[MQTT]] enable = true` in `skin.conf`.
- **Source**: [mqttjs/MQTT.js](https://github.com/mqttjs/MQTT.js).
- **License**: MIT, Copyright (c) the MQTT.js contributors.

## Geist / Geist Mono (font)

- **Not bundled** — loaded at runtime from Google Fonts
  (`fonts.googleapis.com`), see the `<link>` tags in each page template.
  Nothing to redistribute here, just linking to Google's own CDN.
- **Source**: [Vercel/Geist](https://vercel.com/font).
- **License**: SIL Open Font License 1.1.
