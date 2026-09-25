# Source registry

One file per source. The agent picks sources by `kind` and `status`, reads `how`/`caveats`/`drop` before use, and updates entries per `patterns/adapt.md`.

## Entry format

```yaml
---
id: apify-ryanair            # = filename without .md
kind: flight-calendar        # flight-calendar | flight-aggregator | lodging | page-render | geocoder | router | vector-data | reference
connector: apify             # which connector runs it (apify, zapier, brightdata, web)
target: memo23/ryanair-scraper
status: working              # working | degraded | broken | deprecated | untested
last_verified: 2026-09-24     # date of the evidence below, not of the last edit
evidence: "run ByRsawBRFr3ntuQi3 (2026-09-24): priced rows OTP⇄BLQ"   # needs a handle: URL, run/dataset ID, or quoted output
---
how: what input shape worked
caveats: what the output does NOT mean
drop: fields to remove before saving (personal data)
```

The body is free text; keep it short.

`scripts/sources.py check` validates every entry against this format; `set` and `add` write overlay entries in it and log the change (see `patterns/adapt.md`). An entry that fails `check` counts as `untested` for the session.

The `last_verified` dates on bundled entries are the dates this release was verified. After 90 days they read as stale until a run re-verifies them; that is expected, not a fault.
