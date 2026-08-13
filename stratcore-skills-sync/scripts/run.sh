#!/usr/bin/env bash
set -euo pipefail

SOURCE_SCRIPT="/Users/admin/Documents/Obsidian-Stratcore/MySKILLS/sync_skills.py"

if [[ ! -f "$SOURCE_SCRIPT" ]]; then
  printf 'ERROR: persistent sync script not found: %s\n' "$SOURCE_SCRIPT" >&2
  exit 2
fi

exec python3 "$SOURCE_SCRIPT" "$@"
