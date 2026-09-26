# trip-scout review 3 — findings

Reviewed folder: `<scratch>/review3/trip-scout/`
Reviewer: fresh reader, no prior contact with the skill. Date: 2026-09-25. Nothing outside the folder was read; the script was run only against temporary overlays under the scratchpad (and once against a *copy* of the skill folder).
Bar (pre-registered): BLOCKING = wrong result shown / money spent without consent / failed run / undisclosed illegal act or policy breach. MAJOR = likely confusion a careful agent works around but a typical one would not. MINOR = polish. PASS = zero BLOCKING.

Files read (all 20): SKILL.md, LICENSE, reference/legal.md, patterns/{adapt,brief,flights,lodging,page,photos}.md, sources/{README,apify-airbnb,apify-booking,apify-google-flights,apify-page-render,apify-ryanair,apify-wizzair,nominatim,osrm-fossgis,overpass}.md, scripts/sources.py (516 lines).

Script runs performed (TRIP_SCOUT_HOME → temp folders): `--help`, `set --help`, `where`, `check`, `list`, `check --today 2027-01-01`, `check --today 2026-09-20`; `set`/`add` with: no evidence; vague evidence; quoted error fragment; 17-char run id; shrinking drop list; growing drop list; `how` containing "cookies"; `how` containing proxy/captcha/retries/stealth/UA-spoof wording; `how` relaying Nominatim through Apify; `--caveats` without `--reason`; `add` lodging without `--drop`; `add` with empty how/caveats; bad id `../SKILL`; evidence with nested quotes; `--status untested` with vague evidence; future `--last-verified`; 5 changes then a 6th; `verify` after cap; `add` after cap; `--dry-run` after cap; hand-written overlay entry with an extra body line and a lost drop field; overlay path = regular file (exit 3); overlay path = copy of the skill folder; hand-written CHANGELOG lines in adapt.md's format; default overlay path with no env vars.

---

## Q1. Flow walk-through as a small model: "Cheapest way Cluj→Porto, conference at Alfândega do Porto 2–5 March, flat within walking distance, just me"

