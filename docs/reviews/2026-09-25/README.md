# Reviews of trip-scout 2.1 (2026-09-25)

The raw records behind PR 1, kept so the verdicts can be re-checked. They are session artifacts, not maintained docs: line numbers refer to the files as they were at each review, and later commits fixed most findings.

| File | What it is |
|---|---|
| `review1-findings.md` | Blind review of the handed-off v2 (Fable, zero context). PASS, 7 MAJOR. |
| `review2-findings.md` | Blind review after fix round 1. 6 MAJOR; one BLOCKING by the letter of the bar, which is the skill's disclosed premise (scraping against platform terms); left to the owner. |
| `review3-findings.md` | Blind review after fix round 2, with that premise scoped out of the bar. PASS, 3 MAJOR (fixed), 11 MINOR (open). |
| `fable-deepen.md` | Second opinion on whether to ship `scripts/sources.py`, and its interface. |
| `fable-prose-review.md` | Editor pass over README, CLAUDE.md and the rules, with a claim-by-claim check. |
| `legal-sources.md` | Verbatim quotes from the ODbL, OSMF guidelines and the FOSSGIS, Overpass and Nominatim policies, with the relay run IDs used to fetch them. |
| `adhd-converge.md` | Convergence notes from the divergent-ideation run that produced the checker's design. |

`<scratch>/` stands for the reviewing session's temporary folder.
