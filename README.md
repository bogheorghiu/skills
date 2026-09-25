# trip-scout

An [Agent Skill](https://agentskills.io/specification) that finds cheap flights and/or lodging for a dated personal trip. It pulls prices through a scraping connector (Apify by default) and delivers one visual comparison page.

```bash
npx skills add <owner>/<repo>
# or
gh skill install <owner>/<repo> trip-scout
```

## Layout

```
skills/trip-scout/
  SKILL.md            core: invariants + flow (human-maintained)
  reference/legal.md  legal footing with primary sources (human-maintained)
  patterns/*.md       how-to modules: brief, flights, lodging, page, photos, adapt
  sources/*.md        registry of scrapers/sites, kept current by the skill
examples/bologna-bcbf-2027/   demo output (open index.html)
```

**The source layer maintains itself.** Actors break and sites change. When that happens, the skill records it, with evidence, in a user-owned overlay folder. The folder is resolved in this order:

1. `$TRIP_SCOUT_HOME`
2. `${CLAUDE_PLUGIN_DATA}`, when installed as a Claude Code plugin
3. `${XDG_DATA_HOME:-~/.local/share}/trip-scout/`

The skill may update source entries on its own. Changes to patterns need the user's approval. The core and the legal file are never edited by the skill. See `patterns/adapt.md`.

## Limits, by design

- Personal use only. The skill stops if the trip is for a business.
- Before the first paid run, the user is told that platform terms generally forbid automated extraction.
- No circumvention of refusals, no logged-in data, no booking or payment.
- Personal data is minimised. Photos are linked, not copied; copying is opt-in.
- No pre-rendered OpenStreetMap tiles. Maps are drawn from OpenStreetMap vector data (ODbL, attributed).

Not legal advice. See `skills/trip-scout/reference/legal.md` for what the sources say.

## License

MIT