| Step | File opened | What the agent asks / does | Money | What could go wrong |
|---|---|---|---|---|
| Load | SKILL.md → patterns/adapt.md §Overlay | Resolves overlay silently (`sources.py where`) | 0 | If the user later sets `TRIP_SCOUT_HOME` to the skill folder itself, `set` edits bundled files (R-02). |
| 1 Brief | patterns/brief.md | One batched question: whose trip; spend budget in USD (suggests 8–10); page currency; nights (2–5 March → arrive 1 or 2 Mar? leave 5 or 6? "offer both readings"); tickets vs people ("just me"); route CLJ→OPO, direct-only?, alt airports?; baggage; lodging type + must-haves; anchor = the venue's *visitor entrance* from the event's own page; "walking distance" → a radius around the anchor; ceiling. | 0 | The anchor needs the conference's own web page (brief.md L19) and an OSM object (L20). SKILL.md `compatibility` names no web-fetch tool, so a sandbox with only Apify + a publisher has no stated way to read the event page; the anchor becomes UNRESOLVED (brief.md L22 handles this honestly). |
| 2 Sources | scripts/sources.py `check`; sources/README.md; then 9 entry files | Picks flight-calendar (ryanair, wizzair), flight-aggregator (google-flights, *untested*), lodging (airbnb, booking), router (osrm), vector-data (overpass), geocoder (nominatim), page-render (relay). | 0 | Nothing tells the agent which carriers actually fly CLJ–OPO before paying for calendar runs (R-04). A machine clock behind the bundled `last_verified` dates makes `check` demote every entry to untested (R-13). |
| 3 Connector | SKILL.md | Asks for Apify if off. | 0 | – |
| 4 Notice | reference/legal.md | Tells the user in a few sentences that platform terms generally forbid automated extraction, that a third-party actor runs it, that the law is EU-contract/US-CFAA-unsettled; waits for yes. | 0 | Well done. Nominatim needs a *separate* one-line notice before its first lookup (nominatim.md L10) which a small model may skip since Flow step 4 says nothing about it (R-08). |
| 5a Flights | patterns/flights.md; apify-ryanair.md; apify-wizzair.md; apify-google-flights.md | Reads each actor's input schema; runs Ryanair and Wizz calendars ±3 days, both directions; then one Google Flights run (untested → verify on first use). Sets cap per run from budget left; if no cap field or cap refused, asks. Builds all-in price (fare + bags + seat + FX); bag fees not looked up are Gaps. | ~3 runs, ≥ $0.60 each (wizz refused a cap under $0.60) | Wizz returns RON outbound / EUR inbound (caveat covers it). If a carrier doesn't serve the route the run is wasted and the "cheapest" set is incomplete (R-04). Bag fee / FX rate verification has no named source or tool (R-05). |
| 5b Lodging | patterns/lodging.md; apify-booking.md; apify-airbnb.md; osrm-fossgis.md; overpass.md; nominatim.md; apify-page-render.md | Booking: `search`="Porto", one run per propertyType (Apartments, maybe Guest houses = 2–3 runs). Airbnb: map-box URL with dates/adults/currency/maxResults (1 run). Geometry filter by radius. Router: two OSRM requests (table + route); if the sandbox is blocked, relay via page-render URL mode (paid, after notice). Tax rule for Porto reconciled or Gap. Drop host fields. | 3–4 lodging runs + up to 3 relay runs (2 OSRM + 1 Overpass) | Budget of $8–10 is tight for ~10 runs at a $0.60 floor; brief.md warns ("5–8 paid runs"), and Flow 5 makes the agent ask when a cap is refused, so no silent overspend. Booking city-wide run at its cap is a sample (caveat says so). |
| 6 Shortlist | chat | Corrections. | 0 | – |
| 7 Page | patterns/page.md (+photos.md only if opted in) | SVG map from Overpass `streets.js` (ODbL notice), entrance pin, routed minutes chips, scatter, bars, cards, flights table, before-you-book, sources. Private page may show host display names. | 0 (Overpass relay already counted) | A radius constraint must be "drawn on the page" (lodging.md) but page.md says "No circles" (R-06). |
| 8 Adapt | patterns/adapt.md; sources.py `set`/`add` | Records failures/successes with run IDs; ≤5 changes/day. | 0 | Script gaps in R-01..R-03, R-09..R-12. |
| 9 Close | SKILL.md | What wasn't checked; connector retains raw run data; assumption to press; next step. | 0 | – |

Money is never spent before the step-4 yes and the step-1 budget; every paid path (actors, page-render relay, photo renders) is labelled as paid in its own file. I found no path to money without consent.

---

## Findings

### R-01 · MAJOR · scripts/sources.py FORBIDDEN filter is narrower than invariant 3 and than the docstring claims
- **sources.py L12–13 (docstring):** "refuse the mistakes such an agent actually makes (vague evidence, a lost drop field or caveat, a sixth change in a day, a forbidden technique written into `how`)"
- **SKILL.md L29 (invariant 3):** "Never escalate proxies, retries, header spoofing or CAPTCHA solving in response to a refusal."
- **sources.py L57–59:** `FORBIDDEN = re.compile(r"\b(log[- ]?ins?|logged[- ]in|sign(?:ed)?[- ]?in|passwords?|cookies?|session[- ]tokens?|auth[- ]tokens?|captchas?|residential[- _]?prox\w*|rotating[- _]?prox\w*|proxyconfiguration|apifyproxygroups)\b", re.I)`
- **Observed (dry-run, all accepted, exit 0):** `--how 'raise maxRequestRetries to 20, enable stealth, spoof User-Agent as Chrome'`; `--how 'set anticaptcha=true and 2captcha key'` (the `\b` before "captcha" fails inside "2captcha"/"anticaptcha"); `--how 'proxy: {useApifyProxy: true, groups: [RESIDENTIAL]} worked'`; and, for the nominatim entry, `--how 'Relay through apify-page-render URL mode when sandbox blocks it'` (forbidden by nominatim.md L11 and legal.md L32–33). Meanwhile the benign `--how "Do not send cookies; use defaults"` is refused.
- **Failure scenario:** a tired agent that got past a refusal by bumping retries or a UA string records it in `how` as "what worked"; the next session reads `how` as instructions (adapt.md L37) and repeats the escalation, now with no refusal at the moment of the mistake — the exact case the docstring says the script exists for.
- **Fix:** extend the pattern with `retr(y|ies)`, `stealth`, `spoof`, `\w*captcha\w*`, `useapifyproxy`, `proxy[- ]?(group|country)`, `relay` (for `connector: web` entries whose caveats forbid it, or at least for id `nominatim`), and say in adapt.md §The tool that the filter is a keyword net, not a guarantee.

