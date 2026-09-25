---
id: overpass
kind: vector-data
connector: web
target: https://overpass-api.de/api/interpreter
status: working
last_verified: 2026-09-24
evidence: "run AJLOUTEvWyLdPxWkb (2026-09-24): one bbox query for named streets and rail, `out geom`, relayed through apify-page-render with a named userAgent; built the demo's streets.js"
---
how: One query per trip for the map's base layer: streets, railways and the venue footprint inside a small bounding box, `[out:json][timeout:25];(way[highway](S,W,N,E);way[railway=rail](S,W,N,E););out geom;`. Simplify the geometry before shipping it in `streets.js`. Send a User-Agent naming the application; no parallel queries.
caveats: The sandbox that built the demo could not reach the host directly; a relay worked (`apify-page-render.md`, URL mode). On HTTP 429 or 504, wait at least 30 s before one retry; never loop. Policy (wiki, read 2026-09-25): under 10,000 queries and 1 GB a day is fine for one-off use; "No parallel running of multiple scripts"; identify the app in `User-Agent` or `Referer`. An extract of a whole town is a Substantial part of OSM under the OSMF guideline, so a shipped `streets.js` is an ODbL database: ship it with an ODbL notice (reference/legal.md, Maps). If unreachable, fall back as patterns/page.md says.
drop: —
