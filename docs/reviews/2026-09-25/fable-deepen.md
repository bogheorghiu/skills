# trip-scout: deepening the "write-through tool" shortlist (skeptical second opinion)

Read: `SKILL.md`, `patterns/adapt.md`, `sources/README.md`, all 8 `sources/*.md`, `reference/legal.md` header, repo `.githooks/` layout (pre-commit / pre-push already exist for the PII denylist guard). Nothing edited.

Two facts from the files that shape everything below:

- **The bundled entries already fail idea 2 as worded.** Six of eight `evidence` strings carry no run ID and no URL ("run on 2026-09-24 returned priced rows OTP⇄BLQ"; "3 runs ... returned 42/86/150 properties"; "listed in the store (579 users)"). Only `nominatim` and `osrm-fossgis` have a URL-shaped handle. So the author's own model, writing under the prose rules, did not produce "replayable" evidence. That is the strongest evidence in the folder that prose alone under-delivers, and also that a strict regex would reject the shipped baseline.
- **Frontmatter is flat scalars only** (7 keys), and the body is three `key:` lines of free text (`how`, `caveats`, `drop`). That makes a stdlib parser trivial (no YAML library), and it makes `drop` a comma-separated list that is cheap to compare across versions. Bundled `drop` values include tokens with spaces ("hostInfo.* except name", "review authors"), so comparison must be token-set on comma split, whitespace-trimmed, not word-level.

---

## A. The three ideas, sketched honestly

### 1. Write-through tool `scripts/sources.py`

**How it works here.** The script lives inside the skill folder, so it finds the bundled registry as `Path(__file__).parent.parent / "sources"` and resolves the overlay exactly as adapt.md §Overlay orders it (`$TRIP_SCOUT_HOME` → `$CLAUDE_PLUGIN_DATA/trip-scout` → `${XDG_DATA_HOME:-~/.local/share}/trip-scout`). `list` merges overlay over bundled by filename, prints one row per entry with `status`, `last_verified`, and a computed `stale` flag. `check` validates every entry in both layers (flat frontmatter parse, required keys, `id == filename`, `kind`/`status`/`connector` enums from README, ISO date, evidence non-empty and dated) and exits non-zero on any error. `set` rewrites only the changed frontmatter/body lines of the overlay copy (creating it from the bundled entry if absent), keeping every other byte, and appends the CHANGELOG line itself in adapt.md's `date | file | change | evidence | note` format. Refusals fire before any write: day-cap from CHANGELOG, drop-list shrink versus the *current effective* entry (overlay if present, else bundled), evidence shape, path/id shape, and a keyword scan of `how`/`target`/`caveats` for login/proxy/CAPTCHA terms. If the overlay isn't writable it prints the unified diff and exits 3, which *is* adapt.md's propose-only mode.

**Load-bearing risk.** Not bypass (see B). It is that the script becomes a second, drifting spec: README says the schema, adapt.md says the rules, the script encodes both, and the three will disagree within a few edits. Second risk: the "session cap" is really a "today cap" counted from CHANGELOG lines, which conflates two sessions in one day and misses any change made without the script. Third: `set` rewriting free text; a naive "parse then dump" loses anything not under the three known keys. Line-level substitution avoids that but is the fiddliest code in the file.

**First concrete step.** Write `check` only (~100 lines), run it against the 8 bundled entries, make them pass (which forces a decision on the evidence rule, see idea 2), and add one line to `.githooks/pre-commit` so the bundled layer is guarded in this public repo from day one. Only then write `set`.

### 2. Evidence must name a dated handle, checked by pattern

