#!/usr/bin/env python3
"""Tests for skills/trip-scout/scripts/sources.py. Run from the repo root:
    python3 tests/test_sources.py
Kept outside skills/ so the tests do not ship inside the installed skill.

Every case runs against a fresh temporary overlay (TRIP_SCOUT_HOME), with the other
overlay variables unset so a developer's environment cannot leak in. Dates are relative
to the real today and fixtures are derived from the bundled files at run time, so
re-verifying a bundled entry (a normal contribution) does not break the suite.
"""
import datetime as dt
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "skills" / "trip-scout" / "scripts" / "sources.py"
BUNDLED = ROOT / "skills" / "trip-scout" / "sources"
TODAY = dt.date.today()
URL = "https://console.apify.com/actors/runs/AbCdEfGh123456789"


def run(ov, *args, day=None):
    env = {k: v for k, v in os.environ.items()
           if k not in ("TRIP_SCOUT_HOME", "CLAUDE_PLUGIN_DATA", "XDG_DATA_HOME", "TRIP_SCOUT_TEST_TODAY")}
    env["TRIP_SCOUT_HOME"] = str(ov)
    env["TRIP_SCOUT_TEST_TODAY"] = (day or TODAY).isoformat()  # no race at midnight
    p = subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


def body_line(path, key):
    m = re.search(rf"^{key}: (.*)$", Path(path).read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else ""


results = []


def case(label, cond, out=""):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + label + ("" if cond else "\n    " + str(out).strip().replace("\n", "\n    ")))


def logged(ov):
    p = ov / "CHANGELOG.md"
    return p.read_text().splitlines() if p.exists() else []