### R-02 · MAJOR · An overlay pointed at the skill folder edits bundled files and hides the bundled baseline
- **patterns/adapt.md L11:** "changes go to a user-owned overlay, never into the bundled files."
- **patterns/adapt.md L17:** "If they pick another, tell them to set `TRIP_SCOUT_HOME`"
- **sources.py L73–80** resolves `TRIP_SCOUT_HOME` with no check against `SKILL_DIR`.
- **Observed (on a copy of the skill):** with `TRIP_SCOUT_HOME=<copy of skill folder>`, `where` reports writable; `list` shows every bundled entry as layer `overlay`; `set apify-ryanair --status broken --evidence "run ByRsawBRFr3ntuQi3"` rewrote `sources/apify-ryanair.md` in place and created `CHANGELOG.md` at the skill root.
- **Failure scenario:** the honest choice "keep the overlay with the skill" makes `bundled_entry` and `overlay` the same object, so the drop-list guard (`validate` L213–218) and the "shadowed" warning become vacuous, and a skill update silently discards the changes.
- **Fix:** in `overlay_dir()` or `apply_change`, refuse (exit 1 with a message) when the resolved overlay equals or is inside `SKILL_DIR`.

### R-03 · MINOR · adapt.md "propose-only" wording implies `--dry-run` returns exit 3
- **patterns/adapt.md L47:** "`--dry-run` prints the diff without writing. Exit code 3 means the overlay is not writable: show the user the printed diff (propose-only)."
- **Observed:** `--dry-run` always exits 0 and never tests writability (sources.py L450–452); exit 3 comes from a real `set`/`add` (L468–470) or `where` (L244), each printing the diff.
- **Failure scenario:** an agent running `--dry-run` first "to see if the overlay is writable" learns nothing and is surprised on the real write; harmless but confusing.
- **Fix:** split into two sentences: "`--dry-run` prints the diff and CHANGELOG line, exit 0. A real `set`/`add` (or `where`) exits 3 when the overlay is not writable and prints the same diff: show it to the user."

### R-04 · MAJOR · No route-existence step before paid calendar runs
- **patterns/flights.md L8:** "Pull ±3 days around each date, in both directions, from the `flight-calendar` sources that match the route."
- **patterns/adapt.md L28:** "Zero results on a route the carrier may not fly, or for dates not yet on sale, is not a failure: check that first" (says *check*, not where or how).
- **Failure scenario (Cluj→Porto):** the only way given to learn whether Ryanair or Wizz "match the route" is to pay for the calendar run. A typical agent runs both (≥ $0.60 each), gets zero rows from the carrier that does not serve CLJ–OPO, and if the untested Google Flights aggregator also fails, presents the survivor as "cheapest" from a set it never knew was complete. Money is within the consented budget, so not BLOCKING; the result can be incomplete without saying so unless step 9 catches it.
- **Fix:** add to flights.md step 1: "Before a calendar run, confirm the carrier lists the route on its own route map / destinations page (free, GROUNDED); if you cannot check, say so and let the user decide whether to spend the run." Optionally a `kind: reference` entry for each carrier's route page.

### R-05 · MINOR (least sure, see end) · "Verify, don't recite" has no verification path for bag fees, tourist-tax rules or FX rates
- **patterns/flights.md L9:** "A fee you didn't look up for this route and date is a **Gap**; never estimate it into a total."
- **patterns/flights.md L11:** "Check the low-cost traps for each airline. Verify them; don't recite them."
- **patterns/lodging.md L20:** "Find the rule, then check each listing's tax line against it"
- **patterns/flights.md L10:** "with a rate from a dated source you cite (a central-bank reference rate, or one the user gives)"
- **SKILL.md L5 (compatibility):** "Needs a scraping connector (Apify or equivalent) and a tool that publishes an HTML page."
- No `kind: reference` source is shipped and page-render caveats (apify-page-render.md L11) forbid using the relay "to fetch listing pages"; whether an airline's fee page or a city's tax page counts is unstated.
- **Failure scenario:** a small model with no web-fetch tool either tags everything Gap (honest, but the "cheapest all-in" answer degenerates to bare fares) or, more likely, recites bag fees from training and tags them GROUNDED because nothing names an allowed lookup route.
- **Fix:** name the allowed lookup route (a plain web fetch of the airline's/ city's own page; the relay in URL mode is acceptable for a policy page that is not a listing) and say in flights.md step 3 that a recited figure is UNRESOLVED at best.

