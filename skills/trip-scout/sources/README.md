# Source registry

One file per source. The agent picks sources by `kind` and `status`, reads `how`/`caveats`/`drop` before use, and updates entries per `patterns/adapt.md`.

## Entry format

```yaml
---
id: apify-ryanair            # = filename without .md
kind: flight-calendar        # flight-calendar | flight-aggregator | lodging | page-render | geocoder | router | reference
connector: apify             # which connector runs it (apify, zapier, brightdata, web)
target: memo23/ryanair-scraper
status: working              # working | degraded | broken | deprecated | untested
last_verified: 2026-09-24
evidence: "run on 2026-09-24 returned priced rows OTP⇄BLQ"
---
how: what input shape worked
caveats: what the output does NOT mean
drop: fields to remove before saving (personal data)
```

The body is free text; keep it short.
