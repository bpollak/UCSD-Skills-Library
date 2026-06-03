#!/usr/bin/env bash
set -euo pipefail

DEST="${DEST:-$HOME/.agents/skills}"
RAW_BASE_URL="${RAW_BASE_URL:-https://raw.githubusercontent.com/dbalders/UCSD-Skills-Library/main}"
GROUP="${GROUP:-core}"
SKILLS="${SKILLS:-}"

skills_for_group() {
  case "$1" in
    core|built)
      printf '%s\n' "tritonai-feedback"
      ;;
    all)
      printf '%s\n' "tritonai-feedback ucsd-data-classification"
      ;;
    *)
      echo "Unknown skill group: $1" >&2
      return 1
      ;;
  esac
}

skill_files() {
  case "$1" in
    tritonai-feedback)
      printf '%s\n' \
        "skills/tritonai-feedback/SKILL.md"
      ;;
    ucsd-data-classification)
      printf '%s\n' \
        "skills/ucsd-data-classification/SKILL.md" \
        "skills/ucsd-data-classification/references/handling-obligations.md" \
        "skills/ucsd-data-classification/references/protection-levels.md" \
        "skills/ucsd-data-classification/references/sources.md"
      ;;
    *)
      echo "Unknown skill: $1" >&2
      return 1
      ;;
  esac
}

if [[ -z "$SKILLS" ]]; then
  SKILLS="$(skills_for_group "$GROUP")"
fi

RAW_BASE_URL="${RAW_BASE_URL%/}"

mkdir -p "$DEST"

for skill in $SKILLS; do
  rm -rf "$DEST/$skill"

  while IFS= read -r rel_path; do
    target="$DEST/${rel_path#skills/}"
    mkdir -p "$(dirname "$target")"
    curl -fsSL "$RAW_BASE_URL/$rel_path" -o "$target"
  done < <(skill_files "$skill")

  echo "Installed $skill -> $DEST/$skill"
done

echo "UCSD skill install complete."
