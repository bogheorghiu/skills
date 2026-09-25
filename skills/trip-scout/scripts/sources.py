#!/usr/bin/env python3
"""trip-scout source registry tool: resolve the overlay, list, check, and edit entries.

Stdlib only (Python 3; tested on 3.11). patterns/adapt.md holds the rules; this script
applies the parts a machine can check, because an agent late in a long session keeps
counts and dates only as a vague memory, and a refusal at the moment of the mistake
does not fade that way.

Threat model: a well-meaning agent that makes mistakes, not an adversary. An agent set on
breaking the rules can edit the files directly or feed this script crafted text; nothing
in a skill folder can stop that, and the checks here do not try to. What they do: refuse
the mistakes such an agent actually makes (vague evidence, a lost drop field or caveat,
a sixth change in a day, a forbidden technique written into `how`), and, through `check`
at load time, demote any entry that fails however it was written: SKILL.md tells the
agent to treat it as `untested` for the session.

Run `python3 sources.py --help` or `python3 sources.py <command> --help` for usage.
Exit codes: 0 ok, 1 refused or invalid, 2 usage error, 3 overlay not writable (the
change is printed as a diff for the user to apply: adapt.md's propose-only mode).
"""
import argparse
import datetime as dt
import difflib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
BUNDLED = SKILL_DIR / "sources"

# Enums mirror sources/README.md; change both together.
KINDS = {"flight-calendar", "flight-aggregator", "lodging", "page-render", "geocoder",
         "router", "vector-data", "reference"}
CONNECTORS = {"apify", "zapier", "brightdata", "web"}
STATUSES = {"working", "degraded", "broken", "deprecated", "untested"}
REQUIRED = ["id", "kind", "connector", "target", "status", "last_verified", "evidence"]
BODY_KEYS = ["how", "caveats", "drop"]

STALE_DAYS = 90
DAILY_CAP = 5
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# A handle a reader can follow: a URL; a platform run/dataset ID (17 characters mixing
# letters with digits, or several capitals with lower case, as Apify IDs do); or a
# double-quoted fragment of real output. It catches vague evidence, not invented
# evidence; nothing here can.
HANDLE_RE = re.compile(
    r"https?://\S+"
    r"|\b(?:(?=[A-Za-z0-9]*\d)(?=[A-Za-z0-9]*[A-Za-z])|(?=[A-Za-z0-9]*[A-Z][A-Za-z0-9]*[A-Z])(?=[A-Za-z0-9]*[a-z]))[A-Za-z0-9]{17}\b"
    "|[\"“][^\"“”]{20,}[\"”]")
# Invariant 3 and adapt.md's hard limits: no logged-in, proxied or CAPTCHA-solving
# sources. Scanned in `target` and `how` only: `caveats` legitimately say "never use
# residential proxies", and a warning must not read as a violation.
FORBIDDEN = re.compile(
    r"\b(log(?:ged|ging)?[- ]?ins?|sign(?:ed|ing)?[- ]?in|passwords?|(?:session|auth|browser|login)[- ]cookies?|cookies? from|session[- ]tokens?|auth[- ]tokens?"
    r"|captchas?|residential[- _]?prox\w*|rotating[- _]?prox\w*|proxyconfiguration|apifyproxygroups)\b", re.I)
# Characters str.splitlines() treats as line breaks; any of them in a value would start
# a new line, i.e. inject a second key into the entry.
LINE_BREAKS = re.compile("[\x00-\x1f\x7f\x85  ]")
NONE_TOKENS = {"", "-", "—", "none"}
REC_SEP, FIELD_SEP = " ;; ", " :: "   # drop_removed record format: field :: reason :: date


class Refused(Exception):
    pass


# ---------- locating ----------

def overlay_dir():
    """Resolve the overlay folder in adapt.md's order; return (path, rule)."""
    if os.environ.get("TRIP_SCOUT_HOME"):
        return Path(os.path.expanduser(os.environ["TRIP_SCOUT_HOME"])), "TRIP_SCOUT_HOME"
    if os.environ.get("CLAUDE_PLUGIN_DATA"):
        return Path(os.path.expanduser(os.environ["CLAUDE_PLUGIN_DATA"])) / "trip-scout", "CLAUDE_PLUGIN_DATA"
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return Path(base) / "trip-scout", "XDG_DATA_HOME default"


