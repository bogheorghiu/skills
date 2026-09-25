---
id: apify-airbnb
kind: lodging
connector: apify
target: tri_angle/airbnb-scraper
status: working
last_verified: 2026-09-24
evidence: "map-box search URLs returned 66–127 listings with price breakdowns"
---
how: For a precise area, put an Airbnb search URL in `startUrls` with `ne_lat/ne_lng/sw_lat/sw_lng&search_by_map=true`; add `price_max` for a budget. `locationQueries` works for named districts.
caveats: `price.breakDown.taxes` is often the local tourist tax. Reconcile it (patterns/lodging.md §5). Locations may be approximate. Absurd totals mean the dates aren't open.
drop: host.about, host.profileImage, coHosts, host.hostDetails, review authors
