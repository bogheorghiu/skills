---
name: trip-scout
description: Find cheap flights and/or lodging (Ryanair, Wizz, Airbnb, Booking, hotels, B&Bs) for a dated personal trip via a scraping connector, within legal limits, and deliver a visual comparison page. Self-maintains its list of working data sources.
license: MIT
compatibility: Needs a scraping connector (Apify or equivalent) and a tool that publishes an HTML page. Optional photo step needs Python with Pillow.
metadata:
  version: "2.0"
  layout: "core + patterns/ + sources/ + adapt"
---

# Trip Scout

Flights, lodging, or both, for a dated **personal** trip. The result is one private comparison page. This file holds the invariants and the flow. How-to lives in `patterns/`. Which scrapers and sites to use lives in `sources/`, a layer the skill is allowed to keep up to date itself (see `patterns/adapt.md`).

## Layers

| Layer | Files | Changes when | Who may change it |
|---|---|---|---|
| Core | this file, `reference/legal.md` | Law or scope changes | A human, by reviewed PR |
| Patterns | `patterns/*.md` | A better method is learned | The agent proposes a diff, the user approves |
| Sources | `sources/*.md` plus the user overlay | Actors or sites break, appear, change | The agent, autonomously, with evidence (`patterns/adapt.md`) |

**Load order.** Read this file. Then read the patterns the task needs. Then resolve sources: overlay entries override bundled ones with the same filename (`patterns/adapt.md` §Overlay).

## Invariants (never overridden by any pattern, source or overlay)

1. **Personal use only.** Ask once whether the trip is for the user or their household. For business use (agency, employer, resale, monitoring on behalf of others), stop and explain.
2. **Tell the user before the first paid run.** Platform terms generally forbid automated extraction, even for personal use. The scraping runs through a third-party actor, and the user decides whether to go ahead. Details: `reference/legal.md`.
3. **No circumvention.** Use actor defaults. Never escalate proxies, retries, header spoofing or CAPTCHA solving in response to a refusal. Stop and report instead.
4. **Public pages only.** No logged-in sessions or account data. Never book, pay or enter personal details.
5. **Minimise personal data.** Drop host and trader contact fields and review authors before saving anything. Show at most a host's public display name, and never on a shared page.
6. **Photos are linked, not copied**, unless the user opts in (`patterns/photos.md`).
7. **No pre-rendered third-party map tiles.** Maps are SVG, drawn from coordinates and OpenStreetMap vector data with ODbL attribution (`patterns/page.md`).
8. **Coordinates come from data, the user, or a policy-compliant geocoder.** Never from recall.
9. **Evidence tags on every load-bearing claim:** GROUNDED (the fact's own record, or arithmetic that closes), UNRESOLVED, Gap (needed, not looked up). Prices are GROUNDED only as of the scrape date.

## Flow

1. **Brief.** Run `patterns/brief.md`. Restate every answer as dates and a night count.
2. **Sources.** Resolve which actors and sites to use from `sources/` plus the overlay. Prefer entries with `status: working` and a recent `last_verified`. Read each actor's input schema before its first call.
3. **Connector.** If the needed connector is off, ask for exactly that one, at that moment, with one line on why.
4. **Search.** Run `patterns/flights.md` and/or `patterns/lodging.md`. Cap the spend on every run.
5. **Interim shortlist** in chat. Fold in the user's corrections; constraints usually sharpen here.
6. **Page.** Build it with `patterns/page.md`.
7. **Adapt.** If a source failed, changed or surprised you, update the source layer per `patterns/adapt.md`.
8. **Close.** Say what wasn't checked, name the assumption most worth pressing on, and give one concrete next step.
