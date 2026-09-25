#!/usr/bin/env python3
"""Tests for check_skills.py. Run: python3 .github/scripts/test_check_skills.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOOD = """---
name: {name}
description: Does a thing. Use when a thing is needed.
license: MIT
metadata:
  version: "1.0"
---
See `patterns/a.md` and the overlay's `CHANGELOG.md`.
"""


def run(skill_md, dirname="demo", extra=None):
    with tempfile.TemporaryDirectory() as t:
        d = Path(t, "skills", dirname)
        (d / "patterns").mkdir(parents=True)
        (d / "patterns" / "a.md").write_text("x")
        (d / "SKILL.md").write_text(skill_md)
        for rel, body in (extra or {}).items():
            (d / rel).write_text(body)
        p = subprocess.run([sys.executable, str(HERE / "check_skills.py"), t], capture_output=True, text=True)
        return p.returncode, p.stderr


CASES = [
    ("valid skill passes; bare overlay filename is not a skill reference", GOOD.format(name="demo"), "demo", None, 0, ""),
    ("name must match directory", GOOD.format(name="other"), "demo", None, 1, "does not match directory"),
    ("uppercase name rejected", GOOD.format(name="Demo"), "Demo", None, 1, "naming rule"),
    ("double hyphen rejected", GOOD.format(name="de--mo"), "de--mo", None, 1, "naming rule"),
    ("unquoted numeric metadata rejected", GOOD.format(name="demo").replace('"1.0"', "1.0"), "demo", None, 1, "not load as a string"),
    ("unquoted date metadata rejected", GOOD.format(name="demo").replace('version: "1.0"', "released: 2026-09-25"), "demo", None, 1, "not load as a string"),
    ("unquoted yes/no metadata rejected", GOOD.format(name="demo").replace('version: "1.0"', "beta: yes"), "demo", None, 1, "not load as a string"),
    ("semver-looking metadata is a string and passes", GOOD.format(name="demo").replace('"1.0"', "1.2.3"), "demo", None, 0, ""),
    ("folded description passes", GOOD.format(name="demo").replace("description: Does a thing. Use when a thing is needed.", "description: >-\n  Does a thing.\n  Use when needed."), "demo", None, 0, ""),
    ("trailing comment on name passes", GOOD.format(name="demo").replace("name: demo", "name: demo # the id"), "demo", None, 0, ""),
    ("allowed-tools as block list rejected", GOOD.format(name="demo").replace("license: MIT", "license: MIT\nallowed-tools:\n  - Read"), "demo", None, 1, "allowed-tools"),
    ("dangling plain-text reference rejected", GOOD.format(name="demo"), "demo", {"patterns/b.md": "see patterns/gone.md step 2"}, 1, "does not resolve"),
    ("reference outside the skill rejected", GOOD.format(name="demo"), "demo", {"patterns/b.md": "see `../patterns/a.md`"}, 1, "outside the skill"),
    ("dangling reference rejected", GOOD.format(name="demo").replace("patterns/a.md", "patterns/missing.md"), "demo", None, 1, "does not resolve"),
    ("dangling reference in a pattern file rejected", GOOD.format(name="demo"), "demo", {"patterns/b.md": "see `sources/x.md`"}, 1, "does not resolve"),
    ("missing description rejected", GOOD.format(name="demo").replace("description: Does a thing. Use when a thing is needed.\n", ""), "demo", None, 1, "description"),
    ("over-long description rejected", GOOD.format(name="demo").replace("Does a thing.", "x" * 1100), "demo", None, 1, "max 1024"),
    ("install metadata rejected", GOOD.format(name="demo").replace('version: "1.0"', 'version: "1.0"\n  github-repo: x/y'), "demo", None, 1, "install metadata"),
    ("allowed-tools as list rejected", GOOD.format(name="demo").replace("license: MIT", "license: MIT\nallowed-tools: [Read]"), "demo", None, 1, "allowed-tools"),
]

fails = 0
for label, md, dirname, extra, want_rc, want_err in CASES:
    rc, err = run(md, dirname, extra)
    ok = rc == want_rc and want_err in err
    fails += not ok
    print(("PASS " if ok else "FAIL ") + label + ("" if ok else f"  (rc={rc}, stderr={err.strip()!r})"))
print(f"{len(CASES) - fails}/{len(CASES)} passed")
sys.exit(1 if fails else 0)
