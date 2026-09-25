---
pattern: brief
uses: {}
---
# Brief

Ask only what changes the search. Batch every enumerable choice into one structured question.

- **Whose trip.** Is it for the user or their household? Anything else (an agency, an employer, resale, watching prices for others) stops the skill here (invariant 1).
- **Spend.** A total budget for the scraping runs, in the connector's currency (suggest about USD 5 if the user has no number). A lodging search alone is often 5–8 paid runs, so each run gets its share of what is left.
- **Currency** the page should show totals in.

- **Nights, not days.** Restate phrases like "one night before, two after" as check-in / check-out dates plus a night count. When the end day is ambiguous (the event closes mid-afternoon), offer both readings.
- **Tickets vs people.** Tickets bought now and people sharing the room often differ.
- **Route:** airports, direct-only or not, alternative airports allowed or not.
- **Baggage** per ticket: under-seat / cabin trolley / 20–23 kg hold.
- **Lodging type** (hotel / apartment / B&B / guesthouse / room in a home) and must-haves (kitchen, private bath, free cancellation).
- **The anchor is the venue's visitor entrance, not the venue.** Every distance, isochrone and "closest option" hangs on this one point, so settle it before searching lodging:
  - Take the entrance name from the event's own visitor pages (the fact's own record), not from a travel blog or the venue's generic page. Check that each page states the right edition/year: one page can carry this year's header over last year's body.
  - Geocode that entrance in OpenStreetMap: an `entrance=*` node or gate if one exists; otherwise the pedestrian forecourt it is named after (`highway=pedestrian` area). Not a same-named road, a car park, a bus stop or the grounds' centroid, which can sit 100+ m away. Record the OSM type/id.
  - Take the transit lines from the same page.
  - Tag the anchor GROUNDED only when both the name (event page) and the point (OSM object) are sourced. Otherwise the page says the anchor is UNRESOLVED, next to the distances.
- **Location as geometry.** Turn "central, toward the venue" into something testable: a radius around an anchor, a named boundary (old-town ring, district), or a direction from a landmark. Expect it to be refined after the first results.
- **Budget ceiling**, if there is one. Use it to filter, not to anchor the search.
