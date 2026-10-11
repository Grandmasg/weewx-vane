# Vane Lottie Animations

In deze map vind je de Lottie vector-animaties (`.json`) voor Vane.

## Mappenstructuur

* `icons/`: geanimeerde iconen voor de dashboardtegels en weercondities (`clear-day.json`, `rain.json`, `humidity.json`, ...).
* `seasons/`: seizoensanimaties voor het seizoenslabel (`spring.json`, `summer.json`, `autumn.json`, `winter.json`).

## Waar komen ze vandaan?

De JSON-bestanden worden **gegenereerd** uit de geanimeerde SVG's in
`static/img/icons/` en `static/img/seasons/` — de SVG's zijn de bron. Zo
hebben SVG en Lottie altijd dezelfde vormen, kleuren en bewegingen.

Na het aanpassen van een SVG:

```bash
pip install lottie            # python-lottie, alleen nodig voor ontwikkeling
python tools/svg2lottie.py    # alles opnieuw, of: python tools/svg2lottie.py rain snow
```

## Hoe werkt het?

1. Vane gebruikt `vane-lottie.js` samen met de lichte, lokale Lottie-engine (`lottie_light.min.js`).
2. **Hover:** zweef je over een dashboardtegel, dan speelt de bijbehorende animatie af.
3. **Hero conditie:** het actuele weericoon animeert continu.
4. **Seizoenslabel:** speelt één keer bij het laden en opnieuw bij hover.
5. Ontbreekt een JSON-bestand, of staat "beweging verminderen" aan, dan blijft de statische SVG staan.

## Eigen animatie gebruiken

Een eigen animatie (LottieFiles, Jitter, After Effects, Figma) met dezelfde
naam in `icons/` zetten werkt nog steeds — maar `tools/svg2lottie.py`
overschrijft hem bij de volgende run. Haal de naam dan uit `ICONS` in dat script.
