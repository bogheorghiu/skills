---
id: apify-page-render
kind: page-render
connector: apify
target: moonweil/url-screenshot-api
status: working
last_verified: 2026-09-24
evidence: "html-mode grids of 10–11 images rendered in 20–30 s; 22-image grid timed out"
---
how: Two modes. Screenshot mode, for opt-in photos only (patterns/photos.md): `mode: screenshot`, `html` = a tiny page, `waitUntil: networkidle`, `delay: 4`, `fullPage: false`; the image bytes land in the run's key-value store (`screenshot.jpg` / `.png`). URL mode, as a fetch relay for a single router or geocoder request the sandbox cannot reach: `url`, `extract: ["text"]`, and a User-Agent naming the application; read the input schema first, since mode names change.
caveats: Keep screenshot grids to ≤12 images per run. Never use either mode to pre-render map tiles, to fetch listing pages, or to get past a site's own refusal; relay only requests the target's usage policy allows (see the router and geocoder entries).
drop: —
