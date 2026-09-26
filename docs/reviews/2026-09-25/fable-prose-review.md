# Prose review: skills repo guidance (A) and trip-scout diff (B)

Reviewer: Fable 5.1, 2026-09-25. Branch claude/loving-euler-cn6vv6, nothing committed.
Doctrines applied: intrinsic-prompt-design, prompt-engineering, reserve-prose-for-what-code-cannot-say, rule-design.

## A. Edits applied

### README.md
- Overlay path list (`$TRIP_SCOUT_HOME`, else `$CLAUDE_PLUGIN_DATA/...`, else `~/.local/share/...`) cut to the default plus a pointer to `patterns/adapt.md`. It was a third copy of the resolution order (adapt.md and `sources.py:overlay_dir` hold it) and already drifted: it omitted `XDG_DATA_HOME`. Added "it asks before creating it", which a human deciding to install wants to know and adapt.md states.
- Contributing block: the `sources.py check` line now sets `TRIP_SCOUT_HOME=/tmp/empty` with a one-line comment, because CI runs it that way (`skills-ci.yml` line 28) and a contributor with a real overlay would otherwise get a result CI does not.
- Left: agent list on line 3, `npx skills add`, `gh skill install`, "GitHub CLI 2.90+" (external claims, unverifiable from this sandbox: cli.github.com, agentskills.io and skills.sh are egress-blocked; `gh` is not installed). Limits paragraph, licences, layout: verified, left as is.

### CLAUDE.md
- Evidence: cut "A secondhand summary never grounds a legal or policy claim; fetch the primary page" (a copy of bullet 1 of `ground-legal-and-policy-claims.md`) and pointed to that rule instead. CLAUDE.md keeps the general tagging convention, which applies to PR text and source entries where the rule does not load.
- Checks: "PII denylist guard" undersold the workflow (it also runs gitleaks, a history walk and a parity job). Now names the file and defers to its header instead of listing jobs, so the list cannot drift.
- Privacy: was a second always-loaded copy of `keep-personal-data-out.md` (both load every session). Reduced to the mechanics that rule does not hold, with two corrections: the hooks read `PII_DENYLIST` as an env var plus a gitignored file (not the Actions secret), and gitleaks runs in CI regardless of the denylist.
- Left: Rule 1, What is here, Who may change what, Publishing. Publishing step 2 verified against the gh manual (fetched via Exa): `--dry-run` validates, `--tag` publishes non-interactively, publish adds the `agent-skills` topic and creates a release. The "2.90+" version floor is not on that page: unverified, left.

### .claude/rules/keep-personal-data-out.md
- Added one sentence: the repository address `bogheorghiu/skills` is the install path, not personal data. Without it a literal reader (a small model) flags the README install commands and the Nominatim User-Agent example as violations of "no real names (the owner's included)".

### .claude/rules/respect-map-data-terms.md
- The "will get you banned" quote is verified (Nominatim policy, fetched 2026-09-25). Added: no Nominatim relay through Apify, because the same policy's Reselling bullet names Apify as an API reseller that must run its own service. Reworded the ban consequence with its mechanism (shared User-Agent).

### .claude/rules/verify-a-check-by-breaking-it.md
- "listed by name in `.github/workflows/skills-ci.yml`" was false for two of the suites the rule's own `paths:` cover: `layer-parity.test.sh` runs from `pii-denylist-guard.yml`, and `pre-push.test.sh` runs from no workflow at all. Fixed the pointer to "a workflow under `.github/workflows/`", allowed `bash <path>`, and named the unrun suite so the rule's own example is true.

### .claude/rules/ground-legal-and-policy-claims.md
- Last bullet restated CLAUDE.md's approval flow; now a pointer only (rule-design: compose, don't copy). Rest left: each bullet carries its failure mode in one sentence.

### .claude/rules/verify-skill-changes.md
- Left as is. Commands verified, levels distinct, the reason for open questions in blind review is the one sentence it needs.

## Claim checks

