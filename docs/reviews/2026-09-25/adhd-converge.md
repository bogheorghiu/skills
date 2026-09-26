# ADHD converge (orchestrator scoring, 2026-09-25)
Clusters:
A gate-script plays (verify exit 0, schema, core checksum, ID-diff drop list) — N5 V9 F9
B replayable-evidence plays (run id / hash / command / nonce) — N6 V7 F8
C ledger-not-state plays (append-only, status computed, decay) — N8 V5 F7
D asymmetric-burden plays (downgrade cheap, upgrade strict, two days) — N7 V8 F8
E circuit-breaker plays (volatility lockdown, Treg veto) — N7 V6 F6
F consensus/infra plays (quorum across forks, git overlay auto-revert, hash chains, signed manifest, network trace) — TRAPS: infra far beyond a personal-use markdown skill; a small agent can't run them; signatures without a key authority are theatre.
Key insight: a checker the agent may skip is prose with extra steps. ★ WRITE-THROUGH TOOL: the script is the writer (agent calls it to change an entry), so limits bind at the only write path the skill documents; checking is a side effect.
Shortlist: (1)★ write-through sources.py [A+D+B-lite]  (2) evidence must name a replayable handle (run id or URL+date) [B]  (3) derived staleness at read time, never written [C-lite]
