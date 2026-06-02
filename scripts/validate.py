#!/usr/bin/env python3
"""Structural + catalog validation for the UCSD Skills Library.

Checks (hard failures unless noted):
  - ideas.json is valid JSON and matches schema/ideas.schema.json
  - every skills/<name>/ has a SKILL.md with frontmatter `name` (== folder) + `description`
  - built skills are reflected in the catalog, and `done` catalog entries have folders
  - trigger collisions across skill descriptions (advisory warning)

Run locally:  python3 scripts/validate.py
Optional deps for full coverage:  pip install pyyaml jsonschema
Folders under skills/ starting with "_" (e.g. _template) are ignored.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []
warnings: list[str] = []


def err(m: str) -> None:
    errors.append(m)


def warn(m: str) -> None:
    warnings.append(m)


# --- 1. ideas.json: parse + schema ------------------------------------------
ideas: list = []
ideas_path = ROOT / "ideas.json"
try:
    ideas = json.loads(ideas_path.read_text())
except Exception as e:  # noqa: BLE001
    err(f"ideas.json: invalid JSON ({e})")

try:
    import jsonschema  # type: ignore

    schema = json.loads((ROOT / "schema" / "ideas.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for e in sorted(validator.iter_errors(ideas), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in e.path) or "(root)"
        err(f"ideas.json[{loc}]: {e.message}")
except ImportError:
    warn("jsonschema not installed - skipping schema validation (pip install jsonschema)")
except Exception as e:  # noqa: BLE001
    err(f"ideas.json: schema validation failed ({e})")

catalog = {e["name"]: e for e in ideas if isinstance(e, dict) and "name" in e}


# --- 2. frontmatter parsing -------------------------------------------------
def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    body = parts[1]
    try:
        import yaml  # type: ignore

        return yaml.safe_load(body) or {}
    except ImportError:
        data = {}
        for line in body.splitlines():
            m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
            if m:
                data[m.group(1)] = m.group(2).strip().strip("\"'")
        return data


# --- 3. each skill folder ---------------------------------------------------
descriptions: dict[str, str] = {}
skills_dir = ROOT / "skills"
for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
    if d.name.startswith("_"):
        continue  # template / internal
    skill_md = d / "SKILL.md"
    if not skill_md.exists():
        err(f"skills/{d.name}: missing SKILL.md")
        continue
    fm = parse_frontmatter(skill_md.read_text())
    if not fm:
        err(f"skills/{d.name}/SKILL.md: missing or unparseable YAML frontmatter")
        continue
    name, desc = fm.get("name"), fm.get("description")
    if not name:
        err(f"skills/{d.name}/SKILL.md: frontmatter missing 'name'")
    elif name != d.name:
        err(f"skills/{d.name}/SKILL.md: name '{name}' must match folder '{d.name}'")
    if not desc:
        err(f"skills/{d.name}/SKILL.md: frontmatter missing 'description'")
    else:
        descriptions[d.name] = desc
    if name and name not in catalog:
        warn(f"skills/{d.name}: no matching entry in ideas.json")


# --- 4. catalog -> folder consistency ---------------------------------------
for e in ideas:
    if not isinstance(e, dict):
        continue
    name = e.get("name", "")
    folder = skills_dir / name
    links = e.get("links") or []
    links_to_skill = any(str(l.get("url", "")).startswith("skills/") for l in links)
    if e.get("status") == "done" and not folder.exists():
        err(f"ideas.json: '{name}' is status=done but skills/{name}/ is missing")
    if links_to_skill and not folder.exists():
        err(f"ideas.json: '{name}' links to a skill but skills/{name}/ is missing")


# --- 5. trigger-collision (advisory) ----------------------------------------
def triggers(desc: str) -> set[str]:
    out = set(re.findall(r"/[a-z0-9][a-z0-9-]+", desc.lower()))  # slash-commands
    out |= {q.strip().lower() for q in re.findall(r'"([^"]{3,})"', desc)}  # quoted phrases
    return out


names = list(descriptions)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        shared = triggers(descriptions[names[i]]) & triggers(descriptions[names[j]])
        if shared:
            warn(
                f"trigger overlap between '{names[i]}' and '{names[j]}': "
                + ", ".join(sorted(shared))
            )


# --- report -----------------------------------------------------------------
for w in warnings:
    print(f"::warning:: {w}" if "--ci" in sys.argv else f"WARN  {w}")
for e in errors:
    print(f"::error:: {e}" if "--ci" in sys.argv else f"ERROR {e}")

if errors:
    print(f"\nvalidate: FAILED with {len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1)
print(f"validate: OK ({len(warnings)} warning(s))")
