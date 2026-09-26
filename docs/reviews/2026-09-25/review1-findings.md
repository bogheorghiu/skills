# Review 1: trip-scout skill — findings

Reviewer: Claude (Fable 5.1), 2026-09-25
Folder reviewed: scratchpad/review1/trip-scout/ (17 files, 384 lines). Every file read in full. No file edited.
Bar (pre-registered): BLOCKING = wrong result shown to user, illegal/policy-violating action, or failed run. MAJOR = confusion a careful agent works around but a typical one would not. MINOR = polish. PASS = zero BLOCKING.

## Verdict up front: PASS (0 BLOCKING, 7 MAJOR, 12 MINOR). Details and the checks run are below.

---

## Findings

### F1 — MAJOR — sources/apify-page-render.md:11 vs sources/osrm-fossgis.md:10 (and nominatim.md:8)
Quote A (page-render caveats): "Only for opt-in photos (patterns/photos.md). Never use it to pre-render map tiles."
Quote B (osrm how): "The cloud container's proxy blocked the host directly; fetching the URL through the page-render source (URL mode, `extract:["text"]`, a descriptive User-Agent) worked."
Quote C (nominatim evidence): "Direct curl/WebFetch from the cloud container were blocked (proxy 403 / robots.txt); a fetch relay worked."
What goes wrong: the router entry tells the agent to use the page-render actor as an HTTP relay; the page-render entry forbids any use other than photos and documents only `mode: screenshot` + `html` (no "URL mode", no `extract`). An agent that reads entries in registry order refuses the relay and shows no walking figures; one that reads osrm first pays for screenshot-actor runs whose input keys it has never seen documented. Either way behaviour differs by read order. The nominatim "fetch relay" is not even named.
Fix: either (1) add a second `how` mode to apify-page-render.md ("URL mode: `url`, `extract:["text"]`; also usable as a fetch relay for the geocoder/router when the sandbox blocks them") and soften the caveat to "Never for listing pages, map tiles, or anything the invariants forbid", or (2) drop the relay sentences from osrm/nominatim and let those entries say "if unreachable: ask the user or use listing coordinates" (nominatim.md:11 already says this). Name the relay in nominatim.md:8 whichever way you go.

### F2 — MAJOR — sources/nominatim.md:8 (policy grey zone; the finding I am least sure of)
Quote: "Direct curl/WebFetch from the cloud container were blocked (proxy 403 / robots.txt); a fetch relay worked."
What goes wrong: the entry records, as positive evidence, that a robots.txt-based refusal was routed around. SKILL.md:29 (invariant 3) says "Never escalate ... in response to a refusal. Stop and report instead." and SKILL.md:34 requires a "policy-compliant geocoder". A stranger's agent will read "relay worked" as the recommended path. Whether one bounded, UA-identified request via a relay actually violates Nominatim's usage policy I could not check (outside the folder), so this stays MAJOR not BLOCKING; the policy itself (1 req/s, identifying UA, no bulk) is stated correctly in `how`.
Fix: reword evidence to the successful query only; move the reachability note to caveats as "If the sandbox cannot reach it, ask the user for the coordinate or use listing data. Do not proxy around a robots.txt refusal." That makes it consistent with invariant 3 and with nominatim.md:11.

### F3 — MAJOR — SKILL.md:27-28 vs SKILL.md:39-46 and patterns/brief.md:7-20
Quote (invariant 1): "Ask once whether the trip is for the user or their household."
Quote (invariant 2): "Tell the user before the first paid run."
Quote (Flow): "1. **Brief.** Run `patterns/brief.md` ... 3. **Connector.** If the needed connector is off, ask for exactly that one ... 4. **Search.** Run `patterns/flights.md` and/or `patterns/lodging.md`."
What goes wrong: neither the personal-use question nor the legal notice appears anywhere in the Flow or in brief.md's question list ("Ask only what changes the search"). A small model executing Flow steps in order will run the brief, turn on the connector and launch a paid actor without ever asking or warning; the invariants are stated but never sequenced. With strangers' money and platform-terms exposure this is the most consequential wiring gap.
Fix: add the household question as a bullet in brief.md ("Personal or household trip? (invariant 1)") and insert a Flow step between 3 and 4: "3b. **Notice.** Before the first paid run, give the one-paragraph notice from `reference/legal.md` and wait for a yes."