| Claim | Where | Verdict |
|---|---|---|
| Four contributor commands exist and run | README | GROUNDED: all four ran, exit 0 (check_skills 0 errors; sources.py 9 entries 0 invalid; 11/11; 23/23) |
| They are "the checks CI runs" | README | GROUNDED with a caveat: CI sets `TRIP_SCOUT_HOME` to an empty folder; README now does too |
| CI runs spec checks, source check, both suites on every push | CLAUDE.md | GROUNDED (`skills-ci.yml`, `on: push` unfiltered) |
| "plus the PII denylist guard" | CLAUDE.md | Incomplete: workflow has denylist, secrets (gitleaks), parity, history jobs. Fixed |
| PII guard reads secret and a gitignored file | CLAUDE.md | Half right: CI reads only the secret; hooks read env var + file. Fixed |
| `git config core.hooksPath .githooks` activates hooks | README, CLAUDE.md | GROUNDED (hook headers) |
| Demo loads data.js, streets.js, routes.js; EN/RO switch | README | GROUNDED (script tags; lang toggle in index.html) |
| Bologna, April 2027 | README | GROUNDED (data.js check_in=2027-04-04) |
| Python 3.8+ optional, runs the checker | README | GROUNDED (SKILL.md compatibility; sources.py docstring) |
| Stops for business trips; notice before first paid run; no login/book/pay; drops host data; links photos; no tiles | README | GROUNDED (invariants 1-7, flow 4) |
| Overlay path order | README | Drifted (no XDG_DATA_HOME). Replaced with pointer |
| Source list changes within limits a script checks; methods need approval; core by PR | README | GROUNDED (SKILL.md layers table, adapt.md table, sources.py) |
| Offers a ready-made PR text | README | GROUNDED (adapt.md §Log) |
| skills/trip-scout and demo code MIT | README | GROUNDED (skills/trip-scout/LICENSE is MIT; DATA-LICENSE assigns index.html/data.js to it) |
| streets.js/routes.js ODbL | README | GROUNDED (DATA-LICENSE) |
| Everything else Apache-2.0 | README | GROUNDED (root LICENSE) |
| `gh skill publish --dry-run` / `--tag` behaviour | CLAUDE.md | GROUNDED (cli.github.com manual via Exa) |
| GitHub CLI 2.90+ | README, CLAUDE.md | UNRESOLVED (not on the manual page; gh not installed) |
| `npx skills add`; skills.sh lists on first install | README, CLAUDE.md | UNRESOLVED (skills.sh blocked) |
| Runs in Claude Code, Codex, Cursor, Gemini CLI, Copilot | README | UNRESOLVED (agentskills.io blocked) |
| `metadata.version` bump | CLAUDE.md | GROUNDED (SKILL.md 2.1; check_skills requires quoted string) |
| Rule globs match the files claimed | rules | GROUNDED: ground-legal 12 files (legal.md, 10 sources, DATA-LICENSE); map-terms 16; verify-a-check 9 (all tests, hooks, scripts); verify-skill-changes 20. Verified with a glob simulation over `git ls-files` |
| Suites listed by name in skills-ci.yml | verify-a-check rule | CONTRADICTED for the two bash suites. Fixed; pre-push.test.sh runs in no workflow (finding) |
| Nominatim "will get you banned" | map-terms rule | GROUNDED (policy fetched) |
| Nominatim: 1 req/s, identifying UA, LLM clause, cache, no personal data | legal.md, nominatim.md | GROUNDED (fetched) |
| Overpass: 10,000 queries / 1 GB per day, divide by 100, no parallel, UA/Referer, commercial self-host | legal.md, overpass.md | GROUNDED (wiki fetched). Wiki also asks: pause 30 s on 429/406; server "overloaded, use alternatives if possible" |
| FOSSGIS four policy bullets; full policy German | legal.md, osrm-fossgis.md | GROUNDED (about.html fetched) |
| Substantial: <100 features, 1,000 inhabitants, "village map OK, town map not OK"; endorsed 2014-06-06 | legal.md | GROUNDED (fetched) |
| Produced Work: "intended for the extraction of the original data"; SVG/raster usually Produced Works | legal.md | GROUNDED (fetched) |
| Demo streets.js holds 1,108 ways | legal.md, DATA-LICENSE | GROUNDED (counted 1108) |
| sources.py: 5 changes/day cap, 90-day stale, exit 3 propose-only, evidence handle, forbidden words, drop shrink refused | adapt.md, README.md (sources) | GROUNDED, except the drop-growth row (B-1 below) |

## B. Proposed diffs (no edits made)

