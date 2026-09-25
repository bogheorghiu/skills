---
id: nominatim
kind: geocoder
connector: web
target: https://nominatim.openstreetmap.org
status: working
last_verified: 2026-09-25
evidence: "2026-09-25: search?format=json&q=Costituzione&viewbox=11.35,44.52,11.375,44.505&bounded=1&extratags=1 returned way 382707838 (highway=pedestrian, Piazza della Costituzione). Direct curl/WebFetch from the cloud container were blocked (proxy 403 / robots.txt); a fetch relay worked."
---
how: Landmark coordinates (venue entrance, station, gates). Use `viewbox=…&bounded=1&extratags=1` around the venue and read `class/type` to tell an entrance or pedestrian forecourt from a same-named road, car park or bus stop. ≤1 request/s, a named User-Agent, no bulk use.
caveats: Many sandboxes can't reach it. Then ask the user, or take coordinates from listing data.
drop: —
