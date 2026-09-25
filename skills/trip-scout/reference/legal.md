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

## Everywhere else

Treat computer-misuse, unfair-competition and database law as unknown, and say so to the user.
