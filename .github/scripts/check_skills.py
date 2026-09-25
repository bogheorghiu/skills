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
REF_RE = re.compile(r"`([A-Za-z0-9_./-]+\.md)(?:\s*§[^`]*)?`")


def parse_frontmatter(text):
    """Parse the small YAML subset skills use: scalars and one nested map level."""
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with '---' frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("frontmatter is not closed with '---'")
    fm, body = text[4:end], text[end + 4:].lstrip("\n")
    data, current = {}, None
    for raw in fm.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r"^(\s*)([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not m:
            raise ValueError(f"unparseable frontmatter line: {raw!r}")
        indent, key, val = m.groups()
        if indent and current is not None:
            data[current][key] = val
            continue
        if indent:
            raise ValueError(f"indented line without a parent map: {raw!r}")
        if val == "":
            data[key], current = {}, key
        else:
            data[key], current = val, None
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
    name = unquote(fm.get("name", "")) if isinstance(fm.get("name"), str) else ""
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
    if "license" not in fm:
        errors.append("missing field: license (gh skill publish warns on it)")
    meta = fm.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        errors.append("metadata must be a map of string keys to string values")
    elif isinstance(meta, dict):
        for k, v in meta.items():
            if not (len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'") and re.fullmatch(r"[\d.]+|true|false|null", v):
                errors.append(f"metadata.{k} = {v} would parse as a non-string; quote it")
    if isinstance(fm.get("allowed-tools"), dict) or str(fm.get("allowed-tools", "")).startswith("["):
        errors.append("allowed-tools must be a space-separated string, not a list")
    leaked = [k for k in meta if k.startswith(INSTALL_PREFIX)] if isinstance(meta, dict) else []
    if leaked:
        errors.append(f"install metadata present: {sorted(leaked)} (run gh skill publish --fix)")
    n = len(body.splitlines())
    if n > 500:
        errors.append(f"SKILL.md body is {n} lines (recommended max 500)")
    for md in sorted(skill_dir.rglob("*.md")):
        for ref in REF_RE.findall(md.read_text(encoding="utf-8")):
            # Only folder-qualified paths are skill files; a bare name such as
            # `CHANGELOG.md` names a file in the user's overlay, not in the skill.
            if "/" not in ref or ref.startswith(("/", "http")) or "*" in ref:
                continue
            if not (skill_dir / ref).is_file():
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
