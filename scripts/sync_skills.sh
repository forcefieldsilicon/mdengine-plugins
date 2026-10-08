#!/usr/bin/env bash
# sync_skills.sh: keep the root skills/ mirror identical to plugins/mdengine/skills/.
#
# Why the mirror exists: Claude Science imports skills from a GitHub repo only in
# the layout skills/<name>/SKILL.md at the repo root (Settings > Skills > Add skill >
# Import from GitHub). The Claude Code plugin keeps them at plugins/mdengine/skills/.
# plugins/mdengine/skills/ is the source of truth. Edit there, then run this script.
#
# Usage:
#   bash scripts/sync_skills.sh          copy every plugins/mdengine/skills/<name>/ to skills/<name>/
#   bash scripts/sync_skills.sh --check  exit 1 and print the differing paths if the two trees differ
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="plugins/mdengine/skills"
DST="skills"
cd "$ROOT"

if [ "${1:-}" = "--check" ]; then
  if out="$(diff -r "$SRC" "$DST" 2>&1)"; then
    echo "skills/ matches $SRC"
    exit 0
  fi
  echo "skills/ differs from $SRC:" >&2
  echo "$out" >&2
  exit 1
fi

if [ -n "${1:-}" ]; then
  echo "usage: bash scripts/sync_skills.sh [--check]" >&2
  exit 2
fi

mkdir -p "$DST"
for dir in "$SRC"/*/; do
  name="$(basename "$dir")"
  rsync -a --delete "$SRC/$name/" "$DST/$name/"
  echo "synced $DST/$name"
done