**How it works here.** A regex applied by `check` (warning on bundled, error on overlay) and by `set` (refusal). "Replayable" is the wrong word: an Apify run ID is replayable only by the account that owns it, for as long as the platform retains the run; a URL is replayable by anyone until the site changes. What the pattern can actually enforce is *specificity*: the string must contain a `YYYY-MM-DD` and at least one of a URL, a 17-char Apify-style ID (`[A-Za-z0-9]{17}`), or a quoted fragment of at least 20 characters (error text, returned row description). Under that rule the two web entries pass, and the six Apify entries fail only for lacking a date inside the string, which is a one-word fix per entry (or: accept `last_verified` as the date and require only the handle). Recommend the latter, so the bundled baseline passes unchanged except `apify-google-flights` ("listed in the store; not run") which is honest and should stay allowed for `status: untested`.

**Load-bearing risk.** It is theatre against fabrication: a model can type `run 3fK9xL2pQ8mN1vB7c` as easily as it can type "works". The check catches laziness, not lies. If anyone reads the pattern as a security control it will be oversold. Also, real evidence in this skill is often prose-shaped ("22-image grid timed out") and a too-tight regex will train agents to append junk tokens to satisfy it.

**First concrete step.** Decide the rule in `sources/README.md` first (one sentence under `evidence:`), then implement it as the same regex in `check`. Do not ship a regex that the shipped entries fail.

### 3. Staleness computed at read time, never written

**How it works here.** `list` and `check` compute `today - last_verified > 90` and print `stale` in a column; `status` enum stays as is (no `stale` value). SKILL.md step 2 already says "prefer entries with a recent `last_verified`"; the script makes "recent" a number and shows it. A `--today` flag exists for tests and for agents whose clock is untrustworthy.

**Load-bearing risk.** Almost none; this is clearly right. The one semantic gap it exposes: `last_verified` currently means "entry last touched", not "source last ran" (`apify-google-flights` is `untested` with `last_verified: 2026-09-24`). Staleness on an untested entry is meaningless, so `list` should show stale only for `working`/`degraded`. Fix the definition in README in the same commit.

**First concrete step.** Ten lines inside `list`; and one sentence in README defining `last_verified` as "date of the evidence, not of the edit".

---

## B. The counter-case: the agent just edits the markdown

Yes. Nothing in a skill folder can stop `Write`/`Edit` on `~/.local/share/trip-scout/sources/apify-ryanair.md`. In Claude Code the file tools are always available and the script is opt-in. Any argument that `set` *enforces* the bounds is false.

So what does idea 1 buy, honestly?

1. **The enforcement point is read time, not write time.** This is the part the brainstorm missed. If SKILL.md step 2 says "run `sources.py check`; any entry that fails is treated as `untested` this session", then a hand-edited entry with a shrunk drop list, missing evidence or bad date is *demoted on the next load regardless of who wrote it or how*. The write path can be bypassed; the read path cannot, because the agent needs the registry to do its job. That turns `check` from a linter into the actual guard. `set` then only matters as the path of least resistance.
2. **Over a `check`-only validator:** `set` buys atomicity (entry + CHANGELOG line in one call, in the right format; the changelog line is the thing a small model will most reliably botch or forget), a diff for propose-only mode, and refusal messages *at the moment of the mistake* rather than at the next session. Against that: ~120 more lines, the line-preserving rewrite, and the day-cap proxy. Modest gain, modest cost.
3. **Over prose:** adapt.md is 47 lines read once at load; by step 7 of an 8-step flow, a small model has the rules as a vague memory. The bundled entries prove that even the authoring model, under the prose, skipped run IDs. A deterministic "REFUSED ... because adapt.md says ..." string is worth more than the same sentence 40 turns earlier. Prose also cannot compute 90 days or count 5 changes.

**Verdict: ship a smaller version.** `check` + `list` + `set`/`add`, stdlib, one file, ~250 lines, plus a load-time demotion sentence in SKILL.md and a pre-commit hook for the bundled layer. Keep `where` because it is ten lines and adapt.md already requires showing the user the resolved path once. Drop from the brainstorm: the word "replayable", the word "session" (call it what it is: a per-day cap counted from the CHANGELOG, and say in the refusal that it is a proxy), and any implication that `set` is the "only way" to change an entry. It is the *documented* way; `check` is the gate.

