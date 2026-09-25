---
id: osrm-fossgis
kind: router
connector: web
target: https://routing.openstreetmap.de/routed-foot/
status: working
last_verified: 2026-09-25
evidence: "2026-09-25: https://routing.openstreetmap.de/routed-foot/table/v1/foot (1 source, 15 destinations, annotations=duration,distance) and route/v1/foot (31 waypoints, overview=full) returned code Ok; per-leg distances/durations identical across the two requests (e.g. 1250.1 m / 17 min, 3599.5 m / 48 min)."
---
how: Two requests cover a whole trip. Times and distances for all listings in one `table/v1/foot/{anchor};{p1};…?sources=0&annotations=duration,distance`. Route lines for all listings in one `route/v1/foot/{anchor};{p1};{anchor};{p2};…;{anchor}?overview=full&steps=false&geometries=polyline`, then split the polyline at the waypoints (legs 1, 3, 5… are listing→anchor). `steps=true` bloats the reply past 100 kB; avoid it. Coordinates are lon,lat. Send a User-Agent naming the application. If the sandbox blocks the host, a relay is acceptable only if it sends that User-Agent (on 2026-09-25 the page-render source in URL mode did, per `apify-page-render.md`); otherwise show no walking figures and say why (patterns/lodging.md).
caveats: Walking at ~4.5 km/h with no waiting at crossings or lights, so real times run longer. Usage policy (routing.openstreetmap.de/about.html, read 2026-09-25): "One request per second max", "Use a valid user agent", "No scraping, no heavy usage", "Display the required attribution and display a link to 'fix the map'". Results are works produced from OSM (ODbL): attribute them. Never put the user's email or other personal data in the User-Agent.
drop: waypoint `hint` strings (opaque, useless after the request).
