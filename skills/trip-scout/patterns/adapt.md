---
pattern: adapt
uses: {}
---
# Adapt: keeping the source layer alive

Actors break, sites change, better scrapers appear. This skill updates its own **source layer**, and only that layer, and it does so within fixed bounds.

## Overlay (where changes are written)

Installed skill folders are often read-only or overwritten on update, so changes go to a user-owned overlay, never into the bundled files. Resolve the overlay once per session, in this order:

1. `$TRIP_SCOUT_HOME`, if it is set.
2. Running as a Claude Code plugin: `${CLAUDE_PLUGIN_DATA}/trip-scout/` (a persistent per-plugin directory that survives updates).
3. `${XDG_DATA_HOME:-~/.local/share}/trip-scout/`.

The first time, show the user the resolved path and ask once whether to use it or another folder. If they pick another, tell them to set `TRIP_SCOUT_HOME`, since the skill has nowhere else to remember the choice. If nothing is writable, fall back to **propose-only**: print the change as a diff for the user to apply or send upstream.

Overlay layout mirrors the skill: `sources/*.md`, `patterns/*.md` (approved pattern edits only), and `CHANGELOG.md`. Resolution: an overlay file overrides the bundled file with the same name. Entries that exist only in the overlay are added.

## What may change, and how

| Change | Allowed | Condition |
|---|---|---|
| Update a source entry's `status`, `last_verified`, `caveats`, `how` | Autonomous | Evidence from this session: run ID, error text or URL |
| Add a new source entry | Autonomous | It passed one real run in this session, and it respects the invariants |
| Mark an entry `broken` / `deprecated` | Autonomous | Two failures, or one unambiguous failure (actor removed, schema gone) |
| Edit a pattern | Propose a diff, apply only after the user approves | Explain what failed and what the edit fixes |
| Edit `SKILL.md` invariants or `reference/legal.md` | Never | Suggest an upstream PR text instead |

Hard limits:

- Never add a source that needs a login, circumvention, or residential/rotating proxies beyond the actor's defaults.
- Never remove a `drop` list entry or a caveat without evidence that it no longer applies.
- At most 5 autonomous changes per session.
- Stale entries: `last_verified` older than 90 days means UNRESOLVED; re-verify before relying on the entry.

## Log

Append to the overlay's `CHANGELOG.md`, one line per change:

`YYYY-MM-DD | file | change | evidence | session note`

At the end of a session with changes:

- tell the user what changed;
- offer a ready-to-paste upstream PR description, so the fix can reach other users.
