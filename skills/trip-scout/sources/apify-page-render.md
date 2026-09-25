---
id: apify-page-render
kind: page-render
connector: apify
target: moonweil/url-screenshot-api
status: working
last_verified: 2026-09-24
evidence: "html-mode grids of 10–11 images rendered in 20–30 s; 22-image grid timed out"
---
how: `mode: screenshot`, `html` = a tiny page, `waitUntil: networkidle`, `delay: 4`, `fullPage: false`. The image bytes land in the run's key-value store (`screenshot.jpg` / `.png`).
caveats: Keep it to ≤12 images per run. Only for opt-in photos (patterns/photos.md). Never use it to pre-render map tiles.
drop: —
