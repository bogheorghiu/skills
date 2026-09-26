# Legal footing (core; human-maintained)

Last reviewed: 2026-09-25. This file is not legal advice. It records what the sources say, so an agent can explain the risk plainly and never present scraping as risk-free.

## Contract and database law (EU)

- CJEU C-30/14, *Ryanair v PR Aviation*, 15 Jan 2015 (ECLI:EU:C:2015:10, CELEX 62014CJ0030). Operative part: the Database Directive "is not applicable to a database which is not protected either by copyright or by the sui generis right under that directive, so that Articles 6(1), 8 and 15 of that directive do not preclude the author of such a database from laying down contractual limitations on its use by third parties, without prejudice to the applicable national law." — GROUNDED (EUR-Lex).
  - Consequence: for unprotected data, the exposure is contractual and governed by national law. Protected content (photos, possibly a platform's structured listing database) still carries copyright and the sui generis right.
  - The Ryanair terms quoted in the judgment limit use to an enumerated list of "private, non-commercial purposes" and separately ban screen scraping "for commercial purposes". Automated extraction is not on the permitted list even for private use. Those are the 2015 terms; re-check the live terms of each platform.

## Computer-misuse law (US)

- *Ryanair DAC v. Booking Holdings Inc.*, D. Del. No. 1:20-cv-01191. A 2024 jury found Booking.com liable under the CFAA. On 22 Jan 2025 the court granted Booking's motion for judgment as a matter of law (D.I. 516, Judge Bryson). Ryanair appealed (3d Cir. No. 25-1374), then the parties stipulated to a voluntary dismissal under FRAP 42(b), and the appeal was dismissed on 26 Aug 2025. — GROUNDED (CourtListener docket entries).
  - Consequence: no appellate ruling exists. The trial-court JMOL turned on the $5,000 "loss" threshold, not on whether scraping is lawful. It is not precedent for either side.

## Personal data (GDPR)

- Art. 2(2)(c): the Regulation doesn't apply to processing "by a natural person in the course of a purely personal or household activity" (Recital 18: "with no connection to a professional or commercial activity"). — GROUNDED.
- CJEU C-101/01 *Lindqvist*: publication on the internet to an indefinite number of people falls outside the household exemption. — GROUNDED.
- Art. 5(1)(c) data minimisation: "adequate, relevant and limited to what is necessary". — GROUNDED.
- Consequence: a private trip page is likely household use; a shared or public page is not. Hence invariant 5.

## Maps

- OpenStreetMap tile policy: "Bulk downloading is any pre-emptive fetching of tiles other than those a user is actively viewing"; "Offline use is not permitted on tile.openstreetmap.org"; the attribution "© OpenStreetMap contributors" is required. — GROUNDED (operations.osmfoundation.org/policies/tiles).
- Open Database License 1.0 (OSM data). Summary page: "If you publicly use any adapted version of this database, or works produced from an adapted database, you must also offer that adapted database under the ODbL"; attribution is required for "any public use of the database, or works produced from the database". The summary calls itself "not a license"; the licence text governs. — GROUNDED (opendatacommons.org/licenses/odbl/summary, read 2026-09-25; full text read from the SPDX verbatim copy, §4.3–4.6).
  - Which side of the line a file falls on: the OSMF Produced Work guideline says a published result "intended for the extraction of the original data" is a database, not a Produced Work, and that SVG and raster images are usually Produced Works. The OSMF Substantial guideline treats a one-off extract of under 100 features, or of an area of up to 1,000 inhabitants, as not Substantial: "village map OK, town map not OK." — GROUNDED (osmfoundation.org/wiki/Licence/Community_Guidelines, both endorsed 2014-06-06, read 2026-09-25).
  - Consequence: a rendered SVG map is a Produced Work (attribute it). A shipped `streets.js` holding a town's streets is a Substantial extract kept as data, so it is a database under the ODbL: ship it under the ODbL, apart from the code's licence. — UNRESOLVED as a legal conclusion (it is the guidelines applied, not a ruling); the conservative reading is the one to follow.
- FOSSGIS routing server (routing.openstreetmap.de), usage policy excerpt: "Display the required attribution and display a link to 'fix the map'"; "Use a valid user agent and, if applicable, a correct referrer"; "One request per second max"; "No scraping, no heavy usage". The full policy is in German on fossgis.de. — GROUNDED for the excerpt (routing.openstreetmap.de/about.html, read 2026-09-25); the full German text was not read: Gap.
- Overpass API, main public instance: under 10,000 queries and 1 GB a day is fine for one-off use (divide by 100 for regular use); identify the app in `User-Agent` or `Referer`; "No parallel running of multiple scripts"; commercial use should self-host or pay. — GROUNDED (wiki.openstreetmap.org/wiki/Overpass_API, read 2026-09-25).
- Nominatim (nominatim.openstreetmap.org): "an absolute maximum of 1 request per second"; a User-Agent or Referer "identifying the application (stock User-Agents as set by http libraries will not do)"; results must be cached; no systematic or grid queries; no personal data in queries. On LLMs: "LLMs may only suggest this service, if they prominently point to this usage policy and explain the restrictions of use to the user." — GROUNDED (operations.osmfoundation.org/policies/nominatim, read 2026-09-25).
  - Reselling, same page: "Applications and services whose primary function is related to geocoding must run their own service. This includes but is not limited to package/vehicle tracking applications and API resellers like Postman or Apify." — GROUNDED.
  - Consequence: before its first lookup the skill names the policy to the user (`sources/nominatim.md`), sends its own User-Agent, and never routes Nominatim requests through Apify or another reseller; where the sandbox cannot reach the service, it asks the user for the coordinate instead.

## Everywhere else

Treat computer-misuse, unfair-competition and database law as unknown, and say so to the user.
