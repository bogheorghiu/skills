#!/usr/bin/env python3
"""Structural lint for every skill under skills/*/ (stdlib only).

Checks the Agent Skills spec (agentskills.io/specification) plus the extra
checks `gh skill publish` runs, so a PR fails here instead of at publish time:
name rules, description/compatibility length, metadata values as strings,
allowed-tools as a string, no install metadata, license present, body <= 500
lines. Also checks that every backticked relative `*.md` path a skill file
mentions resolves inside that skill folder -- a dangling reference is a
silent failure for the agent that follows it.

Usage: python3 .github/scripts/check_skills.py [repo_root]   (exit 1 on any error)
"""
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# `gh skill publish` treats metadata keys prefixed "github-" as install metadata
# written by `gh skill install` (cli/cli pkg/cmd/skills/publish, findGitHubMetadataKeys).
INSTALL_PREFIX = "github-"
# Folder-qualified file references, backticked or plain ("see patterns/lodging.md §5").
# A bare name such as CHANGELOG.md names a file in the user's overlay, not in the skill.
REF_RE = re.compile(r"(?<![\w/.-])((?:\.{1,2}/)*(?:patterns|reference|references|sources|scripts|assets)/[A-Za-z0-9_./-]*?[A-Za-z0-9_-]\.(?:md|py|js|json|txt))(?![A-Za-z0-9_])")
# Scalars YAML would load as something other than a string (bools incl. YAML 1.1's
# yes/no/on/off, null, numbers, dates); `gh skill publish` expects string values.
YAML_NON_STRING = re.compile(r"^(?:|~|null|true|false|yes|no|on|off|y|n|[-+]?[\d_]+|0x[\da-f_]+|0o[0-7_]+|[-+]?[\d_]*\.[\d_]+(?:e[-+]?\d+)?|[-+]?\.inf|\.nan|\d{4}-\d{2}-\d{2}.*)$", re.I)


def strip_comment(v):
    """Drop a trailing ' # comment', keeping a quoted scalar's quotes."""
    if v[:1] and v[:1] in "\"'":
        close = v.find(v[0], 1)
        return v[:close + 1] if close > 0 else v
    return re.split(r"\s+#", v, maxsplit=1)[0].rstrip()


def parse_frontmatter(text):
    """Parse the YAML subset skills use: scalars, block scalars (| and >), one nested
    map level (metadata), and block lists. Lists come back as Python lists."""
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with '---' frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("frontmatter is not closed with '---'")
    lines, body = text[4:end].splitlines(), text[end + 4:].lstrip("\n")
    data, i = {}, 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not m or raw[0] in " \t":
            raise ValueError(f"unparseable frontmatter line: {raw!r}")
        key, val = m.group(1), strip_comment(m.group(2))
        block = []
        while i < len(lines) and (not lines[i].strip() or lines[i][0] in " \t"):
            block.append(lines[i])
            i += 1
        if val in ("|", "|-", "|+", ">", ">-", ">+"):
            parts = [b.strip() for b in block]
            data[key] = ("\n" if val[0] == "|" else " ").join(parts).strip()
        elif val == "" and block and block[0].strip().startswith("- "):
            data[key] = [strip_comment(b.strip()[2:]) for b in block if b.strip()]
        elif val == "":
            sub = {}
            for b in block:
                if not b.strip():
                    continue
                mm = re.match(r"^\s+([A-Za-z0-9_.-]+):\s*(.*)$", b)
                if not mm:
                    raise ValueError(f"unparseable nested line under {key}: {b!r}")
                sub[mm.group(1)] = strip_comment(mm.group(2))
            data[key] = sub
        else:
            # A plain scalar may continue on indented lines; YAML folds them with spaces.
            data[key] = " ".join([val] + [b.strip() for b in block if b.strip()])
    return data, body


def unquote(v):
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'" else v


def check_skill(skill_dir):
    errors = []
    path = skill_dir / "SKILL.md"
    try:
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    except ValueError as e:
        return [f"{path}: {e}"]
    name = unquote(strip_comment(fm["name"])) if isinstance(fm.get("name"), str) else ""
    if not name:
        errors.append("missing required field: name")
    else:
        if len(name) > 64 or not NAME_RE.match(name):
            errors.append(f"name {name!r} breaks the naming rule (a-z0-9, single hyphens, <=64)")
        if name != skill_dir.name:
            errors.append(f"name {name!r} does not match directory {skill_dir.name!r}")
    desc = fm.get("description")
    if not isinstance(desc, str) or not unquote(desc).strip():
        errors.append("missing required field: description")
    elif len(unquote(desc)) > 1024:
        errors.append(f"description is {len(unquote(desc))} chars (max 1024)")
    comp = fm.get("compatibility")
    if isinstance(comp, str) and not 1 <= len(unquote(comp)) <= 500:
        errors.append("compatibility must be 1-500 chars")
    if not isinstance(fm.get("license"), str) or not unquote(fm["license"]).strip():
        errors.append("missing field: license (gh skill publish warns on it)")
    meta = fm.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        errors.append("metadata must be a map of string keys to string values")
    elif isinstance(meta, dict):
        for k, v in meta.items():
            quoted = len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]
            if not quoted and YAML_NON_STRING.match(v):
                errors.append(f"metadata.{k} = {v!r} would not load as a string in YAML; quote it")
    if isinstance(fm.get("allowed-tools"), (dict, list)) or str(fm.get("allowed-tools", "")).startswith("["):
        errors.append("allowed-tools must be a space-separated string, not a list")
    leaked = [k for k in meta if k.startswith(INSTALL_PREFIX)] if isinstance(meta, dict) else []
    if leaked:
        errors.append(f"install metadata present: {sorted(leaked)} (run gh skill publish --fix)")
    n = len(body.splitlines())
    if n > 500:
        errors.append(f"SKILL.md body is {n} lines (recommended max 500)")
    root = skill_dir.resolve()
    for md in sorted(skill_dir.rglob("*.md")):
        for ref in sorted(set(REF_RE.findall(md.read_text(encoding="utf-8")))):
            target = (skill_dir / ref).resolve()
            if root not in target.parents:
                errors.append(f"{md.relative_to(skill_dir)}: reference `{ref}` points outside the skill folder")
            elif not target.is_file():
                errors.append(f"{md.relative_to(skill_dir)}: reference `{ref}` does not resolve inside the skill")
    return [f"{skill_dir.name}: {e}" for e in errors]


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    skills = sorted(p.parent for p in root.glob("skills/*/SKILL.md"))
    if not skills:
        print("no skills found under skills/*/SKILL.md", file=sys.stderr)
        return 1
    errors = [e for s in skills for e in check_skill(s)]
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    print(f"checked {len(skills)} skill(s): {', '.join(s.name for s in skills)}; {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
