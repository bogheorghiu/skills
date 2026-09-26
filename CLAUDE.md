# CLAUDE.md — skills

Guidance for any agent (or person) changing this repository. It is public, and what ships from it runs in strangers' agents with their money and their connectors. Most of what follows exists because of that.

## Rule 1: state the why

Every decision, rule and instruction you write here carries its reason. A reason lets the next reader apply a rule to a case its author never saw, and lets them see when it stops applying; a bare command gives them only obedience or defiance. Where a rule must hold exactly and a script can enforce it, put it in the script, not in prose: nothing skims or reinterprets a check.

## What is here

The directory tree is the inventory; this file does not repeat it, because a hand-kept list goes stale while still reading as authoritative. Each skill is `skills/<name>/SKILL.md` plus the files it references. `tests/` and `.github/` are for development and never ship with a skill.

## Who may change what in `trip-scout`

`skills/trip-scout/SKILL.md` defines three layers and who may change each. That table is the source of truth. What it means for a development session in this repository:

- **Core** (`SKILL.md`, `reference/legal.md`): changed only in a pull request the owner reviews, and only after the owner has said yes to that change in the conversation. Say in the PR body which core lines changed and where the owner approved them. The invariants at the top of `SKILL.md` protect users from legal and financial harm, and a plausible-sounding improvement is exactly how that kind of protection erodes.
- **Patterns**: propose the change with the failure it fixes; apply it when the owner agrees.
- **Sources**: change them when you have evidence from a real run (a run ID, a URL, one quoted error line). `skills/trip-scout/scripts/sources.py` checks the format.

## Evidence

Tag load-bearing claims GROUNDED (the fact's own record: the court docket, the licence text, the service's own policy page), UNRESOLVED (the evidence does not settle it) or CONTRADICTED; mark a needed but missing fact as a Gap. Date every claim about a live service, because policies and actors change without notice. When the sandbox blocks a host, say so, and say what you used instead. Legal and policy claims have their own rule, `.claude/rules/ground-legal-and-policy-claims.md`, which loads when you read the files they live in.

## Checks

CI (`.github/workflows/`) runs the spec checks, the bundled-source check and the test suites on every pull request and every push to main (`skills-ci.yml`), plus the PII and secrets guard (`pii-denylist-guard.yml`; its header says what each job scans). Run the same commands locally before pushing (the README lists them). A green CI run shows the scripts and the structure are sound; it says nothing about whether the prose still steers an agent correctly. For that, see `.claude/rules/verify-skill-changes.md`, and name the level of verification you actually ran.

## Privacy

What may not be committed is in `.claude/rules/keep-personal-data-out.md` (it loads every session). The mechanics: CI's denylist jobs read the `PII_DENYLIST` Actions secret; the local hooks read the same name as an environment variable and a gitignored `pii-denylist.local`, per clone after `git config core.hooksPath .githooks`. Each denylist layer is inactive, and says so, until it has terms; the gitleaks secret scan in CI runs regardless.

## Publishing

`main` is what users install. Merging to `main` is the release; there is no second step that could catch a mistake.

1. Merge only a green, reviewed PR.
2. `gh skill publish --dry-run` validates; `gh skill publish --tag vX.Y.Z` adds the `agent-skills` topic and creates the release (GitHub CLI 2.90+).
3. Check both install paths from a clean folder: `npx skills add bogheorghiu/skills` and `gh skill install bogheorghiu/skills trip-scout`. skills.sh lists a skill once it has been installed through its CLI; there is no separate submission.
4. Bump `metadata.version` in `SKILL.md` whenever a shipped file changes, so installed copies can tell they are behind.
