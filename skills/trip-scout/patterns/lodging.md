---
pattern: lodging
uses:
  sources: [kind=lodging]
---
# Lodging

1. **Search 2+ lodging platforms.** Cover an area slightly wider than the constraint, so the page can show what's just outside it. Follow each source entry's `how` notes (map box, one run per property type, and so on).
2. **Filter by the geometry**, not by the platforms' neighbourhood labels.
   - For a named boundary, trace a polygon from a map image or from sourced gate coordinates, then test point-in-polygon.
   - Draw the boundary on the page so the user can judge it.
   - Tag where the polygon came from.
3. **Treat points near the boundary as "borderline".** Some platforms show approximate locations when the host hides the precise one.
4. **Derived fields per listing:**
   - total, per night, per person;
   - walking distance and time to the anchor (the entrance from `patterns/brief.md`), **routed along streets** by a router from `sources/` (kind=router), one batched request for all listings. Compute them once, in one place, so map, cards, charts and the bottom line cannot disagree. Never show a straight-line distance or a "straight line × factor" time as a stand-in: rail lines, rivers and ring roads make it wrong exactly where it matters. If no router is reachable, show no walking figures at all and say so on the page; rank by price instead;
   - direction from the centre;
   - kitchen / AC / lift / private bath;
   - the cheapest free-cancellation price, where the data has it.
5. **Reconcile taxes with arithmetic.** Local tourist taxes usually follow a rule (percent of the nightly price, per-person cap, maximum nights). Find the rule, then check each listing's tax line against it:
   - it matches: the tax is already in the total (GROUNDED);
   - there's no line: estimate the tax and flag it (UNRESOLVED);
   - it doesn't match: the line includes something else, so say that.
6. **Flag thin evidence:**
   - fewer than 5 reviews;
   - a rating of 0;
   - placeholder prices. Absurd totals usually mean the dates aren't open yet.
7. **Before saving anything, drop personal fields per the source entry's `drop` list** (invariant 5).
