#!/usr/bin/env bash
set -euo pipefail

DEST="${DEST:-$HOME/.agents/skills}"
RAW_BASE_URL="${RAW_BASE_URL:-https://raw.githubusercontent.com/bpollak/UCSD-Skills-Library/main}"
GROUP="${GROUP:-core}"
SKILLS="${SKILLS:-}"

skills_for_group() {
  case "$1" in
    core|built)
      printf '%s\n' "tritonai-feedback"
      ;;
    all)
      printf '%s\n' \
        "tritonai-feedback" \
        "ucsd-branding" \
        "ucsd-data-classification" \
        "ucsd-memory" \
        "ucsd-memory-create" \
        "ucsd-msgraph-calendar"
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
    ucsd-branding)
      printf '%s\n' \
        "skills/ucsd-branding/SKILL.md" \
        "skills/ucsd-branding/references/decorator5-chrome.md"
      ;;
    ucsd-data-classification)
      printf '%s\n' \
        "skills/ucsd-data-classification/SKILL.md" \
        "skills/ucsd-data-classification/references/handling-obligations.md" \
        "skills/ucsd-data-classification/references/protection-levels.md" \
        "skills/ucsd-data-classification/references/sources.md"
      ;;
    ucsd-memory)
      printf '%s\n' \
        "skills/ucsd-memory/SKILL.md"
      ;;
    ucsd-memory-create)
      printf '%s\n' \
        "skills/ucsd-memory-create/SKILL.md" \
        "skills/ucsd-memory-create/references/scheduler-adapters.md" \
        "skills/ucsd-memory-create/assets/prompts/daily-sync.md" \
        "skills/ucsd-memory-create/assets/prompts/weekly-cleanup.md"
      ;;
    ucsd-msgraph-calendar)
      printf '%s\n' \
        "skills/ucsd-msgraph-calendar/SKILL.md" \
        "skills/ucsd-msgraph-calendar/references/azure-app-setup.md" \
        "skills/ucsd-msgraph-calendar/scripts/graph_auth.py"
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