### F4 — MAJOR — SKILL.md:42 (spend cap without a value or an owner)
Quote: "Cap the spend on every run."
Quote (sources/apify-wizzair.md:10): "The platform refused a spend cap under $0.60."
What goes wrong: nothing says what the cap is, who sets it, or that the total across runs matters (lodging.md:8 requires 2+ platforms; apify-booking.md:10 requires one run per property type, so 5–8 paid runs is normal). A typical agent picks an arbitrary number per run or, if the connector's call tool exposes no cap field, silently runs uncapped.
Fix: "Ask the user for a total budget in the brief (default suggestion: USD 5). Per run, set the connector's maximum-charge field to (remaining budget ÷ runs still planned); if the tool has no such field, say so and ask before each run."

### F5 — MAJOR — patterns/flights.md:9,14 vs sources/apify-wizzair.md:11 (mixed currencies, no conversion rule)
Quote (wizzair caveats): "Currency follows the route (outbound RON, inbound EUR on OTP⇄BLQ)."
Quote (flights.md:9): "Build the all-in price for each option: fare + the baggage asked for + a seat only if needed + the currency effect."
What goes wrong: the only documented real route returns two currencies, yet no file says which currency the page presents in, where the FX rate comes from, or how to tag it. Invariant 8/9 forbid recall for coordinates and demand GROUNDED arithmetic, but an agent will add RON and EUR with a remembered rate and show one total. That is a number on the user's page with no evidence tag.
Fix: in flights.md add "Present all totals in the user's currency. Take the rate from a dated source you cite (or ask the user); tag converted totals UNRESOLVED with the rate and date shown; never add amounts in different currencies."

### F6 — MAJOR — patterns/page.md:14 (Overpass used but not a registered source)
Quote: "Base layer: real streets, railways and the venue footprint from OpenStreetMap vector data (e.g. Overpass `out geom`), simplified and shipped as a local `streets.js`"
What goes wrong: every other network dependency has a `sources/` entry with status, `how`, policy limits and `drop`; Overpass has none, so the adapt loop cannot record that it broke, no rate/UA policy is stated (Overpass has one), and there is no `kind` for it (README kinds: none fits except `reference`). Also sources/README.md:3 says the agent "picks sources by kind and status" — Overpass is invisible to that.
Fix: add `sources/overpass.md` (kind: reference or a new `vector-data` kind added to README:10) with the endpoint, `[out:json][timeout:25]; ... out geom;` shape, size limits, UA requirement, and the fallback already written in page.md:14.

### F7 — MAJOR — sources/README.md is referenced from nowhere; patterns/adapt.md:26 "Add a new source entry" has no schema pointer
Quote (adapt.md:26): "| Add a new source entry | Autonomous | It passed one real run in this session, and it respects the invariants |"
Quote (README:1-3): "# Source registry ... One file per source."
What goes wrong: SKILL.md never names sources/README.md, adapt.md never names it either, so the file holding the entry schema and the enums is reached only by an agent that lists the directory. An autonomously written entry with a wrong `status` value or a missing `kind` is then silently skipped by future resolution ("Prefer entries with `status: working`").
Fix: SKILL.md:40 → "Resolve ... from `sources/` (format: `sources/README.md`)"; adapt.md:26 → "...using the schema in `sources/README.md`".

### F8 — MINOR — SKILL.md:23 vs patterns/adapt.md:19 (overlay patterns are read too late)
Quote (SKILL.md:23): "Read this file. Then read the patterns the task needs. Then resolve sources: overlay entries override bundled ones with the same filename"
Quote (adapt.md:19): "Overlay layout mirrors the skill: `sources/*.md`, `patterns/*.md` (approved pattern edits only)"
What goes wrong: patterns are read before the overlay is resolved, so an approved overlay pattern is never picked up. Only bites users who have approved pattern edits.
Fix: SKILL.md:23 → "Resolve the overlay first (`patterns/adapt.md` §Overlay), then read patterns and sources with overlay files winning."

### F9 — MINOR — patterns/adapt.md:25 vs :34 (`drop` not in the autonomous-change list)
Quote (:25): "Update a source entry's `status`, `last_verified`, `caveats`, `how` | Autonomous"
Quote (:34): "Never remove a `drop` list entry or a caveat without evidence that it no longer applies."
Gap: adding a `drop` field (privacy-increasing) is not listed as allowed; removing is conditionally allowed. Say explicitly: "adding to `drop`: autonomous; removing: never autonomously."

