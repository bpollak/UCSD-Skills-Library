#!/usr/bin/env python3
"""Build ideas.json from skill frontmatter."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
IDEAS_PATH = ROOT / "ideas.json"
SKILLS_DIR = ROOT / "skills"

CATALOG_FIELDS = {
    "title",
    "description",
    "category",
    "status",
    "publicationStatus",
    "tier",
    "owner",
    "updated",
}


def configure_root(root: Path) -> None:
    global ROOT, IDEAS_PATH, SKILLS_DIR

    ROOT = root.resolve()
    IDEAS_PATH = ROOT / "ideas.json"
    SKILLS_DIR = ROOT / "skills"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root")
    parser.add_argument("--check", action="store_true", help="Fail if ideas.json is stale")
    parser.add_argument("--print", action="store_true", help="Print generated catalog to stdout")
    return parser.parse_args()


def load_frontmatter(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required: pip install pyyaml") from exc

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path.relative_to(ROOT)} must start with YAML frontmatter")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path.relative_to(ROOT)} has unterminated YAML frontmatter")

    parsed = yaml.safe_load(parts[1]) or {}
    if not isinstance(parsed, dict):
        raise ValueError(f"{path.relative_to(ROOT)} frontmatter must be a mapping")

    return parsed


def skill_dirs() -> list[Path]:
    if not SKILLS_DIR.exists():
        return []
    return sorted(
        path
        for path in SKILLS_DIR.iterdir()
        if path.is_dir()
        and not path.name.startswith(".")
        and not path.name.startswith("_")
        and (path / "SKILL.md").exists()
    )


def normalize_text(value: Any) -> str:
    return " ".join(str(value).split())


def titleize_path_stem(path: Path) -> str:
    text = path.stem.replace("_", "-")
    text = re.sub(r"(?<=\D)(\d)", r" \1", text)
    words = re.split(r"-+", text)
    specials = {
        "api": "API",
        "ad": "AD",
        "ai": "AI",
        "is": "IS",
        "msgraph": "MSGraph",
        "oauth": "OAuth",
        "ucsd": "UCSD",
    }
    return " ".join(specials.get(word.lower(), word.capitalize()) for word in words if word)


def files_under(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.rglob("*") if path.is_file())


def links_for_skill(skill_dir: Path) -> list[dict[str, str]]:
    links = [
        {
            "label": "Skill",
            "url": f"skills/{skill_dir.name}/SKILL.md",
        }
    ]

    for reference in files_under(skill_dir / "references"):
        label = f"Reference: {titleize_path_stem(reference)}"
        links.append({"label": label, "url": reference.relative_to(ROOT).as_posix()})

    scripts = files_under(skill_dir / "scripts")
    for script in scripts:
        label = "Script" if len(scripts) == 1 else f"Script: {script.name}"
        links.append({"label": label, "url": script.relative_to(ROOT).as_posix()})

    return links


def checklist_for_skill(skill_dir: Path, catalog: dict[str, Any]) -> dict[str, bool]:
    status = str(catalog.get("status", ""))
    tier = str(catalog.get("tier", ""))
    publication_status = str(catalog.get("publicationStatus", ""))
    has_references = bool(files_under(skill_dir / "references"))

    return {
        "definition": True,
        "skillDraft": True,
        "references": has_references,
        "reviewed": bool(catalog.get("reviewed", status == "done" and tier in {"core", "verified"})),
        "published": bool(catalog.get("published", publication_status == "published")),
    }


def catalog_entry(skill_dir: Path) -> dict[str, Any]:
    frontmatter = load_frontmatter(skill_dir / "SKILL.md")
    name = str(frontmatter.get("name", ""))
    if name != skill_dir.name:
        raise ValueError(f"skills/{skill_dir.name}/SKILL.md frontmatter name must match folder")

    catalog = frontmatter.get("catalog")
    if not isinstance(catalog, dict):
        raise ValueError(f"skills/{skill_dir.name}/SKILL.md frontmatter missing catalog mapping")

    missing = sorted(CATALOG_FIELDS - set(catalog))
    if missing:
        raise ValueError(
            f"skills/{skill_dir.name}/SKILL.md catalog missing field(s): {', '.join(missing)}"
        )

    description = catalog.get("description") or frontmatter.get("description")

    return {
        "id": name,
        "name": name,
        "title": normalize_text(catalog["title"]),
        "description": normalize_text(description),
        "category": normalize_text(catalog["category"]),
        "status": normalize_text(catalog["status"]),
        "publicationStatus": normalize_text(catalog["publicationStatus"]),
        "tier": normalize_text(catalog["tier"]),
        "owner": normalize_text(catalog["owner"]),
        "updated": normalize_text(catalog["updated"]),
        "checklist": checklist_for_skill(skill_dir, catalog),
        "links": links_for_skill(skill_dir),
    }


def build_catalog() -> list[dict[str, Any]]:
    return sorted((catalog_entry(directory) for directory in skill_dirs()), key=lambda entry: entry["id"])


def render_catalog(catalog: list[dict[str, Any]]) -> str:
    return json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    args = parse_args()
    configure_root(args.root)

    try:
        output = render_catalog(build_catalog())
    except Exception as exc:
        print(f"build-catalog: ERROR {exc}", file=sys.stderr)
        return 1

    if args.print:
        print(output, end="")
        return 0

    if args.check:
        try:
            current = IDEAS_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            print("build-catalog: ERROR ideas.json is missing", file=sys.stderr)
            return 1
        if current != output:
            print("build-catalog: ERROR ideas.json is stale; run python3 scripts/build_catalog.py")
            return 1
        print("build-catalog: OK")
        return 0

    IDEAS_PATH.write_text(output, encoding="utf-8")
    print(f"build-catalog: wrote {IDEAS_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