### R-06 · MINOR · lodging.md "draw the boundary" vs page.md "no circles" for a radius constraint
- **patterns/brief.md L23:** "Turn 'central, toward the venue' into something testable: a radius around an anchor, a named boundary…"
- **patterns/lodging.md L11:** "Draw the boundary on the page so the user can judge it."
- **patterns/page.md L16:** "No circles or other straight-line isochrones; true isochrones only if computed by a router."
- **Failure scenario:** for this trip the constraint *is* a radius ("walking distance"). A typical agent either omits the boundary (losing the "inside/outside" fill's visual meaning) or draws the circle and worries it broke a rule.
- **Fix:** page.md: "No circles *presented as walking-time isochrones*; a radius that is the user's own constraint may be drawn, labelled 'search radius (straight line)'."

### R-07 · MINOR · overpass.md "at most two queries per trip" vs lodging.md boundary polygon
- **sources/overpass.md L10:** "At most two queries per trip: one small `node[entrance](around:300,LAT,LON)` query for the venue anchor … and one for the map's base layer"
- **patterns/lodging.md L10:** "For a named boundary, take the polygon from OpenStreetMap vector data (the boundary relation or the ring road's ways)"
- **Failure scenario:** a named-district constraint needs a third query (or a wider base-layer bbox that includes the relation). Not this trip's case; a careful agent folds it into the base-layer query.
- **Fix:** overpass.md: "…two or three queries per trip: …, and, for a named boundary, one for the boundary relation."

### R-08 · MINOR · The Nominatim notice is a second, separate consent step not visible from SKILL.md's Flow
- **sources/nominatim.md L10:** "Before the first lookup, tell the user in one line that this is OpenStreetMap's public geocoder, that its usage policy … allows only light, identified, non-bulk use, and that its data is ODbL. The policy requires an LLM that suggests the service to say this."
- **reference/legal.md L31:** "LLMs may only suggest this service, if they prominently point to this usage policy and explain the restrictions of use to the user."
- **SKILL.md L42 (Flow 4):** only "what `reference/legal.md` says about platform terms and scraping".
- **Failure scenario:** a small model that geocodes the anchor in step 1 (brief.md L20) has not yet opened nominatim.md, so the policy-mandated line is skipped. Not undisclosed to the *skill author* (it is written), so not BLOCKING; a typical agent misses it.
- **Fix:** SKILL.md Flow 4 or brief.md L20: "Nominatim has its own one-line notice (`sources/nominatim.md`); give it before the first lookup."

### R-09 · MINOR · `add` accepts empty `how:` and `caveats:` lines
- **sources/README.md L17–18:** "how: what input shape worked / caveats: what the output does NOT mean"
- **sources.py L202–204** checks only presence of the key; **L418** template is `"---\n---\nhow: \ncaveats: \ndrop: —\n"`.
- **Observed:** `add apify-hotels --kind lodging --connector apify --target foo/hotels --status working --evidence "run ByRsawBRFr3ntuQi3" --drop host` wrote `how: ` and `caveats: ` (empty) and `check` reported 0 invalid.
- **Fix:** for `add`, require non-empty `--how`; for `working` status also require non-empty `--caveats` or accept `--caveats "none observed"` explicitly.

### R-10 · MINOR · Nested double quotes in evidence are refused and tempt a reword
- **patterns/adapt.md L46:** "If you believe a refusal is a false positive, tell the user; do not reword and retry."
- **sources.py L53:** `"|[\"“][^\"“”]{20,}[\"”]"` — the quoted fragment may not itself contain a quote.
- **Observed:** `--evidence '"error: "cap too low" from platform"'` → REFUSED "…Copy it from the run; do not invent one." A genuine error line containing quotes is a normal case; the message tells the agent it invented it.
- Also cosmetic: an accepted quoted fragment is written as `evidence: ""Actor … timed out""` (double-double quotes; `check` still passes).
- **Fix:** allow inner quotes (`[\"“](?:[^\"“”]|\"(?=[^\"]*\"))…`) or accept a 20+-char fragment in single quotes; don't double-wrap an already quoted value.

### R-11 · MINOR · Hand-written CHANGELOG lines in adapt.md's own format may not count toward the cap
- **patterns/adapt.md L55:** "`YYYY-MM-DD | file | change | evidence | session note`"
- **sources.py L291:** counts lines with `"| sources/" in ln`.
- **Observed:** five hand-written lines `2026-09-25 | apify-ryanair.md | set … |` did not count; a sixth `set` via the script succeeded.
- **Fix:** adapt.md: "file is written as `sources/<id>.md`"; or count `| ` + `<id>.md` too.

### R-12 · MINOR · `set --evidence` stamps `last_verified` with today's date even when the run was earlier
- **sources/README.md L14:** "last_verified: … date of the evidence below, not of the last edit"
- **sources.py L353–355:** `elif values["evidence"] is not None: front_updates["last_verified"] = on.isoformat()`
- **Failure scenario:** citing yesterday's run without `--last-verified` records a wrong date by one day. Trivial.
- **Fix:** `--last-verified` help text: "defaults to today; pass the run's date if earlier".

### R-13 · MINOR · A machine clock behind the bundled dates demotes the whole registry
- **sources.py L198–199:** `elif d > on: e.append(f"last_verified {lv} is in the future")`
- **Observed:** `check --today 2026-09-20` → 9 invalid, "treat invalid entries as untested this session".
- **Failure scenario:** a container whose date is wrong (it happens) or a release installed on the day of its verification in a UTC-12 timezone; the agent then treats every source as untested and proceeds anyway, which is safe but noisy.
- **Fix:** make "in the future" a WARN when the gap is ≤ 2 days.

### R-14 · MINOR · Invariant 3 "use actor defaults" vs entries that set `userAgent`
- **SKILL.md L29:** "Use actor defaults. Never escalate proxies, retries, header spoofing…"
- **sources/apify-page-render.md L10:** "`userAgent` naming the application"
- **sources/osrm-fossgis.md L10:** "a relay is acceptable only if it sends that User-Agent"
- Not a real contradiction (an identifying UA is required by the OSM policies and is the opposite of spoofing), but a literal small model may see "non-default header" = violation, or conversely take "set userAgent" as licence to set a browser UA.
- **Fix:** invariant 3: "An identifying User-Agent required by a service's policy is not spoofing; a browser-imitating one is."

---

## Q2 summary: does sources.py behave as adapt.md / README say?

Matches (verified): overlay resolution order and `where`; `check` flags missing keys, bad enums, future/invalid dates, stale >90 days (warn), unexpected body lines, lodging without drop, evidence without handle, lost drop fields vs bundled baseline, shadowed dates; `set` refuses status/how/caveats changes without evidence, vague evidence (non-untested), shrinking drop lists without `--allow-drop-removal --reason`, `--caveats` replacement without `--reason`, ids outside `[a-z0-9-]`, line breaks in values; `add` refuses existing ids, statuses other than working/untested, lodging without drop; the 5/day cap counts `set`/`add` and not `verify`; `--dry-run` writes nothing; non-writable overlay (a file path) → exit 3 with the diff printed; propose-only message matches adapt.md.

Mismatches: R-01, R-02, R-03, R-09, R-10, R-11, R-12, R-13.

## Q3 cross-file contradictions (both sides quoted)
R-06 (lodging.md L11 vs page.md L16), R-07 (overpass.md L10 vs lodging.md L10), R-14 (SKILL.md L29 vs apify-page-render.md L10 / osrm-fossgis.md L10), R-03 (adapt.md L47 vs sources.py L450–470), R-11 (adapt.md L55 vs sources.py L291), R-12 (README L14 vs sources.py L353–355). No contradiction found between the invariants and any source entry's `how`; the drop lists match invariant 5 (Booking keeps `hostInfo.name`, Airbnb keeps `host.name`, both "public display name" only).

## Q4 legal/policy statements vs how sources use each service
- Nominatim: legal.md L31–33 ↔ nominatim.md L10–11 ↔ apify-page-render.md L10 "Never for Nominatim" — consistent; the reseller clause is honoured. Notice placement is the only weakness (R-08).
- FOSSGIS OSRM: legal.md L29 ↔ osrm-fossgis.md L11 (1 req/s, UA, attribution, fix-the-map) ↔ page.md L20 (attribution + fix-the-map link) — consistent; two requests per trip is far under "heavy usage".
- Overpass: legal.md L30 ↔ overpass.md L10–11 (UA, no parallel, ≤2 queries, 30 s back-off) ↔ page.md L14 (ODbL notice on `streets.js`) — consistent; the Substantial-extract reasoning is honestly tagged UNRESOLVED (legal.md L28).
- OSM tiles: invariant 7 ↔ page.md L13 ↔ page-render caveat "Never … to pre-render map tiles" — consistent.
- Platforms (Ryanair, Wizz, Booking, Airbnb, Google Flights via Apify): the disclosed premise (invariant 2, Flow 4, legal.md). Google is not named in legal.md but the notice is generic ("Platform terms generally forbid automated extraction"), so it is covered.
- GDPR: legal.md L21 ↔ invariant 5 ↔ page.md L48 (shared page carries no host names) ↔ lodging.md L29 — consistent.
- Photos: photos.md L11 states the copyright risk before opt-in — consistent with the "disclose before acting" stance.
No undisclosed policy breach found.

## Q5 well done — do not change
- The three-layer model with a machine-enforced write boundary (`ID_RE`, overlay-only writes, refusal messages that name the rule and the next step). The refusal texts are the best I have seen in a skill: each says what to do instead.
- "Log first, then write" (sources.py L458–459) and validating the *resulting* entry before any output path (L430–435), so dry-run and real write cannot disagree.
- The honest threat model in the docstring (L9–15).
- Evidence tags with a strict GROUNDED definition and "Prices are GROUNDED only as of the scrape date" (SKILL.md L35).
- Money hygiene: budget asked first, notice before the first paid run, per-run cap from budget left, explicit ask when the cap field is missing or refused, relay and photo runs labelled as paid (apify-page-render.md L11), and the close reminding the user that raw run data sits in their connector account.
- The anchor discipline (brief.md L18–22): entrance not centroid, event page not blog, OSM object id recorded, UNRESOLVED shown next to distances.
- Currency handling in wizzair.md L11 / flights.md L10: "never add the raw amounts".
- Nominatim reseller clause carried into three files, and the LLM-notice requirement quoted verbatim.
- Booking caveat "A city-wide run that stopped at its spend cap … is a sample, not the market".
- The "zero results is not a failure" guard in adapt.md L28.

## Verdict
**PASS** — zero BLOCKING. 3 MAJOR (R-01, R-02, R-04), 11 MINOR. Following the files as written does not plausibly spend money without consent, show a wrong result, fail a run, or breach a policy the user was not told about; the MAJORs concern the self-maintenance layer's guard rails and an avoidable wasted run.

## NOT-COVERED
- Whether the Apify MCP `call-actor` tool actually exposes a spend-cap field, and whether any listed actor is rental-priced (a subscription rather than pay-per-result). The skill's "if the connector has no cap field … say so and ask" covers the first; nothing covers the second. I did not read Apify docs (outside the folder).
- Whether Ryanair or Wizz Air serve CLJ–OPO; R-04 does not depend on the answer.
- The permission-denied branch of `writable()` on a real directory (sandbox runs as root; tested only with a file in place of the directory).
- Rendering of any page; `patterns/page.md` was reviewed as text only.
- Behaviour without Python ("apply the same rules by hand").
- `CLAUDE_PLUGIN_DATA` resolution (only `TRIP_SCOUT_HOME` and the XDG default were exercised).

## Least-sure finding
R-05. It rests on my guess of what a small model does when told to verify a fee with no tool named for it; the skill's explicit "never estimate it into a total" may be enough for most agents, in which case R-05 is only a missing how-to and not even MINOR-worthy.