def writable(path):
    """Best guess without writing; the real test is the write itself (see apply_change)."""
    probe = path
    while not probe.exists():
        if probe.parent == probe:
            return False
        probe = probe.parent
    return probe.is_dir() and os.access(probe, os.W_OK)


def today():
    # Tests pin the date through this variable. It is not a way around the daily cap
    # worth guarding: an agent willing to set it could as easily edit the files.
    pinned = os.environ.get("TRIP_SCOUT_TEST_TODAY")
    return dt.date.fromisoformat(pinned) if pinned else dt.date.today()


def parse_date(s):
    try:
        return dt.date.fromisoformat(s) if DATE_RE.match(s or "") else None
    except ValueError:
        return None


# ---------- parsing ----------

def unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")   # YAML single-quoted: '' is a literal quote
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1].replace('\\"', '"')
    return re.split(r"\s+#", v, maxsplit=1)[0].strip()  # an unquoted value may carry a trailing comment


def split_front(lines):
    """Index of the closing '---', or None."""
    if not lines or lines[0].strip() != "---":
        return None
    return next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)


def parse(text):
    """Return (front: dict, body: dict, errors: list). Frontmatter is flat `key: value`."""
    errors, front, body = [], {}, {}
    lines = text.splitlines()
    end = split_front(lines)
    if end is None:
        return front, body, ["file must start with a '---' frontmatter block closed by '---'"]
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r"^([a-z_]+):\s*(.*)$", raw)
        if not m:
            errors.append(f"frontmatter line is not flat 'key: value': {raw.strip()!r}")
            continue
        if m.group(1) in front:
            errors.append(f"frontmatter key {m.group(1)!r} appears twice")
        front[m.group(1)] = unquote(m.group(2))
    for raw in lines[end + 1:]:
        m = re.match(r"^(how|caveats|drop|drop_removed):\s*(.*)$", raw)
        if m:
            if m.group(1) in body:
                errors.append(f"body line {m.group(1)!r} appears twice")
            body[m.group(1)] = m.group(2).strip()
        elif raw.strip():
            # A future session reads the whole body as instructions; only the known,
            # checked lines may carry any.
            errors.append(f"unexpected body line (only how/caveats/drop/drop_removed): {raw.strip()[:60]!r}")
    return front, body, errors


def drop_tokens(value):
    return {t.strip() for t in (value or "").split(",") if t.strip().lower() not in NONE_TOKENS}


def removed_tokens(value):
    """`drop_removed: field :: reason :: date ;; field2 :: reason :: date` -> {field, field2}."""
    return {rec.split(FIELD_SEP.strip())[0].strip() for rec in (value or "").split(REC_SEP.strip()) if rec.strip()}


def load(folder):
    """Entries of one layer: bundled `sources/`, or `<overlay>/sources/` (never the overlay root)."""
    out = {}
    if not folder.is_dir():
        return out
    for p in sorted(folder.glob("*.md")):
        if p.name == "README.md":
            continue
        try:
            text = p.read_text(encoding="utf-8")
            front, body, errors = parse(text)
        except (UnicodeDecodeError, OSError) as exc:
            text, front, body, errors = "", {}, {}, [f"unreadable: {exc.__class__.__name__}"]
        out[p.stem] = {"path": p, "text": text, "front": front, "body": body, "parse_errors": errors}
    return out


# ---------- validation ----------

