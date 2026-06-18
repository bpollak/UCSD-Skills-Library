#!/usr/bin/env python3
"""Validate the UCSD skills catalog and skill folders."""

from __future__ import annotations

import json
import argparse
import re
import sys
from pathlib import Path
from typing import Any

from build_catalog import build_catalog, configure_root as configure_catalog_root, render_catalog


ROOT = Path(__file__).resolve().parents[1]
IDEAS_PATH = ROOT / "ideas.json"
CATEGORIES_PATH = ROOT / "categories.json"
SCHEMA_PATH = ROOT / "schema" / "ideas.schema.json"
SKILLS_DIR = ROOT / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VALID_STATUSES = {"planned", "idea", "in-progress", "review", "done", "built"}
VALID_PUBLICATION_STATUSES = {"draft", "ready", "published", "archived"}
VALID_TIERS = {"core", "verified", "experimental"}
BUILT_STATUSES = {"done", "built"}
REQUIRED_IDEA_FIELDS = {
    "id",
    "name",
    "title",
    "description",
    "category",
    "status",
    "publicationStatus",
    "tier",
    "owner",
    "updated",
    "checklist",
    "links",
}
REQUIRED_CHECKLIST_FIELDS = {"definition", "skillDraft", "references", "reviewed", "published"}
REQUIRED_CATEGORY_FIELDS = {"id", "name", "description", "examples"}