### F10 — MINOR — patterns/adapt.md:14 (`${CLAUDE_PLUGIN_DATA}` unguarded)
Quote: "Running as a Claude Code plugin: `${CLAUDE_PLUGIN_DATA}/trip-scout/`"
Gap: if the variable is unset the path expands to `/trip-scout/`; a literal agent may try to mkdir at root before falling to propose-only. Add "if set" as in item 1.

### F11 — MINOR — patterns/adapt.md:17 ("ask once" has no memory)
Quote: "The first time, show the user the resolved path and ask once whether to use it or another folder."
Gap: the agent cannot know it is the first time. Say "if the overlay folder does not yet exist, ask; if it exists, use it silently."

### F12 — MINOR — sources/apify-google-flights.md:6-7 (`last_verified` on an untested entry)
Quote: "status: untested / last_verified: 2026-09-24"
Gap: nothing was verified. The validator (see (a)) should allow `last_verified: null` for `untested`, or README should define last_verified as "date of last status change".

### F13 — MINOR — sources/apify-ryanair.md:11 (self-contradictory sentence)
Quote: "With `allFlights:true`, every row carries the day's cheapest fare; only the `isDayCheapest:true` row is priced."
Gap: readable as "every row is priced" and "only one row is priced". The next sentence ("Tag other departure times' prices UNRESOLVED") rescues it. Reword: "every row's `price` field repeats the day's cheapest fare; it is the true price only on the `isDayCheapest:true` row."

### F14 — MINOR — sources/osrm-fossgis.md:10 (wording)
Quote: "One request for everything. Times+distances: `table/...`. Route lines: `route/...`"
Gap: that is two requests. patterns/lodging.md:16 says "one batched request for all listings". Say "one `table` request for all times/distances, plus one `route` request for all lines".

### F15 — MINOR — patterns/lodging.md:22 vs patterns/flights.md:9 (estimate vs Gap)
Quote (lodging): "there's no line: estimate the tax and flag it (UNRESOLVED)"
Quote (flights): "A fee you didn't look up for this route and date is a **Gap**; never estimate it into a total."
Gap: not a contradiction (the tax estimate follows a found rule), but lodging.md does not say what to do when the rule is not found. Add "no rule found: Gap, no estimate."

### F16 — MINOR — patterns/lodging.md:10 ("from a map image")
Quote: "trace a polygon from a map image or from sourced gate coordinates"
Gap: an unnamed "map image" is the one place the skill lets coordinates come from something other than data/user/geocoder (SKILL.md:34), and if the image is a tile it brushes invariant 7. Say "from OSM vector data (the boundary relation) or sourced gate coordinates".

### F17 — MINOR — patterns/page.md:47 (public demo without the privacy consequences)
Quote: "For a public demo, offer a language switch."
Gap: page.md never restates that a public/shared page must carry no host names (SKILL.md:31) and no copied photos (photos.md:15). One line in page.md would close it.

### F18 — MINOR — patterns/adapt.md:25 (untrusted text written into instructions)
Quote: "Evidence from this session: run ID, error text or URL"
Gap: actor error text and page content are untrusted; the overlay is read as instructions by future sessions. SKILL.md:25 does say invariants are never overridden, which bounds the damage. Add "quote at most one line of error text; never paste listing or page content into an entry".

### F19 — MINOR — sources/nominatim.md:8 & osrm-fossgis.md:8 (session-specific evidence in bundled files)
Quote (osrm): "...(e.g. 1250.1 m / 17 min, 3599.5 m / 48 min)."
Gap: the bundled entries carry Bologna-specific evidence and dates that will pass the 90-day line on 2026-12-24, after which every bundled entry is UNRESOLVED at once (adapt.md:36). That is by design, but say in README that bundled `last_verified` dates are the release's verification date, so a fresh user is not alarmed.

---

## Answers to the open questions

### (a) adapt.md limits: would an unfamiliar agent follow them; would a script help; what should it check
Following without enforcement: the qualitative rules (evidence in the changelog line, overlay-not-bundle, propose-only for patterns) are the kind of thing agents do follow because the format (adapt.md:42) forces a value into each slot. The two that slip are the count ("At most 5 autonomous changes per session", adapt.md:35 — models do not count across a long session) and staleness (adapt.md:36 — a 90-day subtraction on a date nobody re-reads). "Never remove a drop entry" (adapt.md:34) is safe as long as the agent edits rather than rewrites; a rewrite from memory is where entries vanish.