with tempfile.TemporaryDirectory() as t:
    ov = Path(t) / "ov"
    rc, out = run(ov, "check")
    case("bundled registry passes check", rc == 0 and " 0 invalid" in out, out)

    # --- evidence rules ---
    rc, out = run(ov, "set", "apify-ryanair", "--status", "degraded")
    case("status change without evidence is refused", rc == 1 and "evidence-required" in out, out)
    rc, out = run(ov, "set", "apify-ryanair", "--last-verified", "today")
    case("refreshing last_verified without evidence is refused", rc == 1 and "evidence-required" in out, out)
    rc, out = run(ov, "set", "apify-ryanair", "--status", "degraded", "--evidence", "it seemed flaky")
    case("evidence without a handle is refused", rc == 1 and "REFUSED evidence:" in out, out)
    rc, out = run(ov, "set", "apify-ryanair", "--status", "degraded", "--evidence", URL + "\nstatus: working")
    case("a newline in a value is refused (no injected second key)", rc == 1 and "one line" in out, out)
    rc, out = run(ov, "set", "apify-ryanair", "--add-caveat", "x\u2028drop_removed: foo", "--evidence", URL)
    case("a Unicode line separator is refused too", rc == 1 and "one line" in out, out)
    for vague in ("it's been failing lately and it doesn't return prices", "Counterproductive"):
        rc, out = run(ov, "set", "apify-ryanair", "--status", "broken", "--evidence", vague)
        case(f"vague evidence is refused even for broken: {vague[:24]!r}", rc == 1 and "REFUSED evidence:" in out, out)
    rc, out = run(ov, "set", "apify-ryanair", "--status", "broken", "--evidence", '"Actor memo23/ryanair-scraper was not found"')
    case("a double-quoted error line counts as evidence", rc == 0, out)
    ev_line = next((l for l in (ov / "sources" / "apify-ryanair.md").read_text().splitlines() if l.startswith("evidence:")), "") \
        if (ov / "sources" / "apify-ryanair.md").exists() else ""
    case("that evidence is written as valid YAML (single-quoted), not wrapped in a second pair of double quotes",
         ev_line.startswith("evidence: '\"Actor"), ev_line)
    (ov / "sources" / "apify-ryanair.md").unlink(missing_ok=True); (ov / "CHANGELOG.md").unlink(missing_ok=True)

    # --- a normal write ---
    rc, out = run(ov, "set", "apify-ryanair", "--status", "degraded", "--evidence", URL, "--dry-run")
    case("dry-run prints a diff and writes nothing", rc == 0 and "+status: degraded" in out and not (ov / "sources" / "apify-ryanair.md").exists(), out)
    rc, out = run(ov, "set", "apify-ryanair", "--status", "degraded", "--evidence", URL, "--last-verified", "today")
    written = ov / "sources" / "apify-ryanair.md"
    case("set writes the overlay copy", rc == 0 and body_line(written, "status") == "degraded", out)
    case("set keeps the lines it did not change",
         all(body_line(written, k) == body_line(BUNDLED / "apify-ryanair.md", k) for k in ("how", "caveats", "target", "drop")))
    log = logged(ov)
    case("set appends one CHANGELOG line in adapt.md's format",
         len(log) == 1 and log[0].startswith(f"{TODAY} | sources/apify-ryanair.md | set ") and URL in log[0], log)

    # --- caveats: appending is the default; replacing must say why ---
    rc, out = run(ov, "set", "apify-ryanair", "--caveats", "fares are fine", "--evidence", URL)
    case("replacing caveats without --reason is refused", rc == 1 and "REFUSED caveats:" in out, out)
    rc, out = run(ov, "set", "apify-ryanair", "--add-caveat", "Seen twice: prices in RON on OTP routes.", "--evidence", URL)
    kept = body_line(BUNDLED / "apify-ryanair.md", "caveats")
    case("--add-caveat keeps the old caveats and appends", rc == 0 and body_line(written, "caveats").startswith(kept) and "RON" in body_line(written, "caveats"), out)

    # --- drop lists ---
    airbnb_drop = body_line(BUNDLED / "apify-airbnb.md", "drop")
    first, rest = airbnb_drop.split(",")[0].strip(), ", ".join(x.strip() for x in airbnb_drop.split(",")[1:])
    rc, out = run(ov, "set", "apify-airbnb", "--drop", airbnb_drop + ", guest.phone")
    case("adding a drop field needs no evidence (adapt.md: any time)", rc == 0, out)
    grown = airbnb_drop + ", guest.phone"
    rc, out = run(ov, "set", "apify-airbnb", "--drop", rest + ", guest.phone", "--evidence", URL)
    case("shrinking a drop list is refused", rc == 1 and "REFUSED drop:" in out, out)
    rc, out = run(ov, "set", "apify-airbnb", "--drop", rest + ", guest.phone", "--evidence", URL, "--reason", "not needed")
    case("a reason alone does not remove a drop field (the field must be named)", rc == 1 and "REFUSED drop:" in out, out)
    rc, out = run(ov, "set", "apify-airbnb", "--drop", rest + ", guest.phone", "--evidence", URL,
                  "--allow-drop-removal", "something-else", "--reason", "x")
    case("an override must name the field actually removed", rc == 1 and "REFUSED drop:" in out, out)
    rc, out = run(ov, "set", "apify-airbnb", "--drop", rest + ", guest.phone", "--evidence", URL, "--allow-drop-removal", first)
    case("a named override needs a reason", rc == 1 and "needs --reason" in out, out)
    rc, out = run(ov, "set", "apify-airbnb", "--drop", rest + ", guest.phone", "--allow-drop-removal", first, "--reason", "renamed upstream")
    case("a drop removal needs evidence", rc == 1 and "evidence-required" in out, out)
    rc, out = run(ov, "set", "apify-airbnb", "--drop", rest + ", guest.phone", "--evidence", URL,
                  "--allow-drop-removal", first, "--reason", "field renamed upstream")
    case("a reasoned drop removal is written and logged loudly", rc == 0 and "DROP REMOVED" in logged(ov)[-1], out)
    case("the removal is recorded in the entry", first in body_line(ov / "sources" / "apify-airbnb.md", "drop_removed"))
    rc, out = run(ov, "check")
    case("check accepts an entry whose removal was recorded", "apify-airbnb (overlay)" not in out, out)
    booking_drop = body_line(BUNDLED / "apify-booking.md", "drop")
    paren = next(t.strip() for t in booking_drop.split(",") if "(" in t)
    rc, out = run(ov, "set", "apify-booking", "--drop", ", ".join(t.strip() for t in booking_drop.split(",") if t.strip() != paren),
                  "--evidence", URL, "--allow-drop-removal", paren, "--reason", "field gone upstream; see run")
    case(f"a drop field with parentheses ({paren!r}) can be removed and recorded", rc == 0, out)
    rc, out = run(ov, "check")
    case("check accepts that recorded removal", "apify-booking (overlay)" not in out, out)
    (ov / "sources" / "apify-booking.md").unlink(missing_ok=True)

    # --- forbidden techniques ---
    for bad in ("use residential proxies when blocked", "use residential-proxies if blocked", "paste the cookies from your browser",
                "pass a session token from the app", "requires a log-in first", "sign in with the account",
                'set proxy apifyProxyGroups ["RESIDENTIAL"]', "requires signing in to the account first", "works after logging in"):
        rc, out = run(ov, "set", "apify-booking", "--how", bad, "--evidence", URL)
        case(f"a forbidden technique in how is refused: {bad[:30]!r}", rc == 1 and "REFUSED invariant:" in out, out)

    for bad in ("use stealth mode and spoof the user agent", "set useApifyProxy true", "solve with 2captcha"):
        rc, out = run(Path(t) / "ov-bad", "set", "apify-booking", "--how", bad, "--evidence", URL)
        case(f"forbidden: {bad[:28]!r}", rc == 1 and "REFUSED invariant:" in out, out)
    rc, out = run(Path(t) / "ov-geo", "set", "nominatim", "--how", "relay the search through apify-page-render", "--evidence", URL)
    case("a geocoder entry may not route through a relay", rc == 1 and "REFUSED invariant:" in out, out)
    rc, out = run(ROOT / "skills" / "trip-scout", "set", "apify-ryanair", "--status", "broken", "--evidence", URL)
    case("an overlay inside the skill folder is refused", rc == 1 and "REFUSED overlay:" in out and "degraded" not in (BUNDLED / "apify-ryanair.md").read_text() and "status: broken" not in (BUNDLED / "apify-ryanair.md").read_text(), out)
    rc, out = run(Path(t) / "ov-cookie", "set", "apify-page-render", "--how", "public page, dismiss the cookie consent banner, then screenshot", "--evidence", URL)
    case("'cookie consent banner' is not a forbidden technique", rc == 0, out)
    # --- ids and adds (fresh overlay: the cap below counts from zero) ---
    ov = Path(t) / "ov-b"
    rc, out = run(ov, "add", "apify-ryanair", "--kind", "flight-calendar", "--connector", "apify", "--target", "x/y",
                  "--status", "working", "--evidence", URL)
    case("add refuses an existing id", rc == 1 and "REFUSED exists:" in out, out)
    rc, out = run(ov, "set", "no-such-source", "--status", "broken", "--evidence", URL)
    case("set refuses an unknown id", rc == 1 and "REFUSED unknown:" in out, out)
    rc, out = run(ov, "set", "../SKILL", "--status", "broken", "--evidence", URL)
    case("a path-shaped id is refused before any write", rc == 1 and "REFUSED id:" in out, out)
    rc, out = run(ov, "add", "new-thing", "--kind", "lodging", "--connector", "apify", "--target", "a/b",
                  "--status", "broken", "--evidence", URL)
    case("a new entry cannot be born broken", rc == 1 and "REFUSED schema:" in out, out)
    rc, out = run(ov, "add", "new-lodging", "--kind", "lodging", "--connector", "apify", "--target", "a/b",
                  "--status", "working", "--evidence", URL, "--how", "one run near the residential area of the city",
                  "--caveats", "tried in one city only", "--drop", "host.name")
    case("add writes a valid new entry (and 'residential area' is not a forbidden word)",
         rc == 0 and (ov / "sources" / "new-lodging.md").exists(), out)

    # --- daily cap: count exactly what is logged, then fill to the cap with checked calls ---
    n = len([ln for ln in logged(ov) if ln.startswith(TODAY.isoformat())])
    fills = [run(ov, "set", "apify-wizzair", "--add-caveat", f"note {i}.", "--evidence", URL)[0] for i in range(5 - n)]
    case(f"changes 1-5 of the day are accepted ({n} logged before the fill)", n < 5 and fills == [0] * (5 - n), fills)
    rc, out = run(ov, "set", "apify-wizzair", "--add-caveat", "one too many.", "--evidence", URL)
    case("the sixth change of the day is refused", rc == 1 and "REFUSED cap:" in out, out)
    rc, out = run(ov, "set", "apify-wizzair", "--add-caveat", "one too many.", "--evidence", URL, "--dry-run")
    case("--dry-run still works at the cap (the refusal tells the agent to use it)", rc == 0 and "one too many." in out, out)
    rc, out = run(ov, "set", "apify-airbnb", "--evidence", URL)
    case("a pure re-verification is allowed at the cap and logged as verify",
         rc == 0 and logged(ov)[-1].split(" | ")[2].startswith("verify "), out)
    case("new evidence moves last_verified to today", body_line(ov / "sources" / "apify-airbnb.md", "last_verified") == TODAY.isoformat())
    rc, out = run(ov, "set", "apify-wizzair", "--add-caveat", "next day.", "--evidence", URL, day=TODAY + dt.timedelta(days=1))
    case("the cap resets the next day", rc == 0, out)

    # --- load-time guard: hand edits that bypass the tool (fresh overlay again) ---
    ov = Path(t) / "ov-c"
    (ov / "sources").mkdir(parents=True)
    p = ov / "sources" / "apify-booking.md"
    booking = (BUNDLED / "apify-booking.md").read_text()
    kept = body_line(BUNDLED / "apify-booking.md", "drop").split(",")[1:]
    p.write_text(re.sub(r"^drop: .*$", "drop: " + ",".join(kept).strip(), booking, flags=re.M))
    rc, out = run(ov, "check")
    case("check rejects a hand-edited overlay entry that shrank its drop list",
         rc == 1 and "apify-booking (overlay)" in out and "drop list lacks" in out, out)
    rc, out = run(ov, "check")
    case("the error for a missing bundled drop field suggests adding it", "add it here" in out, out)
    fix_drop = body_line(BUNDLED / "apify-booking.md", "drop")
    rc, out = run(ov, "set", "apify-booking", "--drop", fix_drop)
    case("following that hint (add the field back) needs no evidence and fixes the entry",
         rc == 0 and "apify-booking (overlay)" not in run(ov, "check")[1], out)
    p.write_text(booking + "Also: pass session cookies from your browser.\n")
    p.write_text(booking.replace("how: ", "how: NEW WORDING. ", 1))
    rc, out = run(ov, "check")
    case("check warns when an overlay copy's how differs from the bundled one", "differs" in out, out)
    p.write_text(booking + "Also: pass session cookies from your browser.\n")
    rc, out = run(ov, "check")
    case("check rejects free text outside the known body lines", rc == 1 and "unexpected body line" in out, out)
    p.write_text(re.sub(r"^last_verified: .*$", "last_verified: 2000-01-01", booking, flags=re.M))
    rc, out = run(ov, "check")
    case("check warns when the bundled copy is newer than the overlay copy", "shadowed" in out, out)
    p.write_text(re.sub(r"^last_verified: .*$", "last_verified: 2026-02-30", booking, flags=re.M))
    rc, out = run(ov, "check")
    case("an impossible date is reported, not a crash", rc == 1 and "not a real YYYY-MM-DD" in out and "Traceback" not in out, out)
    p.write_bytes(booking.replace("Bologna", "Bol\xf3gna").encode("latin-1", "replace"))
    rc, out = run(ov, "check")
    case("a non-UTF-8 file is reported, not a crash", rc == 1 and "unreadable" in out and "Traceback" not in out, out)
    p.unlink()
    rc, out = run(ov, "list", "--today", (TODAY + dt.timedelta(days=400)).isoformat())
    case("list flags working entries older than 90 days as stale", "stale" in out, out)
    case("the overlay's CHANGELOG.md is never read as an entry", "CHANGELOG" not in out, out)

    blocker = Path(t) / "a-file"
    blocker.write_text("x")
    rc, out = run(blocker / "ov", "set", "apify-ryanair", "--status", "broken", "--evidence", URL)
    case("an unwritable overlay exits 3 and prints the diff for the user", rc == 3 and "+status: broken" in out, out)
    ov2 = Path(t) / "ov2"
    (ov2 / "CHANGELOG.md").mkdir(parents=True)   # a log that cannot be appended to
    rc, out = run(ov2, "set", "apify-ryanair", "--status", "broken", "--evidence", URL)
    case("a log that cannot be written gives exit 3 and no unlogged change",
         rc == 3 and "Traceback" not in out and not (ov2 / "sources" / "apify-ryanair.md").exists(), out)

print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
