---
id: apify-booking
kind: lodging
connector: apify
target: voyager/booking-scraper
status: working
last_verified: 2026-09-24
evidence: "runs 5ULVWOoM6bZWhz86N, icJjBcgzcFcEszbMo, MP5IfUxzLnVNgCJUf (2026-09-24), one per type (B&B, guest houses, apartments) for Bologna returned 42/86/150 properties"
---
how: `search` = the city; one run per `propertyType` ("Bed and breakfasts", "Guest houses", "Apartments", …). A district as `search` returned 0 items, so filter by geometry afterwards. `rooms[].options[]` carry `price`, `displayedPrice`, `freeCancellation`.
caveats: `price` and `displayedPrice` differ, and which one includes city tax is UNRESOLVED. Show the higher one and flag it. The cheapest option is often non-refundable.
drop: traderInfo (all), hostInfo.* except name, reviews authors
