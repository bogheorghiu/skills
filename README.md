# skills

Agent Skills ([agentskills.io](https://agentskills.io/specification) format) that run in Claude Code, Codex, Cursor, Gemini CLI, Copilot and other agents that read the format.

| Skill | What it does |
|---|---|
| [`trip-scout`](skills/trip-scout/SKILL.md) | Finds cheap flights and lodging for a dated **personal** trip through a scraping connector (Apify by default), within stated legal limits, and builds one comparison page: map with walking times routed along real streets, price chart, cards, flights table. |

## Install

```bash
npx skills add bogheorghiu/skills          # skills.sh CLI; pick trip-scout
gh skill install bogheorghiu/skills trip-scout   # GitHub CLI 2.90+
```

Or copy `skills/trip-scout/` into your agent's skills folder.

## trip-scout

**Demo:** [`examples/bologna-bcbf-2027/`](examples/bologna-bcbf-2027/index.html). Serve the folder and open `index.html` (it loads `data.js`, `streets.js` and `routes.js` beside it). Lodging for a book fair in Bologna, April 2027, with an EN/RO switch.

**What you need:** an agent with a scraping connector (the bundled sources use Apify actors, which are paid per run) and a way to publish or open an HTML page. Python 3.8+ is optional; it runs the source-registry checker.

**Limits, by design.** The skill stops if the trip is for a business. Before the first paid run it tells you that platform terms generally forbid automated extraction, even for personal use, and waits for your yes. It never works around a refusal, never logs in, never books or pays. It drops hosts' personal data, links photos instead of copying them, and draws maps from OpenStreetMap data instead of copying map tiles. [`reference/legal.md`](skills/trip-scout/reference/legal.md) records what the law and the services' policies say, with sources. It is not legal advice.

**It keeps its own list of scrapers current.** Scrapers break and sites change. When one does, the skill records the change, with evidence, in a folder you own outside the install (by default `~/.local/share/trip-scout`; it asks before creating it), so the record survives updates and the installed files stay untouched. It may change that source list on its own, within limits a script checks. Changes to its methods need your approval. Its rules and legal file change only by a reviewed pull request here. The details, including where the folder goes, are in [`patterns/adapt.md`](skills/trip-scout/patterns/adapt.md).

If it fixed a broken source for you, it offers a ready-made pull request text; sending it upstream helps the next user.

## Layout

```
skills/trip-scout/
  SKILL.md             rules and flow: what the agent reads first
  reference/legal.md   legal footing, primary-sourced
  patterns/            how-to modules: brief, flights, lodging, page, photos, adapt
  sources/             one file per scraper or service, kept current by the skill
  scripts/sources.py   checks and edits the source list (stdlib Python)
examples/              demo output
tests/                 tests for the scripts (not shipped with the skill)
```

## Licences

- `skills/trip-scout/` and the demo's code: MIT ([`skills/trip-scout/LICENSE`](skills/trip-scout/LICENSE)).
- `examples/bologna-bcbf-2027/streets.js` and `routes.js`: derived from OpenStreetMap, © OpenStreetMap contributors, under the [ODbL](https://opendatacommons.org/licenses/odbl/1-0/) ([`DATA-LICENSE`](examples/bologna-bcbf-2027/DATA-LICENSE)).
- Anything else in this repository: Apache-2.0 ([`LICENSE`](LICENSE)).

## Contributing

Pull requests are welcome, most of all fixes to `sources/` entries backed by a real run. Run the checks CI runs before you push:

```bash
python3 .github/scripts/check_skills.py
TRIP_SCOUT_HOME=/tmp/empty python3 skills/trip-scout/scripts/sources.py check   # CI checks the bundled entries only, not your overlay
python3 .github/scripts/test_check_skills.py
python3 tests/test_sources.py
```

This repository is public, so nothing personal goes into it: no names, no host data, nothing that identifies a traveller. A PII guard runs in CI; enable the same check locally with `git config core.hooksPath .githooks`.
