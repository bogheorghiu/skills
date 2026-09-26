---
id: apify-page-render
kind: page-render
connector: apify
target: moonweil/url-screenshot-api
status: working
last_verified: 2026-09-24
evidence: "run 4lJdLydWgDpVXZgnS (2026-09-24): html-mode grid of 11 images rendered; a 22-image grid timed out. URL mode: run AJLOUTEvWyLdPxWkb (2026-09-24) relayed one Overpass query with a custom userAgent"
---
how: Two modes. Screenshot mode, for opt-in photos only (patterns/photos.md): `mode: screenshot`, `html` = a tiny page, `waitUntil: networkidle`, `delay: 4`, `fullPage: false`; the image bytes land in the run's key-value store (`screenshot.jpg` / `.png`). URL mode, as a fetch relay for a single router or map-data request the sandbox cannot reach: `mode: screenshot` with `url`, `extract: ["text"]` and `userAgent` naming the application (the input that worked on 2026-09-24); read the input schema first, since fields change. Never for Nominatim: its policy names Apify among the API resellers that must run their own geocoder.
caveats: Keep screenshot grids to ≤12 images per run. Never use either mode to pre-render map tiles, to fetch listing pages, or to get past a site's own refusal; relay only requests the target's usage policy allows (see the router and map-data entries). A relay run is a paid run: it counts against the budget and comes after the notice (SKILL.md, Flow step 4).
drop: —