Yes, a stdlib-only script helps, and it should be small. I ran a prototype (scratchpad/check_sources.py, 60 lines, no PyYAML) against the bundled sources: all 8 pass, which also confirms id == filename, enums, dates and body keys for the shipped files. Concretely it should check, for bundled + overlay `sources/*.md`:
1. Frontmatter parses as flat `key: value` lines between the first two `---`; required keys {id, kind, connector, target, status, last_verified, evidence}.
2. `id` == filename stem.
3. `kind` ∈ README enum; `connector` ∈ {apify, zapier, brightdata, web}; `status` ∈ {working, degraded, broken, deprecated, untested}.
4. `last_verified` is an ISO date, not in the future; print STALE→UNRESOLVED when older than 90 days (do not fail; the skill's own rule is "re-verify").
5. `status: working` requires non-empty `evidence`; `untested` may have `last_verified: null` (see F12).
6. `connector: apify` → `target` matches `owner/name`; `connector: web` → `target` starts with https://.
7. Body has `how:`, `caveats:`, `drop:` lines; `kind: lodging` must have a non-empty `drop`.
8. Overlay vs bundled: for the same filename, every bundled `drop` token must still appear in the overlay's `drop` unless CHANGELOG.md has a line naming that file and the word "drop".
9. CHANGELOG.md lines match `YYYY-MM-DD | file | change | evidence | note`; count lines with today's date; fail above 5 (the session limit, approximated per day).
10. Warn (not fail) if a body mentions residential/rotating proxies, CAPTCHA or `proxyConfiguration` (invariant 3 / adapt.md:33).
Wire it in at Flow step 2 ("run `scripts/check_sources.py` if Python is available; otherwise check items 2–5 by eye") and at step 7 after every overlay write. Keep it advisory-plus-exit-code; a small agent obeys a red line from a script far more reliably than a sentence in a table.

### (b) Cross-file consistency — contradictions and gaps found
- F1 page-render "Only for opt-in photos" vs osrm/nominatim relay use (contradiction).
- F2 nominatim evidence vs invariant 3 "never escalate in response to a refusal" (tension).
- F3 invariants 1–2 vs Flow/brief (gap: never sequenced).
- F5 wizzair mixed currency vs no conversion rule (gap).
- F6 page.md Overpass vs no source entry (gap).
- F8 load order vs overlay patterns (ordering contradiction).
- F9 drop handling (gap in the permission table).
- F13, F14, F15 wording tensions.
Checked and consistent (no finding): invariant 5 ↔ booking `drop` "traderInfo (all), hostInfo.* except name, reviews authors" ↔ airbnb `drop` ↔ photos.md:16 "Never copy host portraits" ↔ legal.md:21; invariant 7 ↔ page-render caveat "Never use it to pre-render map tiles" ↔ legal.md:25; invariant 6 ↔ photos.md:9; photos.md:22-25 ↔ page-render `how` (screenshot/html/networkidle/delay 4/≤12) ↔ its evidence ("22-image grid timed out"); flights.md:18 ↔ ryanair caveat; lodging.md:16 "kind=router" ↔ osrm `kind: router`; lodging.md §5 tax reconciliation ↔ airbnb caveat "price.breakDown.taxes"; page.md:20 attribution ↔ osrm caveat policy text; brief.md:16 OSM entrance node ↔ nominatim `how` (`extratags`, class/type); SKILL.md:28 ↔ legal.md:9 on terms forbidding automated extraction; README enum ↔ every entry's values (validator-confirmed).

### (c) Does SKILL.md work as a standalone router?
Mostly yes. Each Flow step names the file to open, the layer table says who may change what, and the invariants are visible before any file reference. Three routing holes: sources/README.md is never named (F7); nothing tells the agent when to open reference/legal.md beyond "Details:" in invariant 2 — and since the notice step is not in the Flow (F3) it may never be opened; patterns/photos.md is reached only via invariant 6 and page.md:36, which is fine because it is opt-in. Load order sentence (SKILL.md:23) would be correct if overlay resolution came first (F8).

### (d) References — all one level deep from SKILL.md? Every one checked:
From SKILL.md: `patterns/` (dir, exists) :13; `sources/` (dir) :13; `patterns/adapt.md` :13,:21,:23,:45 (exists); `patterns/adapt.md §Overlay` :23 → heading "## Overlay (where changes are written)" exists; `reference/legal.md` :19,:28 (exists); `patterns/*.md` :20 (6 files); `sources/*.md` :21 (8 entries + README); `patterns/photos.md` :32; `patterns/page.md` :33,:44; `patterns/brief.md` :39; `patterns/flights.md` :42; `patterns/lodging.md` :42 — all exist. "the user overlay" :21 is external by design. All are one hop.
Second-hop references (from referenced files): apify-airbnb.md:11 → "patterns/lodging.md §5" → lodging.md numbered item 5 "Reconcile taxes" exists (not a heading; fine); lodging.md:16 → `patterns/brief.md` ✓, `sources/` kind=router → osrm-fossgis ✓; lodging.md:28 → "invariant 5" ✓; page.md:36 → `patterns/photos.md` ✓; photos.md:23 → page-render source ✓; apify-page-render.md:11 → `patterns/photos.md` ✓; flights.md:4 kinds flight-calendar (ryanair, wizzair ✓) and flight-aggregator (google-flights, untested) ✓; photos.md:5 tools python+pillow ↔ SKILL.md compatibility ✓; page.md:4 optional_skills dataviz/artifact-design — external, declared optional ✓. Missing target: page.md:14 Overpass (F6); osrm.md:10 "page-render URL mode" (F1). No dangling file references.

### (e) Other — including what is well done and should not change
Do not change: the invariant list at the top of SKILL.md (short, numbered, "never overridden"); the three-layer table with an explicit owner per layer; evidence tags with "Prices are GROUNDED only as of the scrape date"; lodging.md:16's flat ban on straight-line distances with a stated fallback ("show no walking figures at all and say so"); the `drop` lists as data rather than prose; the overlay design with a propose-only fallback and a one-line CHANGELOG format; the Ryanair `isDayCheapest` caveat and the ≤12-image limit both derived from recorded evidence; legal.md's honesty ("It is not precedent for either side", "Treat ... as unknown, and say so"); "Read each actor's input schema before its first call" (SKILL.md:40) which is the single line that saves F1 from being a failed run.
Spec conformance (from memory, spec site unreachable): name `trip-scout` matches folder, lowercase-hyphen; description 240 chars (<1024); compatibility 134 chars (<500); metadata values are strings (version is quoted); `reference/` singular instead of the spec's suggested `references/` — allowed, cosmetic.
Actor IDs (`tri_angle/airbnb-scraper`, `voyager/booking-scraper`, `kaix/google-flights-scraper`, `moonweil/url-screenshot-api`, `memo23/ryanair-scraper`, `memo23/wizzair-scraper`) were not verified against the store (out of scope); a wrong ID is a failed run, not a wrong number, and the skill's adapt loop is built for exactly that.

---

## Verdict
PASS against the pre-registered bar: zero BLOCKING. Seven MAJOR items, of which F3 (invariants 1–2 not wired into the Flow) and F4 (spend cap with no value or owner) matter most for a public release with real money; F1/F2 (the relay notes) matter most for policy cleanliness. Twelve MINOR.

## Checks run
- Read all 17 files end to end with line numbers.
- Enumerated every file/section reference from SKILL.md and from each referenced file; confirmed existence.
- Mechanically parsed all 8 source frontmatters (stdlib script): id==filename, enums, ISO dates, evidence presence, body keys, target shapes — 0 errors.
- Cross-checked each invariant (1–9) against every pattern and every source `caveats`/`drop`.
- Checked SKILL.md frontmatter field lengths and name format.
- Walked the Flow as a small model would (file open order) to find unsequenced obligations.

## NOT COVERED
- The agentskills.io spec page (egress blocked); spec limits applied from memory.
- Whether the six Apify actor IDs exist, their current input schemas, or whether the connector's call tool exposes a spend-cap field.
- Nominatim/OSRM/Overpass live usage policies and robots.txt (outside the folder).
- The legal citations in reference/legal.md (case numbers, dates, quotes) — not verified.
- No live run of any actor; no rendering of a page.
- Behaviour of the overlay on a real Claude Code plugin install.

## Least-sure finding
F2 (nominatim "fetch relay" as policy tension). It hinges on what Nominatim's robots.txt and usage policy actually say about a single identified request via an intermediary, which I did not fetch. If a bounded, UA-identified query is within policy regardless of path, F2 drops to MINOR wording; F1 (the page-render contradiction) stands either way.
