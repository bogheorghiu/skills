#!/usr/bin/env python3
"""trip-scout source registry tool: resolve the overlay, list, check, and edit entries.

Stdlib only (Python 3.8+). patterns/adapt.md holds the rules; this script applies the
parts of them that a machine can check, because an agent late in a long session keeps
the counts and dates in adapt.md only as a vague memory, and a refusal message at the
moment of the mistake does not fade that way.

This script cannot stop a direct file edit. The guard is `check` at load time:
SKILL.md tells the agent to treat any entry `check` rejects as `untested` for the
session, however that entry was written.

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
FRONT_EDITABLE = {"status", "last_verified", "evidence"}

STALE_DAYS = 90
DAILY_CAP = 5
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# A handle a reader can follow: a URL, a platform run/dataset ID, or a quoted
# fragment of real output. It catches vague evidence, not invented evidence.
HANDLE_RE = re.compile(r'https?://\S+|\b(?=[A-Za-z0-9]*\d)(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{17}\b|["“][^"”]{20,}["”]')
# Invariant 3 and adapt.md's hard limits: no logged-in, proxied or CAPTCHA-solving sources.
FORBIDDEN = ["login", "log in", "password", "cookie", "session token", "captcha",
             "residential", "rotating prox", "proxyconfiguration"]
NONE_TOKENS = {"", "-", "—", "none"}


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
    probe = path
    while not probe.exists():
        if probe.parent == probe:
            return False
        probe = probe.parent
    return probe.is_dir() and os.access(probe, os.W_OK)


# ---------- parsing ----------

def unquote(v):
    v = v.strip()
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'" else v


def parse(text):
    """Return (front: dict, body: dict, errors: list). Frontmatter is flat `key: value`."""
    errors, front, body = [], {}, {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return front, body, ["file must start with '---' frontmatter"]
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return front, body, ["frontmatter is not closed with '---'"]
    for raw in lines[1:end]:
        s = raw.rstrip()
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        m = re.match(r"^([a-z_]+):\s*(.*)$", s)
        if not m or raw.startswith((" ", "\t")):
            errors.append(f"frontmatter line is not flat 'key: value': {raw.strip()!r}")
            continue
        front[m.group(1)] = unquote(m.group(2))
    for raw in lines[end + 1:]:
        m = re.match(r"^(how|caveats|drop):\s*(.*)$", raw)
        if m:
            body[m.group(1)] = m.group(2).strip()
    return front, body, errors


def drop_tokens(value):
    return {t.strip() for t in (value or "").split(",") if t.strip().lower() not in NONE_TOKENS}


def load(layer_dir):
    out = {}
    if (layer_dir / "sources").is_dir():
        layer_dir = layer_dir / "sources"
    if not layer_dir.is_dir():
        return out
    for p in sorted(layer_dir.glob("*.md")):
        if p.name == "README.md":
            continue
        text = p.read_text(encoding="utf-8")
        front, body, errors = parse(text)
        out[p.stem] = {"path": p, "text": text, "front": front, "body": body, "parse_errors": errors}
    return out


def today_from(args):
    return dt.date.fromisoformat(args.today) if getattr(args, "today", None) else dt.date.today()


# ---------- validation ----------

def validate(entry, stem, layer, bundled_entry, today):
    """Return (errors, warnings) for one entry."""
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
    if lv and lv != "null":
        if not DATE_RE.match(lv):
            e.append("last_verified must be YYYY-MM-DD")
        else:
            d = dt.date.fromisoformat(lv)
            if d > today:
                e.append(f"last_verified {lv} is in the future")
            elif (today - d).days > STALE_DAYS and f.get("status") in ("working", "degraded"):
                w.append(f"stale: last verified {(today - d).days} days ago; re-verify before relying on it")
    elif lv == "null" and f.get("status") != "untested":
        e.append("last_verified may be null only for status untested")
    for k in BODY_KEYS:
        if k not in b:
            e.append(f"missing body line: {k}:")
    if f.get("kind") == "lodging" and not drop_tokens(b.get("drop")):
        e.append("a lodging source must list personal fields to drop (invariant 5)")
    if layer == "overlay":
        if f.get("evidence") and f.get("status") != "untested" and not HANDLE_RE.search(f["evidence"]):
            e.append("evidence has no handle (a URL, a run/dataset ID, or a quoted output fragment of 20+ chars)")
        hit = forbidden_word(" ".join([f.get("target", ""), b.get("how", ""), b.get("caveats", "")]))
        if hit:
            e.append(f"mentions {hit!r}: adapt.md forbids sources needing login, CAPTCHA solving or proxies beyond actor defaults")
        if bundled_entry:
            lost = drop_tokens(bundled_entry["body"].get("drop")) - drop_tokens(b.get("drop"))
            if lost:
                e.append(f"drop list is missing bundled field(s) {sorted(lost)}; removal needs evidence (use set --allow-drop-removal)")
            blv, olv = bundled_entry["front"].get("last_verified", ""), f.get("last_verified", "")
            if DATE_RE.match(blv) and DATE_RE.match(olv) and blv > olv:
                w.append(f"shadowed: the bundled entry was verified later ({blv}) than this overlay copy ({olv}); compare them")
    return e, w


def forbidden_word(text):
    low = text.lower()
    return next((word for word in FORBIDDEN if word in low), None)


def merged(today):
    ov, _ = overlay_dir()
    bundled, overlay = load(BUNDLED), load(ov)
    rows = []
    for stem in sorted(set(bundled) | set(overlay)):
        layer = "overlay" if stem in overlay else "bundled"
        entry = overlay.get(stem) or bundled[stem]
        errors, warnings = validate(entry, stem, layer, bundled.get(stem) if layer == "overlay" else None, today)
        if layer == "overlay" and stem in bundled:
            b_err, _ = validate(bundled[stem], stem, "bundled", None, today)
            errors += [f"(bundled copy) {x}" for x in b_err]
        rows.append({"id": stem, "layer": layer, "path": str(entry["path"]), "front": entry["front"],
                     "body": entry["body"], "errors": errors, "warnings": warnings})
    return rows


# ---------- commands ----------

def cmd_where(args):
    path, rule = overlay_dir()
    ok = writable(path)
    print(f"overlay: {path}\nchosen by: {rule}\nexists: {path.exists()}\nwritable: {ok}")
    return 0 if ok else 3


def cmd_list(args):
    today = today_from(args)
    rows = merged(today)
    if args.json:
        print(json.dumps([dict({k: r[k] for k in ("id", "layer", "errors", "warnings")},
                               kind=r["front"].get("kind"), status=r["front"].get("status"),
                               last_verified=r["front"].get("last_verified")) for r in rows], indent=2))
        return 0
    print(f"overlay: {overlay_dir()[0]}")
    print(f"{'id':24} {'kind':18} {'status':11} {'verified':11} {'layer':8} flags")
    for r in rows:
        flags = ["INVALID->treat as untested"] if r["errors"] else []
        flags += [w.split(":")[0] for w in r["warnings"]]
        f = r["front"]
        print(f"{r['id']:24} {f.get('kind', '?'):18} {f.get('status', '?'):11} {f.get('last_verified', '?'):11} {r['layer']:8} {', '.join(flags)}")
    return 0


def cmd_check(args):
    rows = merged(today_from(args))
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


def changelog_count(changelog, today):
    if not changelog.exists():
        return 0
    return sum(1 for ln in changelog.read_text(encoding="utf-8").splitlines() if ln.startswith(today.isoformat()))


def replace_line(text, key, value, in_front):
    """Substitute one `key: value` line, keeping every other byte; append it if absent."""
    lines = text.splitlines(keepends=True)
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    rng = range(1, end) if in_front else range(end + 1, len(lines))
    rendered = f'{key}: "{value}"' if in_front and key == "evidence" else f"{key}: {value}"
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
    today = today_from(args)
    ov, _ = overlay_dir()
    if not ID_RE.match(args.id):
        raise Refused(f'id: "{args.id}" must match {ID_RE.pattern}; only <overlay>/sources/<id>.md is writable. '
                      "SKILL.md, reference/legal.md and patterns/ are not editable here: propose an upstream PR text instead.")
    bundled, overlay = load(BUNDLED), load(ov)
    current = overlay.get(args.id) or bundled.get(args.id)
    if new_entry and current:
        raise Refused(f'exists: "{args.id}" already exists. Use set.')
    if not new_entry and not current:
        raise Refused(f'unknown: no entry "{args.id}" in the bundled registry or the overlay. Use add.')
    changelog = ov / "CHANGELOG.md"
    if changelog_count(changelog, today) >= DAILY_CAP:
        raise Refused(f"cap: {DAILY_CAP} changes already logged today in {changelog}. adapt.md allows at most "
                      f"{DAILY_CAP} autonomous changes per session (counted per day here). Stop; show the user "
                      "this change with --dry-run instead.")
    front_updates, body_updates = {}, {}
    for k in ("status", "evidence"):
        if getattr(args, k, None) is not None:
            front_updates[k] = getattr(args, k)
    if getattr(args, "last_verified", None):
        front_updates["last_verified"] = today.isoformat() if args.last_verified == "today" else args.last_verified
    for k in BODY_KEYS:
        if getattr(args, k, None) is not None:
            body_updates[k] = getattr(args, k)
    if new_entry:
        front_updates.update({"id": args.id, "kind": args.kind, "connector": args.connector, "target": args.target})
        front_updates.setdefault("last_verified", today.isoformat())
        if args.status not in ("working", "untested"):
            raise Refused("schema: a new entry starts as working (it passed a real run) or untested")
    changed = set(front_updates) | set(body_updates)
    if not changed:
        raise Refused("nothing to change: pass at least one field")
    if changed & {"status", "how", "caveats", "drop"} - {"id"} and not front_updates.get("evidence"):
        raise Refused(f"evidence-required: changing {sorted(changed & {'status', 'how', 'caveats', 'drop'})} needs "
                      "--evidence from this session (adapt.md, 'What may change').")
    ev = front_updates.get("evidence")
    if ev and not HANDLE_RE.search(ev):
        raise Refused(f'evidence: --evidence needs a handle: a URL, a run/dataset ID, or a quoted fragment of 20+ '
                      f'characters. Got: "{ev}". Copy it from the run or the error; do not invent one.')
    for k, allowed in (("status", STATUSES), ("kind", KINDS), ("connector", CONNECTORS)):
        if k in front_updates and front_updates[k] not in allowed:
            raise Refused(f"schema: {k} must be one of {sorted(allowed)}")
    if "last_verified" in front_updates and not DATE_RE.match(front_updates["last_verified"]):
        raise Refused("schema: last_verified must be YYYY-MM-DD or 'today'")
    hit = forbidden_word(" ".join([front_updates.get("target", ""), body_updates.get("how", ""), body_updates.get("caveats", "")]))
    if hit:
        raise Refused(f'invariant: "{hit}" found in the new text. adapt.md forbids sources needing login, CAPTCHA '
                      "solving, or proxies beyond actor defaults. If this is a false positive, tell the user; do not reword and retry.")
    if "drop" in body_updates and current:
        lost = drop_tokens(current["body"].get("drop")) - drop_tokens(body_updates["drop"])
        allowed_loss = {x.strip() for x in (args.allow_drop_removal or [])}
        if lost - allowed_loss:
            raise Refused(f'drop: {sorted(lost - allowed_loss)} are in the current drop list and not in the new one. Keep them, '
                          'or pass --allow-drop-removal "<field>" --reason "<why it no longer applies>"; the removal is logged.')
        if lost and not args.reason:
            raise Refused("drop: --allow-drop-removal needs --reason")

    old = current["text"] if current else "---\n---\nhow: \ncaveats: \ndrop: —\n"
    new = old
    for k in ["id", "kind", "connector", "target", "status", "last_verified", "evidence"]:
        if k in front_updates:
            new = replace_line(new, k, front_updates[k], True)
    for k, v in body_updates.items():
        new = replace_line(new, k, v, False)
    target = ov / "sources" / f"{args.id}.md"
    summary = ", ".join(f"{k}={v}" for k, v in {**front_updates, **body_updates}.items() if k not in ("evidence", "id"))
    if getattr(args, "allow_drop_removal", None):
        summary += f"; DROP REMOVED {args.allow_drop_removal} because {args.reason}"
    log_line = f"{today.isoformat()} | sources/{args.id}.md | {'add' if new_entry else 'set'} {summary} | {ev or '-'} | {args.note or ''}\n"
    diff = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                        f"a/sources/{args.id}.md", f"b/sources/{args.id}.md"))
    if args.dry_run:
        print(diff + f"\nCHANGELOG line:\n{log_line}", end="")
        return 0
    if not writable(ov):
        print(f"overlay {ov} is not writable; propose this change to the user instead:\n{diff}\nCHANGELOG line:\n{log_line}", end="")
        return 3
    check_front, check_body, _ = parse(new)
    tmp_entry = {"front": check_front, "body": check_body, "parse_errors": []}
    errors, _ = validate(tmp_entry, args.id, "overlay", bundled.get(args.id), today)
    errors = [x for x in errors if not (x.startswith("drop list is missing") and args.allow_drop_removal)]
    if errors:
        raise Refused("schema: the resulting entry would be invalid: " + "; ".join(errors))
    write_atomic(target, new)
    with open(changelog, "a", encoding="utf-8") as fh:
        fh.write(log_line)
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
        p.add_argument("--today", help="YYYY-MM-DD, for tests or an untrustworthy clock")
    for name in ("set", "add"):
        p = sub.add_parser(name, help=("change fields of an existing entry (written to the overlay)" if name == "set"
                                       else "add a new entry that passed one real run this session"))
        p.add_argument("id")
        p.add_argument("--status", required=(name == "add"))
        p.add_argument("--last-verified", help="YYYY-MM-DD or 'today'")
        p.add_argument("--evidence", required=(name == "add"), help="must contain a URL, run/dataset ID, or quoted output")
        p.add_argument("--how")
        p.add_argument("--caveats")
        p.add_argument("--drop", help='comma-separated personal fields to drop, e.g. "host.about, review authors"')
        p.add_argument("--note", default="")
        p.add_argument("--today")
        p.add_argument("--dry-run", action="store_true", help="print the diff and CHANGELOG line; write nothing")
        if name == "set":
            p.add_argument("--allow-drop-removal", action="append", metavar="FIELD")
            p.add_argument("--reason")
        else:
            p.add_argument("--kind", required=True)
            p.add_argument("--connector", required=True)
            p.add_argument("--target", required=True)
            p.set_defaults(allow_drop_removal=None, reason=None)
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