def validate(entry, stem, bundled_entry, on):
    """Return (errors, warnings) for one entry. `bundled_entry` is set for overlay copies."""
    e, w = list(entry["parse_errors"]), []
    f, b = entry["front"], entry["body"]
    for k in REQUIRED:
        if not f.get(k):
            e.append(f"missing frontmatter key: {k}")
    if f.get("id") and f["id"] != stem:
        e.append(f"id {f['id']!r} does not match filename {stem!r}")
    for key, allowed in (("kind", KINDS), ("connector", CONNECTORS), ("status", STATUSES)):
        if f.get(key) and f[key] not in allowed:
            e.append(f"{key} {f[key]!r} is not one of {sorted(allowed)}")
    lv = f.get("last_verified", "")
    if lv:
        d = parse_date(lv)
        if d is None:
            e.append(f"last_verified {lv!r} is not a real YYYY-MM-DD date")
        elif d > on:
            e.append(f"last_verified {lv} is in the future")
        elif (on - d).days > STALE_DAYS and f.get("status") in ("working", "degraded"):
            w.append(f"stale: last verified {(on - d).days} days ago; re-verify before relying on it")
    for k in BODY_KEYS:
        if k not in b:
            e.append(f"missing body line: {k}:")
    if f.get("kind") == "lodging" and not drop_tokens(b.get("drop")):
        e.append("a lodging source must list personal fields to drop (invariant 5)")
    if f.get("evidence") and f.get("status") != "untested" and not HANDLE_RE.search(f["evidence"]):
        e.append('evidence has no handle (a URL, a run/dataset ID, or a "double-quoted" output fragment of 20+ chars)')
    hit = FORBIDDEN.search(" ".join([f.get("target", ""), b.get("how", "")]))
    if hit:
        e.append(f"`how`/`target` mention {hit.group(0)!r}: adapt.md forbids sources needing login, cookies, "
                 "CAPTCHA solving or proxies beyond actor defaults")
    if bundled_entry:
        missing = drop_tokens(bundled_entry["body"].get("drop")) - drop_tokens(b.get("drop")) - removed_tokens(b.get("drop_removed"))
        if missing:
            e.append(f"drop list lacks {sorted(missing)}, which the bundled entry drops. If upstream added it, add it here "
                     "(set ID --drop \"<current list>, <field>\"; adding needs no evidence). If it was removed on purpose, "
                     "the removal must be recorded (set --allow-drop-removal FIELD --reason ...).")
        blv, olv = parse_date(bundled_entry["front"].get("last_verified")), parse_date(f.get("last_verified"))
        if blv and olv and blv > olv:
            w.append(f"shadowed: the bundled entry was verified later ({blv}) than this overlay copy ({olv}); compare them")
        differ = [k for k in ("target", "how", "caveats") if (bundled_entry["front"] if k == "target" else bundled_entry["body"]).get(k)
                  != (f if k == "target" else b).get(k)]
        if differ:
            # An overlay copy hides every later upstream fix to these lines, even one made
            # only to renew a date; say so, so the agent compares instead of trusting either.
            w.append(f"differs: this overlay copy's {', '.join(differ)} differ from the bundled entry; if the bundled text is newer, it may fix what the overlay still says")
    return e, w


def merged(on):
    ov, _ = overlay_dir()
    bundled, overlay = load(BUNDLED), load(ov / "sources")
    rows = []
    for stem in sorted(set(bundled) | set(overlay)):
        layer = "overlay" if stem in overlay else "bundled"
        entry = overlay.get(stem) or bundled[stem]
        errors, warnings = validate(entry, stem, bundled.get(stem) if layer == "overlay" else None, on)
        rows.append({"id": stem, "layer": layer, "path": str(entry["path"]), "front": entry["front"],
                     "errors": errors, "warnings": warnings})
    return rows


# ---------- commands ----------

def cmd_where(args):
    path, rule = overlay_dir()
    ok = writable(path)
    print(f"overlay: {path}\nchosen by: {rule}\nexists: {path.exists()}\nwritable: {ok}")
    return 0 if ok else 3


def on_date(args):
    return dt.date.fromisoformat(args.today) if args.today else today()


def cmd_list(args):
    rows = merged(on_date(args))
    if args.json:
        print(json.dumps([dict(id=r["id"], layer=r["layer"], kind=r["front"].get("kind"),
                               status=r["front"].get("status"), last_verified=r["front"].get("last_verified"),
                               errors=r["errors"], warnings=r["warnings"]) for r in rows], indent=2))
        return 0
    print(f"overlay: {overlay_dir()[0]}")
    print(f"{'id':24} {'kind':18} {'status':11} {'verified':11} {'layer':8} flags")
    for r in rows:
        flags = ["INVALID->treat as untested"] if r["errors"] else []
        flags += [x.split(":")[0] for x in r["warnings"]]
        f = r["front"]
        print(f"{r['id']:24} {f.get('kind', '?'):18} {f.get('status', '?'):11} {f.get('last_verified', '?'):11} {r['layer']:8} {', '.join(flags)}")
    return 0


