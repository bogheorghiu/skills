---
pattern: page
uses:
  optional_skills: [dataviz, artifact-design]   # use if present; the page must work without them
---
# The page

One private page, designed for this trip; no fixed template. Keep this skeleton:

1. **Header:** trip, dates, one-line brief, and the scrape date ("prices extracted on …, will change").
2. **Calendar strip:** one cell per day. Travel, event (with opening hours) and free days look different. Count the nights.
3. **Bottom line:** 2–3 sentences with the real trade-off in numbers, computed from the data (compare like with like: apartment vs apartment), never hard-coded.
4. **Map.** An SVG drawn from vector data, never from pre-rendered tiles. It must answer "how far is each option from the venue, and what does it cost" without opening a card:
   - Base layer: real streets, railways and the venue footprint from OpenStreetMap vector data (a `vector-data` source, such as `sources/overpass.md`), simplified and shipped as a local `streets.js` with an ODbL notice beside it, with "© OpenStreetMap contributors (ODbL)" on the map. If no vector data is reachable, fall back to sourced gate coordinates or a radius around the anchor, and say the map is schematic.
   - The venue's real entrance (not the centroid of its grounds), labelled.
   - Routed walking minutes on each pin's chip (`17′ · €818`). No circles or other straight-line isochrones; true isochrones only if computed by a router.
   - Numbered pins: shape = platform, fill = inside/outside the constraint, a price chip under each. Resolve overlaps with box-based repulsion that counts the chip, and draw a thin leader line to the true position.
   - Selecting a pin or a card's "Show on map" draws its routed walking path (geometry from the router, shipped in `routes.js`) and states "km along streets, ~min" in a text line above the map (not inside the SVG, where it collides).
   - Narrow screens: smaller pins, minutes and price only on the selected pin, no street labels; say so in the map note.
   - Attribution on the map: "© OpenStreetMap contributors (ODbL)" plus the router; a "fix the map" link (openstreetmap.org/fixthemap) in the sources line.
   - Scale bar in metres, north arrow, true aspect ratio.
   - Every card also links to `https://www.openstreetmap.org/?mlat=LAT&mlon=LON#map=17/LAT/LON`.
   - Projection: equirectangular around the centre's latitude (x ∝ lon·cos φ₀, y ∝ −lat) is accurate enough at city scale.
   - Derive distances from the same entrance coordinate the map uses, so map, cards, chart and bottom line agree.
5. **Price against walking time:** a scatter (x = routed minutes to the venue, y = total), same numbers and shapes as the map. Bottom-left is the best trade-off. Skip it when there is no routing.
6. **Price chart:** horizontal bars, sorted.
   - Colour = lodging type; an outline marks listings outside the constraint. Where the platform shows a price below the total, hatch the difference.
   - Put the per-night label at the end of each bar, and leave ~30% headroom so labels never clip.
7. **Cards.** Each card holds:
   - number, name, platform · type · beds/bath;
   - total, per night and per person;
   - facts: distances, rating on its native scale with review count, price source and date;
   - tags: constraint, direction, amenities, cancellation, thin evidence;
   - a tax/fee note tagged with its evidence status;
   - a link out.
   - Photos only per `patterns/photos.md`.
8. **Flights:** an options table plus the hidden-cost checklist, each item tagged.
9. **Before you book:** taxes, transfers (airport → centre, centre → venue) and cancellation, each uncertainty tagged.
10. **Sources**, with the verification level named.

Behaviour and layout:

- Filters: all / inside the constraint / whole places. Sort: price / distance / rating.
- No self-starting animation.
- Light and dark themes.
- No horizontal scroll at 390 px wide.
- The user's language. For a public demo, offer a language switch.
- A page that will be shared or published carries no host names (invariant 5) and no copied photos (`patterns/photos.md`); the private page may.

Mechanics:

- Many hosted-page sandboxes block external images and fetches. Ship the data with the page (inline, or a local `data.js`).
- Look at one local render before publishing if you can, fix what it shows, then publish.