def configure_root(root: Path) -> None:
    global ROOT, IDEAS_PATH, CATEGORIES_PATH, SCHEMA_PATH, SKILLS_DIR

    ROOT = root.resolve()
    IDEAS_PATH = ROOT / "ideas.json"
    CATEGORIES_PATH = ROOT / "categories.json"
    SCHEMA_PATH = ROOT / "schema" / "ideas.schema.json"
    SKILLS_DIR = ROOT / "skills"
    configure_catalog_root(ROOT)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ci", action="store_true", help="Emit GitHub Actions annotations")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root to validate")
    return parser.parse_args()


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        errors.append(f"Missing required file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        errors.append(
            f"{path.relative_to(ROOT)} is not valid JSON: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        )
    return None


def parse_frontmatter(path: Path, errors: list[str]) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        errors.append(f"{path.relative_to(ROOT)} must start with YAML frontmatter")
        return {}

    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{path.relative_to(ROOT)} has unterminated YAML frontmatter")
        return {}

    body = parts[1]
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(body) or {}
        if not isinstance(parsed, dict):
            errors.append(f"{path.relative_to(ROOT)} frontmatter must be a mapping")
            return {}
        return {str(key): str(value) for key, value in parsed.items() if value is not None}
    except ImportError:
        data: dict[str, str] = {}
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or line[:1].isspace():
                continue
            if ":" not in line:
                errors.append(f"{path.relative_to(ROOT)} frontmatter line is not key/value: {line}")
                continue
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip("\"'")
        return data


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


def validate_schema_file(errors: list[str]) -> None:
    schema = load_json(SCHEMA_PATH, errors)
    if schema is None:
        return
    if schema.get("type") != "array":
        errors.append("schema/ideas.schema.json must describe an array catalog")


def validate_categories(categories: Any, errors: list[str]) -> set[str]:
    if not isinstance(categories, list):
        errors.append("categories.json must contain a JSON array")
        return set()

    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for index, entry in enumerate(categories):
        label = f"categories.json[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue

        missing = sorted(REQUIRED_CATEGORY_FIELDS - set(entry))
        if missing:
            errors.append(f"{label} is missing required field(s): {', '.join(missing)}")

        category_id = entry.get("id")
        name = entry.get("name")

        if not isinstance(category_id, str) or not category_id:
            errors.append(f"{label}.id must be a non-empty string")
        elif not NAME_RE.fullmatch(category_id):
            errors.append(f"{label}.id must use lowercase letters, digits, and hyphens: {category_id}")
        elif category_id in seen_ids:
            errors.append(f"{label}.id is duplicated: {category_id}")
        else:
            seen_ids.add(category_id)

        if not isinstance(name, str) or not name.strip():
            errors.append(f"{label}.name must be a non-empty string")
        elif name in seen_names:
            errors.append(f"{label}.name is duplicated: {name}")
        else:
            seen_names.add(name)

        description = entry.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{label}.description must be a non-empty string")

        examples = entry.get("examples")
        if not isinstance(examples, list) or not examples:
            errors.append(f"{label}.examples must be a non-empty array")
        elif not all(isinstance(example, str) and example.strip() for example in examples):
            errors.append(f"{label}.examples must contain only non-empty strings")

    return seen_names


def validate_schema(ideas: Any, errors: list[str], warnings: list[str]) -> None:
    try:
        import jsonschema  # type: ignore

        schema = load_json(SCHEMA_PATH, errors)
        if schema is None:
            return
        validator = jsonschema.Draft202012Validator(schema)
        for error in sorted(validator.iter_errors(ideas), key=lambda item: list(item.path)):
            location = "/".join(str(part) for part in error.path) or "(root)"
            errors.append(f"ideas.json[{location}]: {error.message}")
    except ImportError:
        warnings.append("jsonschema not installed - skipping schema validation (pip install jsonschema)")


def validate_links(label: str, links: Any, errors: list[str]) -> bool:
    if not isinstance(links, list):
        errors.append(f"{label}.links must be an array")
        return False

    links_to_skill = False
    for link_index, link in enumerate(links):
        link_label = f"{label}.links[{link_index}]"
        if not isinstance(link, dict):
            errors.append(f"{link_label} must be an object")
            continue
        if set(link) - {"label", "url"}:
            extras = ", ".join(sorted(set(link) - {"label", "url"}))
            errors.append(f"{link_label} has unsupported field(s): {extras}")
        for field in ("label", "url"):
            if not isinstance(link.get(field), str) or not link.get(field, "").strip():
                errors.append(f"{link_label}.{field} must be a non-empty string")
        url = str(link.get("url", ""))
        links_to_skill = links_to_skill or url.startswith("skills/")

    return links_to_skill


def validate_ideas(ideas: Any, category_names: set[str], errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(ideas, list):
        errors.append("ideas.json must contain a JSON array")
        return {}

    by_name: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for index, entry in enumerate(ideas):
        label = f"ideas.json[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue

        missing = sorted(REQUIRED_IDEA_FIELDS - set(entry))
        if missing:
            errors.append(f"{label} is missing required field(s): {', '.join(missing)}")

        extra = sorted(set(entry) - REQUIRED_IDEA_FIELDS)
        if extra:
            errors.append(f"{label} has unsupported field(s): {', '.join(extra)}")

        idea_id = entry.get("id")
        name = entry.get("name")

        if not isinstance(idea_id, str) or not idea_id:
            errors.append(f"{label}.id must be a non-empty string")
        elif not NAME_RE.fullmatch(idea_id):
            errors.append(f"{label}.id must use lowercase letters, digits, and hyphens: {idea_id}")
        elif idea_id in seen_ids:
            errors.append(f"{label}.id is duplicated: {idea_id}")
        else:
            seen_ids.add(idea_id)

        if not isinstance(name, str) or not name:
            errors.append(f"{label}.name must be a non-empty string")
        elif not NAME_RE.fullmatch(name):
            errors.append(f"{label}.name must use lowercase letters, digits, and hyphens: {name}")
        elif name in seen_names:
            errors.append(f"{label}.name is duplicated: {name}")
        else:
            seen_names.add(name)
            by_name[name] = entry

        if isinstance(idea_id, str) and isinstance(name, str) and idea_id != name:
            errors.append(f"{label}.id and .name must match: {idea_id} != {name}")

        for field in ("title", "description", "owner"):
            if not isinstance(entry.get(field), str) or not entry.get(field, "").strip():
                errors.append(f"{label}.{field} must be a non-empty string")

        category = entry.get("category")
        if not isinstance(category, str) or not category.strip():
            errors.append(f"{label}.category must be a non-empty string")
        elif category_names and category not in category_names:
            errors.append(f"{label}.category must match a category in categories.json: {category}")

        status = entry.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{label}.status must be one of {', '.join(sorted(VALID_STATUSES))}: {status}")

        publication_status = entry.get("publicationStatus")
        if publication_status not in VALID_PUBLICATION_STATUSES:
            errors.append(
                f"{label}.publicationStatus must be one of "
                f"{', '.join(sorted(VALID_PUBLICATION_STATUSES))}: {publication_status}"
            )

        tier = entry.get("tier")
        if tier not in VALID_TIERS:
            errors.append(f"{label}.tier must be one of {', '.join(sorted(VALID_TIERS))}: {tier}")

        updated = entry.get("updated")
        if not isinstance(updated, str) or not DATE_RE.fullmatch(updated):
            errors.append(f"{label}.updated must use YYYY-MM-DD format")

        checklist = entry.get("checklist")
        if not isinstance(checklist, dict):
            errors.append(f"{label}.checklist must be an object")
        else:
            missing_checklist = sorted(REQUIRED_CHECKLIST_FIELDS - set(checklist))
            if missing_checklist:
                errors.append(
                    f"{label}.checklist is missing required field(s): {', '.join(missing_checklist)}"
                )
            extra_checklist = sorted(set(checklist) - REQUIRED_CHECKLIST_FIELDS)
            if extra_checklist:
                errors.append(
                    f"{label}.checklist has unsupported field(s): {', '.join(extra_checklist)}"
                )
            for key, value in checklist.items():
                if not isinstance(value, bool):
                    errors.append(f"{label}.checklist.{key} must be boolean")

        links_to_skill = validate_links(label, entry.get("links"), errors)
        folder = SKILLS_DIR / str(name)
        if status in BUILT_STATUSES and not folder.exists():
            errors.append(f"{label} is status={status} but skills/{name}/ is missing")
        if links_to_skill and not folder.exists():
            errors.append(f"{label} links to a skill but skills/{name}/ is missing")

    return by_name


def validate_skill_folders(catalog: dict[str, dict[str, Any]], errors: list[str]) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    for directory in skill_dirs():
        name = directory.name
        if not NAME_RE.fullmatch(name):
            errors.append(f"skills/{name} must use lowercase letters, digits, and hyphens")

        skill_md = directory / "SKILL.md"
        frontmatter = parse_frontmatter(skill_md, errors)
        frontmatter_name = frontmatter.get("name")
        description = frontmatter.get("description")

        if not frontmatter_name:
            errors.append(f"skills/{name}/SKILL.md frontmatter missing 'name'")
        elif frontmatter_name != name:
            errors.append(
                f"skills/{name}/SKILL.md frontmatter name '{frontmatter_name}' must match folder '{name}'"
            )

        if not description:
            errors.append(f"skills/{name}/SKILL.md frontmatter missing 'description'")
        else:
            descriptions[name] = description

        if name not in catalog:
            errors.append(f"skills/{name} has no matching entry in the generated catalog")

    return descriptions


def trigger_tokens(description: str) -> set[str]:
    tokens = set(re.findall(r"/[a-z0-9][a-z0-9-]+", description.lower()))
    tokens |= {phrase.strip().lower() for phrase in re.findall(r'"([^"]{3,})"', description)}
    return tokens


def validate_trigger_collisions(descriptions: dict[str, str], warnings: list[str]) -> None:
    names = list(descriptions)
    for left_index, left_name in enumerate(names):
        for right_name in names[left_index + 1 :]:
            shared = trigger_tokens(descriptions[left_name]) & trigger_tokens(descriptions[right_name])
            if shared:
                warnings.append(
                    f"trigger overlap between '{left_name}' and '{right_name}': "
                    + ", ".join(sorted(shared))
                )


def main() -> int:
    args = parse_args()
    configure_root(args.root)

    errors: list[str] = []
    warnings: list[str] = []

    validate_schema_file(errors)
    categories = load_json(CATEGORIES_PATH, errors)

    category_names = validate_categories(categories, errors) if categories is not None else set()

    try:
        ideas = build_catalog()
    except Exception as exc:
        errors.append(f"generated catalog failed: {exc}")
        ideas = []

    validate_schema(ideas, errors, warnings)
    catalog = validate_ideas(ideas, category_names, errors)
    descriptions = validate_skill_folders(catalog, errors)
    validate_trigger_collisions(descriptions, warnings)

    checked_in_ideas = load_json(IDEAS_PATH, errors)
    if checked_in_ideas is not None:
        validate_schema(checked_in_ideas, errors, warnings)
        try:
            if IDEAS_PATH.read_text(encoding="utf-8") != render_catalog(ideas):
                warnings.append("ideas.json is generated and stale; run python3 scripts/build_catalog.py")
        except OSError as exc:
            errors.append(f"Could not read ideas.json: {exc}")

    ci = args.ci
    for warning in warnings:
        print(f"::warning:: {warning}" if ci else f"WARN  {warning}")
    for error in errors:
        print(f"::error:: {error}" if ci else f"ERROR {error}")

    if errors:
        print(f"\nvalidate: FAILED with {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    print(f"validate: OK ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