def cmd_check(args):
    rows = merged(on_date(args))
    if args.json:
        print(json.dumps([{k: r[k] for k in ("id", "layer", "path", "errors", "warnings")} for r in rows], indent=2))
    else:
        print(f"overlay: {overlay_dir()[0]}")
        for r in rows:
            for x in r["errors"]:
                print(f"ERROR {r['id']} ({r['layer']}): {x}")
            for x in r["warnings"]:
                print(f"WARN  {r['id']} ({r['layer']}): {x}")
        bad = sum(1 for r in rows if r["errors"])
        print(f"{len(rows)} entries, {bad} invalid" + (" (treat invalid entries as untested this session)" if bad else ""))
    return 1 if any(r["errors"] for r in rows) else 0


def changes_logged(changelog, on):
    """Source changes logged on this date that count toward the cap. Approved pattern edits
    and pure re-verifications (`verify`: new evidence and date, nothing else) do not: a trip
    that re-checks seven stale sources must still be able to record a real fix."""
    if not changelog.is_file():
        return 0
    return sum(1 for ln in changelog.read_text(encoding="utf-8", errors="replace").splitlines()
               if ln.startswith(on.isoformat()) and "| sources/" in ln and "| verify " not in ln)


def replace_line(text, key, value, in_front):
    """Substitute one `key: value` line, keeping every other byte; append it if absent."""
    lines = text.splitlines(keepends=True)
    end = split_front([ln.rstrip("\n") for ln in lines])
    if end is None:
        raise Refused("schema: the current entry has no closed frontmatter; fix or replace it by hand first")
    rng = range(1, end) if in_front else range(end + 1, len(lines))
    if in_front and key == "evidence":
        # Valid YAML either way: double quotes unless the value has one, then single quotes.
        rendered = f'{key}: "{value}"' if '"' not in value else "{}: '{}'".format(key, value.replace("'", "''"))
    else:
        rendered = f"{key}: {value}"
    for i in rng:
        if re.match(rf"^{key}:", lines[i]):
            lines[i] = rendered + "\n"
            return "".join(lines)
    if in_front:
        lines.insert(end, rendered + "\n")
    else:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(rendered + "\n")
    return "".join(lines)