"Ship nothing" was considered: the skill is one day old and there is no failure to point at. But `check` earns its keep in CI alone on a public repo, and the evidence-quality drift in the bundled entries is a failure to point at.

---

## C. Wrongly rejected, and missing

**Rejected correctly:** hash-chained logs, signed manifests, quorum across forks, network-trace inspection. All assume an adversary that a personal overlay folder does not have.

**Partly wrongly rejected: "git-backed overlay with auto-revert".** Auto-revert is over-engineering. But the repo already has `.githooks/pre-commit`; running `sources.py check` there on `skills/trip-scout/sources/` costs one line and guards the layer that actually ships to other users. The overlay stays git-free.

**Missing from the brainstorm:**

- **Load-time demotion** (B.1). Without it the tool is a convenience; with it the bounds hold against direct edits.
- **Overlay shadowing an upstream fix.** Once an overlay entry exists it hides the bundled one forever. If the skill is updated and the bundled `last_verified` is newer than the overlay's, the user silently keeps the stale local copy. `list` should print `shadowed-by-newer-bundled` and `check` warn. This is the most likely real-world failure and nobody proposed it.
- **Atomic writes.** Write to `tmp` then `os.replace`, so a crash mid-`set` never leaves a half-entry that `check` then rejects and demotes.
- **Drop-removal needs a loud override, not a hard wall.** adapt.md permits removal "with evidence". A refusal with no escape trains models to hand-edit. `--allow-drop-removal FIELD --reason TEXT` logs the removal explicitly in the CHANGELOG line; that converts a silent shrink into a loud one, which is all a script can honestly do.
- **False positives on the invariant keyword scan.** "no login needed" contains "login". Refuse anyway (the invariant says "never"), but the message must say "if this is a false positive, tell the user; do not reword and retry". Reword-and-retry is exactly what a small model will otherwise do.
- **Body-text preservation.** `set` must substitute lines, not re-serialise, or free text under unknown keys is lost.
- **Windows/`~`.** `os.path.expanduser`; no shell expansion assumed.

---

## D. Minimal interface to ship

Single file `scripts/sources.py`, Python 3.8+, stdlib only (`argparse re json datetime pathlib os tempfile difflib`). All output is plain text; `--json` on `list`/`check` for agents that prefer it. Every command prints `overlay: <path>` as its first line.

### SKILL.md pointer (replace nothing, add three lines under Flow step 7)

```
Source-layer edits go through `python3 scripts/sources.py` (`check`, `list`, `set`, `add`).
Run `check` before step 2; an entry it rejects counts as `untested` this session.
No Python: follow patterns/adapt.md by hand and write the CHANGELOG line yourself.
```

### Subcommands

| Command | Does | Exit |
|---|---|---|
| `where` | Prints the resolved overlay path and which rule picked it (`TRIP_SCOUT_HOME` / `CLAUDE_PLUGIN_DATA` / `XDG`), and whether it is writable. | 0, or 3 if not writable |
| `list [--json] [--stale-days N] [--today YYYY-MM-DD]` | Merged table: `id kind status last_verified age_days layer flags`. Flags: `stale` (only for working/degraded), `shadowed` (overlay older than bundled). | 0 |
| `check [--json] [--today D]` | Validates bundled and overlay. Errors: bad frontmatter, missing key, `id != filename`, enum violation, bad date, empty evidence, evidence lacks handle (overlay only), drop shrink vs bundled (overlay only), invariant keyword (overlay only). Warnings: stale, shadowed, non-flat frontmatter, unknown body key, evidence lacks handle (bundled). | 0 clean, 1 any error |
| `set ID [--status S] [--last-verified D\|today] [--evidence T] [--how T] [--caveats T] [--drop "a, b"] [--allow-drop-removal F --reason T] [--note T] [--dry-run]` | Copies bundled → overlay if absent, substitutes only the given lines, appends CHANGELOG line, atomic. `--dry-run` prints the diff and the CHANGELOG line, writes nothing. Any change to `status`, `how`, `caveats`, `drop` requires `--evidence`. | 0 written, 1 refused, 2 usage, 3 propose-only (diff printed) |
| `add ID --kind K --connector C --target T --status S --evidence T [--how T] [--caveats T] [--drop T] [--note T] [--dry-run]` | New overlay entry. Same refusals plus `exists`. `status` must be `working` or `untested` (a new entry cannot be born `broken`). | as `set` |