### B-1 MAJOR: adapt.md promises drop-list growth "any time"; the tool refuses it without evidence
adapt.md table: "Add a field to an entry's `drop` list | Autonomous | Any time". `sources.py` line 311: any change to `drop` without `--evidence` is REFUSED ("evidence-required"), and line 315 refuses an evidence string without a handle. An agent following adapt.md gets refused and is told not to invent a handle. Fix in the check, not the prose (Rule 1's second half):
```diff
--- a/skills/trip-scout/scripts/sources.py
@@ apply_change
-    if changed & {"status", "how", "caveats", "drop"} - {"id"} and not front_updates.get("evidence"):
+    needs_evidence = changed & {"status", "how", "caveats"}
+    if "drop" in body_updates and current and \
+            drop_tokens(current["body"].get("drop")) - drop_tokens(body_updates["drop"]):
+        needs_evidence.add("drop")   # shrinking needs evidence; growing never does (adapt.md table)
+    if needs_evidence and not front_updates.get("evidence"):
```
plus a test in `tests/test_sources.py` ("set --drop that only adds a field succeeds without --evidence"), and the rule verify-a-check-by-breaking-it applies. If the owner prefers the prose fix instead, change the table row's condition to "name the run that showed the field (`--evidence`)".

### B-2 MAJOR: Nominatim relay through Apify contradicts the Nominatim policy
`nominatim.md` caveats allow a relay "through another service only if that service sends your identifying User-Agent"; the only relay source is `apify-page-render.md`, whose `how` names "a single router or geocoder request". The policy's Reselling bullet (fetched 2026-09-25): "Applications and services whose primary function is related to geocoding must run their own service. This includes ... API resellers like Postman or Apify." Routing Nominatim traffic through an Apify actor is the pattern the policy names, and a ban would hit the shared User-Agent for every user.
```diff
--- a/skills/trip-scout/sources/nominatim.md
-caveats: Many sandboxes cannot reach it. Then ask the user for the coordinate, or take it from listing data. Relay the request through another service only if that service sends your identifying User-Agent; a stock browser or library User-Agent breaks the policy. Never geocode ...
+caveats: Many sandboxes cannot reach it. Then ask the user for the coordinate, or take it from listing data. Do not relay through Apify or any other API reseller: the policy names them under Reselling and requires them to run their own geocoder. Never geocode ...
--- a/skills/trip-scout/sources/apify-page-render.md
-... URL mode, as a fetch relay for a single router or geocoder request the sandbox cannot reach: ...
+... URL mode, as a fetch relay for a single router request the sandbox cannot reach (not for Nominatim: its policy names Apify as a reseller): ...
--- a/skills/trip-scout/reference/legal.md  (core: owner approval)
 - Nominatim (...): "an absolute maximum of 1 request per second"; ... — GROUNDED (...).
+  - Reselling: "Applications and services whose primary function is related to geocoding must run their own service. This includes ... API resellers like Postman or Apify." — GROUNDED (same page, read 2026-09-25).
```
Also worth recording in legal.md (same page): "The public Nominatim API must not be built into, offered through, suggested by, or automatically generated by no-code, low-code, or vibe-coding platforms as a generic geocoding ... service. Use ... is only permitted where the application developer has made a deliberate, informed decision." The skill's use is deliberate and documented, which is why the sentence belongs in the file: it is the line the notice to the user rests on.

### B-3 MINOR: a relay run is a paid run
`osrm-fossgis.md` and `apify-page-render.md` describe relaying a router request through a paid actor. Nothing says it counts against the budget from `brief.md` or that the invariant-2 notice precedes it. Add to `apify-page-render.md` caveats: "A relay run is a paid run: it counts against the budget and comes after the notice (SKILL.md flow 4)."

### B-4 MINOR: `python3 scripts/sources.py check` is cwd-relative
SKILL.md flow 2 and adapt.md give the path relative to the skill folder; the agent's cwd is the user's project. A small model runs it from the wrong directory and concludes Python "is not available". Proposed: "`python3 <this skill's folder>/scripts/sources.py check`" in flow 2, once.

### B-5 MINOR: adapt.md §The tool restates the script
The bullet "They refuse a missing or vague evidence handle, a shrinking `drop` list, a forbidden technique, or a sixth change in a day" is the script's refusal list in prose (reserve-prose rule; it already disagrees with the script on B-1). Keep the two things the agent cannot learn from `--help` output it has not run yet: a rejected entry is `untested` for the session; exit 3 means propose-only. Cut the refusal list to "Each refusal names the rule and the next step".

### B-6 MINOR: legal.md carries a demo fact
"The demo's `streets.js` holds 1,108 ways" is true today and lives in a core, owner-approved file; DATA-LICENSE already states it beside the data. Cut from legal.md so the demo can change without a core PR. Same file: the "(map-data and OSM service policies added the same day)" parenthetical is changelog noise in a "Last reviewed" line; git holds it.

### B-7 MINOR: overpass.md misses two lines from the policy it cites
The wiki cell also says: pause 30 s on HTTP 429/406 before retrying, and that the main instance is overloaded ("use alternatives if possible"). An agent that retries a 429 immediately is the "heavy use" the entry warns against. Add both to `caveats`, dated.

### B-8 MINOR: brief.md budget sentence
"suggest about USD 5 if the user has no number" with "5–8 paid runs" and wizzair's "refused a spend cap under $0.60" is consistent (6 runs x 0.60 = 3.60). Left; noted because a future actor minimum would silently break the sum.

### Verified consistent (no diff)
- Invariants block unchanged in the diff (checked line by line).
- Flow 4 notice, brief.md "whose trip", page.md shared-page rule, lodging.md polygon-from-data: each cites the invariant it applies; no contradiction found.
- flights.md currency rule and wizzair caveat agree.
- sources/README kinds and connectors equal `KINDS`/`CONNECTORS` in sources.py.
- 90-day staleness: README (sources), adapt.md and `STALE_DAYS` agree.

## Findings outside the brief
- `.githooks/pre-push.test.sh` is not run by any workflow (now stated in the rule).
- Four external claims (gh 2.90+, npx skills add, skills.sh listing, agent list) could not be verified from this sandbox; the owner should check them from a machine with network access before publishing.
