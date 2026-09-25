# trip-scout review 2 — findings

Reviewed folder: `scratchpad/review2/trip-scout/` (SKILL.md, reference/legal.md, patterns/{adapt,brief,flights,lodging,page,photos}.md, sources/README.md + 9 entries, scripts/sources.py, LICENSE, plus a stray `scripts/__pycache__/sources.cpython-311.pyc`). Date of review: 2026-09-25. Nothing outside the folder was read; the script was run under Python 3.11.15 as uid 0 with `TRIP_SCOUT_HOME` pointed at two throwaway folders (`scratchpad/review2-ovl`, `scratchpad/review2-ovl2`).

Bar (fixed before starting): BLOCKING = wrong result shown / illegal or policy-violating action (incl. breaking a web service's published usage policy) / money spent without consent / failed run. MAJOR = confusion a careful agent works around, a typical one would not. MINOR = polish. PASS = zero BLOCKING.

---

## Q1. Flow walk: "cheapest flights Bucharest–Lisbon + a room near the Web Summit venue, 9–13 Nov, me and my partner"

Traced as a small model that reads SKILL.md and opens files on demand.

| Step | Opens | Asks the user | Spends | What can go wrong (finding IDs) |
|---|---|---|---|---|
| Load order | SKILL.md, then `patterns/adapt.md` §Overlay (SKILL.md: "Resolve the user overlay (`patterns/adapt.md` §Overlay)") | On a fresh install the overlay folder does not exist, so adapt.md makes the **first question of the conversation** "show the user the path and ask whether to use it or another folder" — before anything about the trip. | 0 | UX ordering (F-13). |
| 1 Brief | `patterns/brief.md` | Whose trip (household → ok); spend budget ("suggest about USD 5"); page currency; nights (9→13 = 4 nights, or 3 if the event closes mid-afternoon on the 13th — brief.md tells it to offer both); tickets vs people (2/2); route (OTP/BBU → LIS, direct-only?); baggage; lodging type ("a room" → hotel / room in a home); the anchor = venue's visitor entrance; location geometry; budget ceiling. | 0 | The anchor requires reading "the event's own visitor pages" and geocoding "an `entrance=*` node" — the skill supplies no way to read a web page and Nominatim cannot search by tag (F-10, F-11). If the agent cannot reach Nominatim it must ask for a coordinate; a small model is tempted to recall MEO Arena's coordinates (invariant 8 forbids; brief.md's UNRESOLVED fallback covers the honest case). |
| 2 Sources | runs `scripts/sources.py check`; `sources/README.md`; all 9 entries; "Read each actor's input schema before its first call" | — | 0 | Reading the input schema needs the Apify connector, which is only requested in step 3 (F-12). Only `apify-google-flights` matches `flight-aggregator` and it is `untested`. |
| 3 Connector | — | "turn on Apify" with one line why | 0 | — |
| 4 Notice | `reference/legal.md` | A few sentences on platform terms + "wait for a yes" | 0 | The notice is honest; the run that follows still breaks the platforms' terms (F-01). |
| 5a Flights | `patterns/flights.md`, `sources/apify-ryanair.md`, `apify-wizzair.md`, `apify-google-flights.md` | Cap per run if the connector has no cap field | Ryanair roundTrip ±3 days (1 run), Wizz roundTrip (1 run, cap ≥ $0.60), Google Flights (1 run, untested actor) ≈ 3 paid runs | FX conversion needs "a rate from a dated source you cite" — no `reference` source exists (F-14). Wizz refuses caps under $0.60; a $5 budget shared over ~10 runs is under that floor (F-09). A calendar returning 0 rows for a route the carrier does not fly has no rule separating "no route" from "failure" (F-15). |
| 5b Lodging | `patterns/lodging.md`, `apify-airbnb.md`, `apify-booking.md`, `nominatim.md`, `osrm-fossgis.md`, `overpass.md`, `apify-page-render.md` | Nominatim policy one-liner before the first geocode | Airbnb map-box (1 run), Booking city-wide one run per propertyType (2–3 runs), relay runs if the sandbox cannot reach Overpass/OSRM (1 + 1–2 runs) ≈ 5–7 paid runs | Airbnb `how` omits `checkin/checkout/adults` (F-05). Booking city-wide "Lisbon" with a per-run cap truncates an arbitrary subset (F-06). Lisbon tourist-tax rule must be "found" with no source (F-14). |
| 6 Interim shortlist | — | corrections | 0 | — |
| 7 Page | `patterns/page.md` (+ optional dataviz/artifact-design) | — | 0 | Base-layer fallback assumes a polygon that comes from the same unreachable source (F-16). |
| 8 Adapt | `patterns/adapt.md`, `scripts/sources.py set …` | approval only for pattern edits | 0 | Re-verifying 6–8 used sources + one fix exceeds the cap of 5 (F-17); `--caveats`/`--how` replace wholesale (F-03); on a root sandbox an unwritable overlay tracebacks instead of exit 3 (F-02). |
| 9 Close | — | — | 0 | — |

Total plausible spend for this request: 8–10 paid Apify runs; every one is behind the step-4 notice and a per-run cap, so **no money-without-consent path was found** as long as the agent follows step 5 literally.

---

## Findings

### F-01 — BLOCKING (by the letter of the bar; see note) — the skill's core action breaks the target platforms' published terms, knowingly
- **File / quote:** `reference/legal.md` L9: "The Ryanair terms quoted in the judgment limit use to an enumerated list of "private, non-commercial purposes" and separately ban screen scraping "for commercial purposes". Automated extraction is not on the permitted list even for private use." `SKILL.md` L28 (invariant 2): "Platform terms generally forbid automated extraction, even for personal use. The scraping runs through a third-party actor, and the user decides whether to go ahead." `SKILL.md` L3: "…for a dated personal trip via a scraping connector, within legal limits…".
- **Scenario:** The user says yes at Flow step 4; the agent runs `memo23/ryanair-scraper`, `memo23/wizzair-scraper`, `tri_angle/airbnb-scraper`, `voyager/booking-scraper`, `kaix/google-flights-scraper`. By the skill's own account, each of those extractions is outside the platform's terms of use. The bar defines "breaking a web service's published usage policy" as BLOCKING, and following the files as written does exactly that after informed consent.
- **Note on severity:** This is the skill's premise, not an oversight; the mitigation (disclosure, no circumvention, actor defaults only, public pages only) is as complete as a skill can make it, and a contract breach is a civil matter (legal.md is careful to say so). If the reviewer treats consented ToU breach as outside "policy-violating action", this finding disappears and the verdict becomes PASS. I record it as BLOCKING because the bar as written names it; I would not call it a defect the author failed to see.
- **Fix:** Either (a) accept it and drop "within legal limits" from the description (it is more than the file supports: legal.md says the exposure is contractual and unknown outside the EU), replacing it with "with the platforms' terms disclosed", or (b) narrow the skill to sources whose terms permit the use (the OSM stack, official airline/OTA APIs where they exist) and make the scraping actors an opt-in the user configures.

### F-02 — MAJOR — `sources.py` crashes with a traceback instead of the documented exit 3 when the overlay cannot be created (root sandboxes)
- **File / quote:** `patterns/adapt.md` L47: "Exit code 3 means the overlay is not writable: show the user the printed diff (propose-only)." `scripts/sources.py` L70–76 (`writable()` walks up to the first existing ancestor and returns `os.access(probe, os.W_OK)`).
- **Observed:** `TRIP_SCOUT_HOME=/proc/nope/x python3 scripts/sources.py where` → `writable: True`, exit 0 (uid 0 passes `os.access` on `/proc`). `… set apify-airbnb --drop "…, host.email"` → `FileNotFoundError` traceback from `write_atomic`, exit 1, no diff printed. The same happens for any path whose first existing ancestor is root-writable but not creatable (read-only mounts, `/proc`, `/sys`).
- **Scenario:** Cloud agent sandboxes commonly run as uid 0 (this one does). The agent gets a Python traceback, adapt.md has told it nothing about that case, and a small model reports "the tool crashed" or retries.
- **Fix:** Wrap `write_atomic` + the changelog append in `try/except OSError` and route to the same exit-3 propose-only branch; make `writable()` attempt a probe (`tempfile.mkstemp` in the first existing ancestor, or `os.makedirs` inside a try) instead of `os.access`.

### F-03 — MAJOR — `--caveats` / `--how` replace the whole line; a hard limit in adapt.md is silently violated and `check` cannot see it
- **File / quote:** `patterns/adapt.md` L35: "Never remove a `drop` list entry or a caveat without evidence that it no longer applies." `patterns/adapt.md` L42: "`scripts/sources.py` … applies the rules above that a machine can check." `scripts/sources.py` L271 `replace_line` docstring: "Substitute one `key: value` line".
- **Observed:** `set apify-ryanair --caveats "new caveat" --evidence "run ABCDEFGHIJKLMNOP1"` was accepted; the overlay entry now reads `caveats: new caveat` and the bundled caveat "With `allFlights:true`, every row's price field repeats the day's cheapest fare…" is gone. `check` reports `0 invalid`.
- **Scenario:** Session A learns one more caveat and, reading `--caveats` as "add a caveat", passes only the new text. Session B (overlay overrides bundled) reads the Ryanair entry without the allFlights warning, quotes every departure time at the day's cheapest fare, tags them GROUNDED. This is a wrong result on a shared page, two sessions later. The `drop` list has exactly the guard that caveats and `how` lack.
- **Fix:** Either make `--caveats`/`--how` append by default (with `--replace-caveats` requiring `--reason`, mirroring `--allow-drop-removal`), or have `validate()` warn when an overlay `caveats:` lacks each sentence of the bundled one. State the replace semantics in the `--help` text and in adapt.md.

### F-04 — MAJOR — `evidence` handle rule is enforced only for `working`/`degraded`; marking `broken`, and adding `untested` entries, accept anything
- **File / quote:** `patterns/adapt.md` L25: "Update a source entry's `status`, … | Autonomous | Evidence from this session: a run ID, a URL, or one quoted line of error text". L27: "Add a new source entry | Autonomous | It passed one real run in this session". `sources/README.md` L15: `evidence: "…" # needs a handle: URL, run/dataset ID, or quoted output`. `scripts/sources.py` L367: `if ev and status_after in ("working", "degraded") and not HANDLE_RE.search(ev)`.
- **Observed:** `set apify-ryanair --status broken --evidence "x"` → written, logged as `| x |`. `add apify-kiwi … --status untested --evidence "seen in store, not run"` → written. Conversely `set … --status degraded --evidence "Error: actor timed out after 300s"` → REFUSED (no quote characters around the error line), and adapt.md L46 then says "do not reword and retry".
- **Scenario:** A working source is marked `broken` on a hunch with evidence "x", and future sessions skip it (adapt.md: mark broken needs "Two failures, or one unambiguous failure" — not checked either). Meanwhile an honest agent pasting a real error line unquoted is refused and told not to retry.
- **Fix:** Apply `HANDLE_RE` to every status change and to `add`; in the refusal say literally "wrap the error line in double quotes"; drop `untested` from `add` (adapt.md does not allow it) or add it to adapt.md's table.

### F-05 — MAJOR — Airbnb `how` omits the URL parameters that determine the price (dates, guests)
- **File / quote:** `sources/apify-airbnb.md` L10: "For a precise area, put an Airbnb search URL in `startUrls` with `ne_lat/ne_lng/sw_lat/sw_lng&search_by_map=true`; add `price_max` for a budget."
- **Scenario:** For "me and my partner", 9–13 Nov, an agent that builds the URL exactly as written gets undated, 1-guest results: no stay total, or a per-night price that excludes the extra-guest fee some hosts charge. The page then compares a 1-adult Airbnb price with a 2-adult Booking price. The actor's input schema does not help because the URL is hand-built. (The bundled evidence says "price breakdowns", so the verified run must have had dates in the URL; the `how` does not carry that.)
- **Fix:** Add to `how`: "…`&checkin=YYYY-MM-DD&checkout=YYYY-MM-DD&adults=N` (from the brief); without them the actor returns undated per-night prices."

### F-06 — MAJOR — Booking city-wide search plus a per-run spend cap yields an arbitrary subset; nothing tells the agent to say so
- **File / quote:** `sources/apify-booking.md` L10: "`search` = the city; one run per `propertyType` … A district as `search` returned 0 items, so filter by geometry afterwards." `SKILL.md` L43: "Set each run's spend cap from the budget left".
- **Scenario:** `search: "Lisbon", propertyType: "Apartments"` for a city with thousands of listings, cap ≈ $0.50: the actor stops at the cap, returning whichever N listings it reached first. The agent filters by the Parque das Nações geometry, finds few or none, and the page's bottom line says "nothing under €X inside 1.5 km of the entrance" — an artefact of truncation. The Bologna evidence (42/86/150 properties) never hit this.
- **Fix:** In `how`: pass a `maxItems`/results limit and prefer a landmark or the venue name as `search` with a radius/sort-by-distance if the actor has one; in `caveats`: "If the run stopped at the charge limit, the set is a sample: say so on the page and never state 'no options' from it."

### F-07 — MAJOR — the notice text is the only guard; SKILL.md's description over-claims "within legal limits"
- **File / quote:** `SKILL.md` L3: "…via a scraping connector, within legal limits…". `reference/legal.md` L86: "Treat computer-misuse, unfair-competition and database law as unknown, and say so to the user."
- **Scenario:** A user chooses this skill from a listing on the strength of "within legal limits"; the skill's own core file says the law is unknown outside the EU and that the platforms' terms are broken even in the EU. The agent surfaces the truth only at step 4.
- **Fix:** Reword the description: "…with the platforms' terms disclosed before any paid run…".

### F-08 — MINOR — the FORBIDDEN guard is word-adjacency based and misses obvious rewordings; the Nominatim relay ban is not enforced in the overlay
- **File / quote:** `scripts/sources.py` L49–50 (`residential prox\w*|rotating prox\w*|proxyconfiguration`). `sources/nominatim.md` L11: "Do not relay it through Apify or another API reseller".
- **Observed:** `--how "set useApifyProxy true with proxy group residential"` → accepted. `set nominatim --how "use the apify relay, target … via proxy" --evidence https://example.com/run/1` → accepted; a later session reads that `how` as instructions and violates the Nominatim reselling clause. The script's docstring admits it "cannot stop … an agent that lies to it", so this is a gap, not a contradiction.
- **Fix:** Add `relay|apify|reseller` to a per-entry forbidden list for `kind: geocoder`; add `proxy group|useapifyproxy` to FORBIDDEN.

### F-09 — MINOR — the suggested default budget cannot cover the flow's own run count at the documented cap floor
- **File / quote:** `patterns/brief.md` L10: "suggest about USD 5 if the user has no number. A lodging search alone is often 5–8 paid runs, so each run gets its share of what is left." `sources/apify-wizzair.md` L10: "The platform refused a spend cap under $0.60."
- **Scenario:** ~10 runs / $5 = $0.50 each < $0.60; the agent hits a refusal on the very first Wizz run and must improvise (raise the cap or drop sources). Nothing in SKILL.md step 5 says what to do when a cap is refused as too low.
- **Fix:** Suggest USD 8–10 for flights + lodging, and add to step 5: "If the platform refuses the cap as too low, ask before raising it."

### F-10 — MINOR — brief.md asks for an `entrance=*` node but the only geocoder cannot search by tag; Overpass is limited to "One query per trip"
- **File / quote:** `patterns/brief.md` L20: "Geocode that entrance in OpenStreetMap: an `entrance=*` node or gate if one exists". `sources/overpass.md` L10: "One query per trip for the map's base layer". `sources/nominatim.md` L10: "read `class`/`type` to tell an entrance or pedestrian forecourt from a same-named road".
- **Scenario:** Unnamed entrance nodes are not returned by Nominatim; the agent either takes the forecourt (the evidence case, fine) or runs a second Overpass query, which the Overpass `how` reads as disallowed.
- **Fix:** In overpass.md allow "one base-layer query plus one small `node[entrance](around:…)` query for the anchor"; in brief.md say which source finds which.

### F-11 — MINOR — reading "the event's own visitor pages" has no sanctioned source
- **File / quote:** `patterns/brief.md` L19: "Take the entrance name from the event's own visitor pages (the fact's own record)". `sources/apify-page-render.md` L11: "Never use either mode to pre-render map tiles, to fetch listing pages, or to get past a site's own refusal; relay only requests the target's usage policy allows (see the router and map-data entries)."
- **Scenario:** An agent without its own web-fetch tool has no listed way to open websummit.com; a small model recalls the venue instead. brief.md's UNRESOLVED fallback handles the honest case, so no wrong result is forced.
- **Fix:** Add a `kind: reference` entry (or a line in brief.md) saying how to read a public event page, or state explicitly that the page-render relay may fetch one event page.

### F-12 — MINOR — Flow step 2 requires the connector that step 3 turns on
- **File / quote:** `SKILL.md` L40: "Read each actor's input schema before its first call." L41: "3. **Connector.** If the needed connector is off, ask for exactly that one, at that moment".
- **Fix:** Move the schema sentence into step 5 or say "once the connector is on".

### F-13 — MINOR — overlay folder question comes before the brief on a fresh install
- **File / quote:** `SKILL.md` L23: "Read this file. Resolve the user overlay (`patterns/adapt.md` §Overlay)." `patterns/adapt.md` L17: "If that folder does not exist yet, show the user the path and ask whether to use it or another folder".
- **Fix:** Resolve silently at load; ask about the folder only at step 8 when there is something to write.

### F-14 — MINOR — patterns require lookups (FX reference rate, tourist-tax rule, airline fee pages) with no `reference` source to do them
- **File / quote:** `patterns/flights.md` L10: "Convert each to the user's currency with a rate from a dated source you cite (a central-bank reference rate, or one the user gives)". `patterns/lodging.md` L20: "Find the rule, then check each listing's tax line against it". `sources/README.md` L10 lists `reference` as a kind; no entry has it.
- **Scenario:** The agent recalls ECB EUR/RON or the Lisbon €4/night rule. The Gap/UNRESOLVED rules keep it off the total, so no wrong number is forced, but "GROUNDED" on a tax line that matches a recalled rule is generous.
- **Fix:** Ship one `reference` entry per lookup (ECB daily rates URL; the city's tourist-tax page pattern) or say "ask the user for the rate".

### F-15 — MINOR — no rule separates "carrier does not fly this route" from a failure
- **File / quote:** `patterns/adapt.md` L28: "Mark an entry `broken` / `deprecated` | Autonomous | Two failures, or one unambiguous failure (actor removed, schema gone)".
- **Scenario:** Ryanair returns 0 rows for OTP→LIS; a small model logs a "failure" and, on the second route, marks the actor `degraded`.
- **Fix:** Add "0 rows on a route the carrier may not serve is not a failure; check the route exists first".

### F-16 — MINOR — page fallback assumes a polygon from the same source that just failed
- **File / quote:** `patterns/page.md` L14: "If no vector data is reachable, fall back to the boundary polygon and landmarks"; `patterns/lodging.md` L10: "take the polygon from OpenStreetMap vector data (the boundary relation or the ring road's ways) or from sourced gate coordinates".
- **Fix:** "…fall back to sourced gate coordinates or a radius; say the map is schematic."

### F-17 — MINOR — the daily cap of 5 is consumed by routine re-verification
- **File / quote:** `patterns/adapt.md` L36: "At most 5 autonomous changes per session (`sources.py` counts them per day from `CHANGELOG.md`)". `sources/README.md` L27: "After 90 days they read as stale until a run re-verifies them".
- **Scenario:** After 2026-12-23 every bundled entry is stale; a trip that uses 7 sources and re-verifies each with `set --last-verified today` hits the cap at the 6th and cannot record a real fix. Also `set --status working` does not bump `last_verified`, so an overlay entry can carry today's evidence with last year's date (README L14: "date of the evidence below").
- **Fix:** Exclude pure `last_verified`+`evidence` bumps from the cap; set `last_verified` automatically when `--evidence` is given with a working/degraded status.

### F-18 — MINOR — "Run it with the skill folder's path" reads as a positional argument; the script takes none
- **File / quote:** `patterns/adapt.md` L42: "Run it with the skill folder's path; `--help` lists the commands." Observed: `sources.py check /some/path` → "unrecognized arguments", exit 2.
- **Fix:** "Run it by its path (`python3 <skill>/scripts/sources.py …`); it finds the bundled sources itself."

### F-19 — MINOR — scraped datasets persist on the user's Apify account with all personal fields; invariant 5 covers only the local copy
- **File / quote:** `SKILL.md` L31: "Drop host and trader contact fields and review authors before saving anything."
- **Scenario:** The actor has already saved the full records to the user's Apify dataset. The skill's minimisation claim is narrower than it sounds. Household exemption likely applies to the user, so no illegal act is forced.
- **Fix:** One line in the notice or Close: "the raw dataset stays in your Apify account; delete it if you want the minimised copy to be the only one."

### F-20 — MINOR — "Photos are linked, not copied" is ambiguous between "link to the listing" and hotlinking image CDN URLs
- **File / quote:** `SKILL.md` L32: "**Photos are linked, not copied**, unless the user opts in". `patterns/photos.md` L9: "Each card links to its listing, and the listing shows the photos."
- **Fix:** In invariant 6: "cards link to the listing; no `<img>` to the platform's CDN".

### F-21 — MINOR — bundled `apify-google-flights` violates the skill's own `add` rule and the README's evidence comment
- **File / quote:** `sources/apify-google-flights.md` L8: `evidence: "listed in the store (579 users); not run in this session"`; `patterns/adapt.md` L27: "Add a new source entry | Autonomous | It passed one real run in this session"; `sources/README.md` L15: "needs a handle: URL, run/dataset ID, or quoted output".
- **Fix:** Either run it once before release or state in adapt.md that bundled `untested` entries are placeholders.

### F-22 — MINOR — polish
- `scripts/__pycache__/sources.cpython-311.pyc` is shipped in a public skill folder; delete it and add it to whatever packs the skill.
- `sources/nominatim.md` L10 example UA `trip-scout/2.1 (+https://github.com/bogheorghiu/skills)`: every stranger's agent will identify the author's repo to OSMF; that is what the policy wants (a contact for the application), so it is a design choice, but the author should know they are the abuse contact.
- Frontmatter comment in `sources/README.md` L9 `# = filename without .md` is parsed correctly by `unquote` (verified), but the README example is not itself a valid entry (`how:` etc. are placeholders); fine.

---

## Q2. `scripts/sources.py` vs `patterns/adapt.md` / `sources/README.md` — every mismatch found

| # | Doc says | Script does | Finding |
|---|---|---|---|
| 1 | adapt.md L47 exit 3 when not writable | As uid 0 with a non-creatable path: traceback, exit 1 | F-02 |
| 2 | adapt.md L35 never remove a caveat without evidence; L42 machine-checks the rules it can | `--caveats`/`--how` replace wholesale, no check | F-03 |
| 3 | adapt.md L25 status change needs run ID / URL / quoted error line | Any text accepted when the resulting status is `broken`/`deprecated`/`untested` | F-04 |
| 4 | adapt.md L27 `add` only after one real run | `add --status untested` with any evidence text accepted (help text L435 says "add a new entry that passed one real run this session", L338 allows untested) | F-04 / F-21 |
| 5 | adapt.md L28 broken needs two failures or one unambiguous one | Not checked (not machine-checkable; adapt.md should say so) | F-04 |
| 6 | README L14 `last_verified` = date of the evidence | `set --status working --evidence …` leaves the old `last_verified` | F-17 |
| 7 | adapt.md L42 "Run it with the skill folder's path" | No positional path; exit 2 if given | F-18 |
| 8 | adapt.md L34 forbids residential/rotating proxies | Regex misses "proxy group residential", "useApifyProxy" | F-08 |
| 9 | adapt.md L36 "5 autonomous changes per session (… per day)" | Matches (verified: 6th write refused, dry-run still allowed). Drop-only additions count too — adapt.md does not say whether they should. | F-17 |
| 10 | adapt.md L17 `where` prints "whether it is writable" | Prints `writable: True` for `/proc/nope/x` as root | F-02 |

Verified as matching: `check` validates bundled + overlay and exits 1 on any invalid entry; `list` shows stale (tested with `--today 2027-01-01`) and shadowed flags; `set`/`add` write only `<overlay>/sources/<id>.md` and append the `date | file | change | evidence | note` line in the documented format; `--dry-run` prints diff + log line and writes nothing; the drop-removal guard works exactly as adapt.md describes (`--allow-drop-removal` + `--reason` + evidence, recorded as `drop_removed:`); refusals name the rule and next step; control characters and `|` in fields are refused; the resulting entry is validated before any output.

## Q3. Cross-file consistency — contradictions with both sides quoted

1. `patterns/brief.md` L20 "an `entrance=*` node or gate" vs `sources/overpass.md` L10 "One query per trip" and Nominatim's tag-blind search (F-10).
2. `patterns/page.md` L14 "fall back to the boundary polygon" vs `patterns/lodging.md` L10 polygon "from OpenStreetMap vector data" (F-16).
3. `patterns/adapt.md` L27 "It passed one real run in this session" vs bundled `sources/apify-google-flights.md` L8 "not run in this session" (F-21).
4. `SKILL.md` L40 "Read each actor's input schema before its first call" (step 2) vs L41 connector requested in step 3 (F-12).
5. `SKILL.md` L3 "within legal limits" vs `reference/legal.md` L86 "Treat … as unknown" and L9 "not on the permitted list even for private use" (F-07).
6. `patterns/brief.md` L10 "about USD 5" vs `sources/apify-wizzair.md` L10 "refused a spend cap under $0.60" × ~10 runs (F-09).

Checked and consistent: invariant 5 ↔ Booking `drop: … hostInfo.* except name` ↔ page.md L48 "no host names" on a shared page; invariant 7 ↔ page.md "never from pre-rendered tiles" ↔ legal.md tile policy; invariant 8 ↔ lodging.md "Never trace it from a map image"; invariant 9 tags ↔ lodging.md §5 and flights.md §2; lodging.md "one batched request" ↔ osrm `how` "Two requests cover a whole trip" (table + route); page.md attribution + fix-the-map ↔ FOSSGIS policy excerpt; photos.md private-only ↔ page.md L48; apify-page-render "A relay run is a paid run … comes after the notice" ↔ SKILL.md step 4; stale-90-days in adapt.md ↔ README ↔ script `STALE_DAYS = 90`.

## Q4. Legal/policy statements vs how the sources use each service

- **Nominatim:** policy as quoted (≤1 req/s, identifying UA, cache, no bulk/grid, no personal data, LLM must name the policy, Apify named as a reseller) ↔ nominatim.md `how`/`caveats` and apify-page-render.md "Never for Nominatim". **Consistent.** Gap: nothing stops a later overlay `how` from re-enabling the relay (F-08).
- **FOSSGIS/OSRM:** "One request per second max", "valid user agent", "No scraping, no heavy usage", attribution + fix-the-map ↔ two requests per trip, UA in `how`, page.md L20 attribution and link. **Consistent.** The relay through a headless-browser actor sends the UA per the 2026-09-24 evidence; whether the UA actually reached the service is not provable from the run ID alone (NOT-COVERED).
- **Overpass:** identify the app, no parallel scripts, ≤10k queries/day one-off ↔ one query, UA, 30 s back-off on 429/504, never loop. **Consistent.**
- **OSM tiles:** not used at all; the only OSM link is a card link to openstreetmap.org (not a tile fetch). **Consistent.**
- **ODbL:** legal.md's Produced Work / Substantial reasoning ↔ page.md "shipped as a local `streets.js` with an ODbL notice beside it" ↔ overpass.md caveats. **Consistent**, and correctly marked UNRESOLVED as a legal conclusion.
- **GDPR:** Art. 2(2)(c) household + Lindqvist ↔ invariant 5 and page.md L48. **Consistent**; the Apify-side dataset retention is not mentioned (F-19).
- **Platform ToU (Ryanair/Wizz/Airbnb/Booking/Google):** legal.md says extraction is outside the terms even for private use; the flow proceeds after a yes. **Internally consistent and honest; policy-breaking by design** (F-01).
- **CFAA case:** described as non-precedential either way; the skill draws no comfort from it. Factual accuracy of the docket history could not be checked from inside the folder (NOT-COVERED).

## Q5. Well done — should not change

- The three-layer model with the overlay never touching bundled files, and "future sessions read the overlay as instructions … Quote at most one line of error text; never paste listing or page content into an entry" (adapt.md L37): explicit prompt-injection hygiene for a self-updating skill.
- Evidence tags with "Prices are GROUNDED only as of the scrape date" and the Gap rule "never estimate it into a total" (flights.md L9).
- Invariant 3 as written: "Never escalate proxies, retries, header spoofing or CAPTCHA solving in response to a refusal. Stop and report instead."
- The Nominatim reseller clause found, applied, and the LLM-disclosure duty honoured in `how`.
- Per-run spend cap from the remaining budget, and "if the connector has no cap field, say so and ask before each run".
- Script quality: atomic writes, validation before dry-run output, refusals that name the rule and the next step, drop-removal audit trail in the entry itself, `--today` for staleness tests, and `check` as the load-time guard that survives hand edits.
- lodging.md L16: routed distances computed once, "so map, cards, charts and the bottom line cannot disagree", and the explicit ban on straight-line stand-ins.
- legal.md's habit of tagging its own claims (GROUNDED / UNRESOLVED / Gap) including the unread German policy.

---

## Verdict against the bar

**BLOCKING count: 1 (F-01), and it is the skill's declared premise rather than an error.** Money-without-consent: none found. Failed run: none that stops the trip (F-02 only breaks the optional adapt step). Wrong-result paths: F-03, F-05, F-06 are MAJOR because each needs either a second session or a truncated run plus an incurious agent.

- Strict reading of the bar ("breaking a web service's published usage policy" is BLOCKING regardless of disclosure): **FAIL** on F-01 alone.
- If consented ToU breach with no circumvention is accepted as the skill's scope: **PASS**, with 6 MAJOR (F-02…F-07) and 15 MINOR to fix.

## NOT-COVERED

- Whether the six Apify actors exist under those names today, their input schemas, per-result pricing, and whether the connector's `call-actor` exposes a spend-cap field (could not read outside the folder).
- Whether Ryanair actually serves OTP–LIS; whether Web Summit 2026 runs 9–13 Nov; the current Lisbon tourist-tax rule.
- Accuracy of the legal citations (C-30/14 quote, D. Del. docket numbers, 3d Cir. dismissal date, OSMF guideline wording).
- Whether the page-render relay's `userAgent` field reaches Overpass/OSRM (only the run ID is in evidence).
- Behaviour on Windows paths, `CLAUDE_PLUGIN_DATA` resolution, and Python < 3.11.
- Exit-3 path as a non-root user (as uid 0 `os.access` never returns False; the non-root branch is untested here).
- The photo recipe (Pillow crop) end to end.

## Least sure

F-01's severity. The bar names ToU breach as BLOCKING and the skill's own legal.md concedes the breach, so I recorded it; but the skill discloses it, forbids circumvention, and treats it as a civil, consented risk — a reviewer who scoped "policy-violating" to services with usage policies the agent itself hits (OSM stack) would not count it, and then the verdict is PASS.
