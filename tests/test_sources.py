#!/usr/bin/env python3
"""Tests for skills/trip-scout/scripts/sources.py. Run from the repo root:
    python3 tests/test_sources.py
Kept outside skills/ so the tests do not ship inside the installed skill.
Every case runs against a fresh temporary overlay (TRIP_SCOUT_HOME), with the
other overlay variables unset so a developer's own environment cannot leak in.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "skills" / "trip-scout" / "scripts" / "sources.py"
TODAY = "2026-09-25"
URL = "https://console.apify.com/actors/runs/AbCdEfGh123456789"


def run(ov, *args):
    env = {k: v for k, v in os.environ.items() if k not in ("TRIP_SCOUT_HOME", "CLAUDE_PLUGIN_DATA", "XDG_DATA_HOME")}
    env["TRIP_SCOUT_HOME"] = str(ov)
    p = subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


results = []


def case(label, cond, out=""):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + label + ("" if cond else "\n    " + out.strip().replace("\n", "\n    ")))


with tempfile.TemporaryDirectory() as t:
    ov = Path(t) / "ov"
    rc, out = run(ov, "check", "--today", TODAY)
    case("bundled registry passes check", rc == 0 and "0 invalid" in out, out)

    rc, out = run(ov, "set", "apify-ryanair", "--status", "degraded", "--today", TODAY)
    case("status change without evidence is refused", rc == 1 and "evidence-required" in out, out)

    rc, out = run(ov, "set", "apify-ryanair", "--status", "degraded", "--evidence", "it seemed flaky", "--today", TODAY)
    case("evidence without a handle is refused", rc == 1 and "REFUSED evidence:" in out, out)

    rc, out = run(ov, "set", "apify-ryanair", "--status", "degraded", "--evidence", URL, "--dry-run", "--today", TODAY)
    case("dry-run prints a diff and writes nothing", rc == 0 and "+status: degraded" in out and not (ov / "sources").exists(), out)

    rc, out = run(ov, "set", "apify-ryanair", "--status", "degraded", "--evidence", URL, "--last-verified", "today", "--today", TODAY)
    written = (ov / "sources" / "apify-ryanair.md")
    text = written.read_text() if written.exists() else ""
    bundled = (ROOT / "skills/trip-scout/sources/apify-ryanair.md").read_text()
    case("set writes the overlay copy", rc == 0 and "status: degraded" in text, out)
    case("set keeps the lines it did not change", [l for l in bundled.splitlines() if l.startswith(("how:", "caveats:", "target:"))]
         == [l for l in text.splitlines() if l.startswith(("how:", "caveats:", "target:"))], text)
    log = (ov / "CHANGELOG.md").read_text() if (ov / "CHANGELOG.md").exists() else ""
    case("set appends one CHANGELOG line in adapt.md's format", log.count("\n") == 1 and log.startswith(f"{TODAY} | sources/apify-ryanair.md | set ") and URL in log, log)

    rc, out = run(ov, "set", "apify-airbnb", "--drop", "host.about", "--evidence", URL, "--today", TODAY)
    case("shrinking a drop list is refused", rc == 1 and "REFUSED drop:" in out, out)
    rc, out = run(ov, "set", "apify-airbnb", "--drop", "host.about", "--evidence", URL, "--allow-drop-removal", "host.profileImage", "--today", TODAY)
    case("an override must name every removed field", rc == 1 and "REFUSED drop:" in out, out)
    rc, out = run(ov, "set", "apify-airbnb", "--drop", "host.about, host.profileImage, coHosts, host.hostDetails",
                  "--evidence", URL, "--allow-drop-removal", "review authors", "--today", TODAY)
    case("a named override needs a reason", rc == 1 and "needs --reason" in out, out)
    rc, out = run(ov, "set", "apify-airbnb", "--drop", "host.about, host.profileImage, coHosts, host.hostDetails, reviewer.name",
                  "--evidence", URL, "--allow-drop-removal", "review authors", "--reason", "\"field renamed to reviewer.name in the output\"", "--today", TODAY)
    log = (ov / "CHANGELOG.md").read_text()
    case("a reasoned drop removal is written and logged loudly", rc == 0 and "DROP REMOVED" in log, out + log)

    rc, out = run(ov, "set", "apify-booking", "--how", "use residential proxies when blocked", "--evidence", URL, "--today", TODAY)
    case("a forbidden technique in how is refused", rc == 1 and "REFUSED invariant:" in out, out)

    rc, out = run(ov, "add", "apify-ryanair", "--kind", "flight-calendar", "--connector", "apify", "--target", "x/y",
                  "--status", "working", "--evidence", URL, "--today", TODAY)
    case("add refuses an existing id", rc == 1 and "REFUSED exists:" in out, out)
    rc, out = run(ov, "set", "no-such-source", "--status", "broken", "--evidence", URL, "--today", TODAY)
    case("set refuses an unknown id", rc == 1 and "REFUSED unknown:" in out, out)
    rc, out = run(ov, "set", "../SKILL", "--status", "broken", "--evidence", URL, "--today", TODAY)
    case("a path-shaped id is refused before any write", rc == 1 and "REFUSED id:" in out, out)
    rc, out = run(ov, "add", "new-thing", "--kind", "lodging", "--connector", "apify", "--target", "a/b",
                  "--status", "broken", "--evidence", URL, "--today", TODAY)
    case("a new entry cannot be born broken", rc == 1 and "REFUSED schema:" in out, out)
    rc, out = run(ov, "add", "new-lodging", "--kind", "lodging", "--connector", "apify", "--target", "a/b",
                  "--status", "working", "--evidence", URL, "--how", "one run per city", "--caveats", "untested beyond one city",
                  "--drop", "host.name", "--today", TODAY)
    case("add writes a valid new entry", rc == 0 and (ov / "sources" / "new-lodging.md").exists(), out)

    for i in range(3):  # 3 changes logged so far (1 set + 1 drop removal + 1 add); fill to 5
        run(ov, "set", "apify-wizzair", "--caveats", f"note {i}", "--evidence", URL, "--today", TODAY)
    rc, out = run(ov, "set", "apify-wizzair", "--caveats", "one too many", "--evidence", URL, "--today", TODAY)
    case("the sixth change of the day is refused", rc == 1 and "REFUSED cap:" in out, out)
    rc, out = run(ov, "set", "apify-wizzair", "--caveats", "next day", "--evidence", URL, "--today", "2026-09-26")
    case("the cap resets the next day", rc == 0, out)

    # Load-time guard: a hand edit that bypasses the tool is caught by check.
    p = ov / "sources" / "apify-booking.md"
    p.write_text((ROOT / "skills/trip-scout/sources/apify-booking.md").read_text().replace("traderInfo (all), ", ""))
    rc, out = run(ov, "check", "--today", "2026-09-26")
    case("check rejects a hand-edited overlay entry that shrank its drop list", rc == 1 and "apify-booking (overlay)" in out and "drop list is missing" in out, out)
    p.write_text((ROOT / "skills/trip-scout/sources/apify-booking.md").read_text().replace("last_verified: 2026-09-24", "last_verified: 2026-09-01"))
    rc, out = run(ov, "check", "--today", "2026-09-26")
    case("check warns when the bundled copy is newer than the overlay copy", "shadowed" in out, out)
    rc, out = run(ov, "list", "--today", "2027-03-01")
    case("list flags working entries older than 90 days as stale", "stale" in out, out)

    blocker = Path(t) / "a-file"
    blocker.write_text("x")
    rc, out = run(blocker / "ov", "set", "apify-ryanair", "--status", "broken", "--evidence", URL, "--today", TODAY)
    case("an unwritable overlay exits 3 and prints the diff for the user", rc == 3 and "+status: broken" in out, out)

print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
