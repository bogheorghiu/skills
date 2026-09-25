---
paths:
  - "examples/**"
  - "skills/**/patterns/page.md"
  - "skills/**/sources/**"
---

# Use OpenStreetMap data and services on their terms

The skill's maps and walking times rest on OpenStreetMap data and on services run by volunteers (Nominatim, the FOSSGIS router, Overpass). Their terms are in `skills/trip-scout/reference/legal.md` under Maps, quoted from the primary pages. What they mean when you work here:

- Never add pre-rendered map tiles to the repository or to a page: the tile policy forbids offline and bulk use, and the skill's invariant 7 rules them out.
- A file that stores OSM-derived data (such as `streets.js` or `routes.js`) is licensed under the ODbL and sits beside a notice that says so. The code's MIT licence does not cover it.
- Every page that shows the data says "© OpenStreetMap contributors (ODbL)" and links to openstreetmap.org/fixthemap.
- Scripted requests to these services send a User-Agent that names the application, go one at a time, and stay within each policy's rate limit. A relay is acceptable only if it forwards that User-Agent, and never for Nominatim through Apify: that policy names Apify as an API reseller that must run its own geocoder. The services run on donated capacity, and the Nominatim policy says unacceptable use "will get you banned"; every user of the skill shares its User-Agent, so a ban hits all of them.