No `remove`: adapt.md offers `deprecated` for that, and deletion is what `drop`-shrink guards against.

### Exit codes

- `0` success / clean
- `1` refused or validation failed (message starts `REFUSED <code>:` or `ERROR <file>:`)
- `2` usage error (argparse)
- `3` overlay not writable; the diff on stdout is for the user (propose-only)

### Refusal messages (one line each, verbatim shape)

- `REFUSED cap: 5 changes already logged today in <CHANGELOG>. adapt.md allows at most 5 autonomous changes per session (counted per day here). Stop; show the user this change with --dry-run instead.`
- `REFUSED evidence: --evidence needs a handle: a URL, a run/dataset ID, or a quoted fragment of 20+ characters. Got: "<text>". Copy it from the run or the error, do not invent one.`
- `REFUSED evidence-required: changing <fields> needs --evidence from this session (adapt.md §What may change).`
- `REFUSED drop: "<field>" is in the current drop list and not in the new one. Keep it, or pass --allow-drop-removal "<field>" --reason "<why it no longer applies>"; the removal is logged.`
- `REFUSED invariant: "<word>" found in <field>. adapt.md forbids sources needing login, CAPTCHA solving, or proxies beyond actor defaults. If this is a false positive, tell the user; do not reword and retry.`
- `REFUSED schema: <field> must be one of <values>` / `REFUSED schema: last_verified must be YYYY-MM-DD`
- `REFUSED id: "<id>" must match ^[a-z0-9][a-z0-9-]*$ and is written only to <overlay>/sources/<id>.md`
- `REFUSED unknown: no entry "<id>" in bundled or overlay. Use add.`
- `REFUSED exists: "<id>" already exists. Use set.`
- `REFUSED core: SKILL.md, reference/legal.md and patterns/ are not editable here. Propose an upstream PR text instead.` (fires on any path argument that isn't a plain id)

### Rules the script encodes (and adapt.md stays the source of truth for)

- Enums copied from README: `kind`, `status`, `connector`.
- Evidence handle regex: `https?://\S+` or `\b[A-Za-z0-9]{17}\b` or `"[^"]{20,}"`.
- Invariant keywords (case-insensitive, `how`/`target`/`caveats`): `login`, `password`, `cookie`, `session token`, `captcha`, `residential`, `rotating prox`, `proxyConfiguration`.
- Day cap: count CHANGELOG lines starting with today's date; refuse the 6th.
- Drop list: comma-split, trimmed, `—`/empty = none; refuse if `current − new ≠ ∅` unless every removed field is named in `--allow-drop-removal`.
- Staleness: `age_days > 90` and status in {working, degraded}.

### Tests

One `scripts/sources.test.sh` in the style of the existing `.githooks/*.test.sh`: bundled layer passes `check`; each refusal code fires once from a temp overlay (`TRIP_SCOUT_HOME=$tmp`); `--dry-run` writes nothing; `set` preserves an unknown body line byte-for-byte; unwritable overlay exits 3 with a diff.

### Size

About 250 lines of Python, 80 of shell test, 3 lines in SKILL.md, 2 sentences in README (`last_verified` = date of the evidence; `evidence` must carry a handle), 1 line in `.githooks/pre-commit`. adapt.md unchanged.