def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def apply_change(args, new_entry):
    on = today()
    ov, _ = overlay_dir()
    if not ID_RE.match(args.id):
        raise Refused(f'id: "{args.id}" must match {ID_RE.pattern}; only <overlay>/sources/<id>.md is writable. '
                      "SKILL.md, reference/legal.md and patterns/ are not editable here: propose an upstream PR text instead.")
    values = {k: getattr(args, k, None) for k in ("status", "last_verified", "evidence", "how", "caveats", "add_caveat",
                                                  "drop", "kind", "connector", "target", "note", "reason")}
    values["allow_drop_removal"] = " ".join(args.allow_drop_removal or []) or None
    for k, v in values.items():
        if v is None:
            continue
        # Every value lands on one line of the entry or of the CHANGELOG line.
        if LINE_BREAKS.search(v):
            raise Refused(f"schema: --{k.replace('_', '-')} must be one line (no line breaks or control characters)")
        if k in ("reason", "allow_drop_removal") and (";;" in v or "::" in v):
            raise Refused(f"schema: --{k.replace('_', '-')} must not contain ';;' or '::' (they separate drop_removed records)")
    bundled, overlay = load(BUNDLED), load(ov / "sources")
    current = overlay.get(args.id) or bundled.get(args.id)
    if new_entry and current:
        raise Refused(f'exists: "{args.id}" already exists. Use set.')
    if not new_entry and not current:
        raise Refused(f'unknown: no entry "{args.id}" in the bundled registry or the overlay. Use add.')

    front_updates, body_updates = {}, {}
    for k in ("status", "evidence"):
        if values[k] is not None:
            front_updates[k] = values[k]
    if values["last_verified"]:
        front_updates["last_verified"] = on.isoformat() if values["last_verified"] == "today" else values["last_verified"]
    elif values["evidence"] is not None:
        # last_verified is the date of the evidence (sources/README.md): new evidence, new date.
        front_updates["last_verified"] = on.isoformat()
    for k in ("how", "drop"):
        if values[k] is not None:
            body_updates[k] = values[k]
    old_caveats = (current["body"].get("caveats") or "").strip() if current else ""
    if values["caveats"] is not None and values["add_caveat"] is not None:
        raise Refused("schema: pass --caveats (replace) or --add-caveat (append), not both")
    if values["add_caveat"] is not None:
        body_updates["caveats"] = f"{old_caveats} {values['add_caveat']}".strip()
    elif values["caveats"] is not None:
        body_updates["caveats"] = values["caveats"]
    replaces_caveats = values["caveats"] is not None and bool(old_caveats)
    if new_entry:
        front_updates.update({"id": args.id, "kind": args.kind, "connector": args.connector, "target": args.target})
        front_updates.setdefault("last_verified", on.isoformat())
        if args.status not in ("working", "untested"):
            raise Refused("schema: a new entry starts as working (it passed a real run) or untested")
    if not (set(front_updates) | set(body_updates)):
        raise Refused("nothing to change: pass at least one field")

    # Drop-list bookkeeping. Adding fields is always allowed (adapt.md); removing one needs
    # evidence and a named, reasoned override, recorded in the entry itself so the load-time
    # check can tell an approved removal from a silent one.
    lost, allowed = set(), {x.strip() for x in (args.allow_drop_removal or [])}
    if "drop" in body_updates and current:
        baseline = drop_tokens(current["body"].get("drop"))
        if args.id in bundled:
            baseline |= drop_tokens(bundled[args.id]["body"].get("drop")) - removed_tokens(current["body"].get("drop_removed"))
        lost = baseline - drop_tokens(body_updates["drop"])
        if lost - allowed:
            raise Refused(f'drop: {sorted(lost - allowed)} would leave the drop list. Keep them, or pass '
                          '--allow-drop-removal "<field>" --reason "<why it no longer applies>"; the removal is recorded.')
    if allowed - lost:
        raise Refused(f"drop: --allow-drop-removal names {sorted(allowed - lost)}, which this change does not remove")
    if lost and not args.reason:
        raise Refused("drop: --allow-drop-removal needs --reason")

    needs_evidence = (set(front_updates) | set(body_updates)) & {"status", "last_verified", "how", "caveats"}
    if lost:
        needs_evidence.add("drop")
    ev = front_updates.get("evidence")
    if needs_evidence and not ev:
        raise Refused(f"evidence-required: changing {sorted(needs_evidence)} needs --evidence from this session "
                      "(adapt.md, 'What may change').")
    status_after = front_updates.get("status") or (current["front"].get("status") if current else None)
    if ev and status_after != "untested" and not HANDLE_RE.search(ev):
        raise Refused(f'evidence: --evidence needs a handle: a URL, a run/dataset ID, or the error or output line itself '
                      f'in double quotes (20+ characters). Got: "{ev}". Copy it from the run; do not invent one.')
    if replaces_caveats and not args.reason:
        raise Refused("caveats: --caveats replaces the whole line and removes what it said. Use --add-caveat to add a "
                      "sentence, or pass --reason saying why each dropped caveat no longer applies (adapt.md: never remove "
                      "a caveat without evidence).")
    for k, allowed_values in (("status", STATUSES), ("kind", KINDS), ("connector", CONNECTORS)):
        if k in front_updates and front_updates[k] not in allowed_values:
            raise Refused(f"schema: {k} must be one of {sorted(allowed_values)}")
    if "last_verified" in front_updates and parse_date(front_updates["last_verified"]) is None:
        raise Refused("schema: last_verified must be a real YYYY-MM-DD date or 'today'")
    hit = FORBIDDEN.search(" ".join([front_updates.get("target", ""), body_updates.get("how", "")]))
    if hit:
        raise Refused(f'invariant: "{hit.group(0)}" found in the new how/target. adapt.md forbids sources needing login, '
                      "cookies, CAPTCHA solving, or proxies beyond actor defaults. If this is a false positive, tell the "
                      "user; do not reword and retry.")

    old = current["text"] if current else "---\n---\nhow: \ncaveats: \ndrop: —\n"
    new = old
    for k in ["id", "kind", "connector", "target", "status", "last_verified", "evidence"]:
        if k in front_updates:
            new = replace_line(new, k, front_updates[k], True)
    for k, v in body_updates.items():
        new = replace_line(new, k, v, False)
    if lost:
        prior = (current["body"].get("drop_removed") or "").strip()
        record = REC_SEP.join(f"{x}{FIELD_SEP}{args.reason}{FIELD_SEP}{on.isoformat()}" for x in sorted(lost))
        new = replace_line(new, "drop_removed", f"{prior}{REC_SEP}{record}" if prior else record, False)

    # Validate what would be written before any output path, so a dry run or a proposed
    # diff never shows the user a change the real write would refuse.
    nf, nb, nerr = parse(new)
    errors, _ = validate({"front": nf, "body": nb, "parse_errors": nerr}, args.id, bundled.get(args.id), on)
    if errors:
        raise Refused("schema: the resulting entry would be invalid: " + "; ".join(errors))

    def cell(v):  # the log is '|'-separated; keep each field in its column
        return str(v).replace("|", "/")
    summary = ", ".join(f"{k}={cell(v)}" for k, v in {**front_updates, **body_updates}.items() if k not in ("evidence", "id"))
    if lost:
        summary += f"; DROP REMOVED {sorted(lost)} because {cell(args.reason)}"
    if replaces_caveats:
        summary += f"; CAVEATS REPLACED because {cell(args.reason)}"
    verb = "add" if new_entry else ("verify" if set(front_updates) <= {"evidence", "last_verified"} and not body_updates else "set")
    log_line = (f"{on.isoformat()} | sources/{args.id}.md | {verb} {summary} | "
                f"{cell(ev or '-')} | {cell(values['note'] or '')}\n")
    diff = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                        f"a/sources/{args.id}.md", f"b/sources/{args.id}.md"))
    proposal = f"{diff}\nCHANGELOG line:\n{log_line}"
    if args.dry_run:
        print(proposal, end="")
        return 0
    changelog = ov / "CHANGELOG.md"
    if verb != "verify" and changes_logged(changelog, on) >= DAILY_CAP:
        raise Refused(f"cap: {DAILY_CAP} source changes already logged today in {changelog}. adapt.md allows at most "
                      f"{DAILY_CAP} autonomous changes per session (counted per day here). Stop; show the user this "
                      "change with --dry-run instead.")
    # Log first, then write: a failure between the two leaves a logged change that did not
    # happen (it still counts toward the cap), never a change that was not logged.
    target = ov / "sources" / f"{args.id}.md"
    try:
        ov.mkdir(parents=True, exist_ok=True)
        with open(changelog, "a", encoding="utf-8") as fh:
            fh.write(log_line)
        write_atomic(target, new)
    except OSError as exc:
        print(f"overlay {ov} is not writable ({exc.__class__.__name__}); propose this change to the user instead:\n{proposal}", end="")
        return 3
    print(f"overlay: {ov}\nwrote {target}\nlogged: {log_line}", end="")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("where", help="print the resolved overlay folder and whether it is writable")
    for name, h in (("list", "merged bundled+overlay table with computed staleness"),
                    ("check", "validate every entry; exit 1 if any is invalid (treat those as untested)")):
        p = sub.add_parser(name, help=h)
        p.add_argument("--json", action="store_true")
        p.add_argument("--today", help="YYYY-MM-DD: judge staleness as of this date")
    for name in ("set", "add"):
        p = sub.add_parser(name, help=("change fields of an existing entry (written to the overlay)" if name == "set"
                                       else "add a new entry that passed one real run this session"))
        p.add_argument("id")
        p.add_argument("--status", required=(name == "add"))
        p.add_argument("--last-verified", help="YYYY-MM-DD or 'today'; needs --evidence")
        p.add_argument("--evidence", help='a URL, a run/dataset ID, or the output/error line in double quotes')
        p.add_argument("--how", help="replaces the how line")
        p.add_argument("--add-caveat", help="appends a sentence to the caveats line")
        p.add_argument("--caveats", help="replaces the caveats line; needs --reason if it had text")
        p.add_argument("--drop", help='the full comma-separated drop list, e.g. "host.about, review authors"')
        p.add_argument("--note", default="")
        p.add_argument("--dry-run", action="store_true", help="print the diff and CHANGELOG line; write nothing")
        p.add_argument("--allow-drop-removal", action="append", metavar="FIELD",
                       help="name a drop field this change removes (repeat per field); needs --reason")
        p.add_argument("--reason", help="why a removed drop field or caveat no longer applies")
        if name == "add":
            p.add_argument("--kind", required=True)
            p.add_argument("--connector", required=True)
            p.add_argument("--target", required=True)
    args = ap.parse_args(argv)
    try:
        if args.cmd in ("set", "add"):
            return apply_change(args, args.cmd == "add")
        return {"where": cmd_where, "list": cmd_list, "check": cmd_check}[args.cmd](args)
    except Refused as r:
        print(f"REFUSED {r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
