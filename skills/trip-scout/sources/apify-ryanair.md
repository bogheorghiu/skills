---
id: apify-ryanair
kind: flight-calendar
connector: apify
target: memo23/ryanair-scraper
status: working
last_verified: 2026-09-24
evidence: "runs ByRsawBRFr3ntuQi3 and VWobg8SDM2tq0Gg1f (2026-09-24): roundTrip OTP⇄BLQ, 1–14 Apr 2027: 7 priced rows; oneWay allFlights BLQ→OTP: 6 rows"
---
how: `tripType` is `oneWay` | `roundTrip` (camelCase). `currency` and `market` params exist, so they can test market-based pricing.
caveats: With `allFlights:true`, every row's price field repeats the day's cheapest fare; it is the true price only on the `isDayCheapest:true` row. Tag other departure times' prices UNRESOLVED. Fares exclude bags.
drop: —
