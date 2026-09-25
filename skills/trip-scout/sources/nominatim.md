---
id: nominatim
kind: geocoder
connector: web
target: https://nominatim.openstreetmap.org
status: working
last_verified: 2026-09-25
evidence: "2026-09-25: search?format=json&q=Costituzione&viewbox=11.35,44.52,11.375,44.505&bounded=1&extratags=1 returned way 382707838 (highway=pedestrian, Piazza della Costituzione)"
---
how: A handful of landmark lookups per trip (venue entrance, station, gates), one request at a time, at most 1 per second, with a User-Agent naming the application (e.g. `trip-scout/2.1 (+https://github.com/bogheorghiu/skills)`). Use `viewbox=…&bounded=1&extratags=1` around the venue and read `class`/`type` to tell an entrance or pedestrian forecourt from a same-named road, car park or bus stop. Cache each answer in the trip's working notes; never repeat the same query. Before the first lookup, tell the user in one line that this is OpenStreetMap's public geocoder, that its usage policy (https://operations.osmfoundation.org/policies/nominatim/) allows only light, identified, non-bulk use, and that its data is ODbL. The policy requires an LLM that suggests the service to say this.
caveats: Many sandboxes cannot reach it. Then ask the user for the coordinate, or take it from listing data. Relay the request through another service only if that service sends your identifying User-Agent; a stock browser or library User-Agent breaks the policy. Never geocode listings in bulk or in a grid, and never send the user's own address or other personal data (the policy asks for none).
drop: —
