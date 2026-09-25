---
id: apify-wizzair
kind: flight-calendar
connector: apify
target: memo23/wizzair-scraper
status: working
last_verified: 2026-09-24
evidence: "run BWPOGNJZhpbSqT8e3 (2026-09-24): roundTrip OTP⇄BLQ, out 2–5 Apr, back 9–13 Apr 2027: 9 fare-day rows"
---
how: `tripType` is `oneWay` | `roundTrip`. The platform refused a spend cap under $0.60.
caveats: Cheapest fare per day only: no flight times, no bags. Currency follows the route (outbound RON, inbound EUR on OTP⇄BLQ); convert per patterns/flights.md step 3, never add the raw amounts.
drop: —
