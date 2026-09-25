---
id: osrm-fossgis
kind: router
connector: web
target: https://routing.openstreetmap.de/routed-foot/
status: working
last_verified: 2026-09-25
evidence: "2026-09-25: table/v1/foot (1 source, 15 destinations, annotations=duration,distance) and route/v1/foot (31 waypoints, overview=full) returned code Ok; per-leg distances/durations identical across the two requests (e.g. 1250.1 m / 17 min, 3599.5 m / 48 min)."
---
how: One request for everything. Times+distances: `table/v1/foot/{anchor};{p1};…?sources=0&annotations=duration,distance`. Route lines: `route/v1/foot/{anchor};{p1};{anchor};{p2};…;{anchor}?overview=full&steps=false&geometries=polyline`, then split the polyline at the waypoints (legs 1, 3, 5… are listing→anchor). `steps=true` bloats the reply past 100 kB; avoid it. Coordinates are lon,lat. The cloud container's proxy blocked the host directly; fetching the URL through the page-render source (URL mode, `extract:["text"]`, a descriptive User-Agent) worked.
caveats: Walking at ~4.5 km/h with no waiting at crossings or lights, so real times run longer. Usage policy (routing.openstreetmap.de/about.html): max 1 request/s, valid User-Agent, no scraping or heavy use, show attribution and a "fix the map" link. Data is OSM under ODbL: attribution required for public use of works produced from it; share-alike applies to publicly used adapted databases. Never put the user's email or other personal data in the User-Agent.
drop: waypoint `hint` strings (opaque, useless after the request).
