---
id: apify-ryanair
kind: flight-calendar
connector: apify
target: memo23/ryanair-scraper
status: working
last_verified: 2026-09-24
evidence: "roundTrip OTP⇄BLQ, 1–14 Apr 2027: 7 priced rows; oneWay allFlights BLQ→OTP: 6 rows"
---
how: `tripType` is `oneWay` | `roundTrip` (camelCase). `currency` and `market` params exist, so they can test market-based pricing.
caveats: With `allFlights:true`, every row carries the day's cheapest fare; only the `isDayCheapest:true` row is priced. Tag other departure times' prices UNRESOLVED. Fares exclude bags.
drop: —
