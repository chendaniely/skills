#!/usr/bin/env bash
# Link every skill in this repo into ~/.claude/skills, one symlink per skill,
# so Claude Code picks it up and edits here apply live.
#
# Safe to re-run. Correct links are left alone. Anything else already at a
# target path (a real folder, or a link pointing somewhere else) is reported
# and skipped. Links into this repo whose skill folder is gone are removed.
#
# Usage: ./install.sh   (set CLAUDE_SKILLS_DIR to install somewhere else)
set -euo pipefail
shopt -s nullglob

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
dest="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$dest"

for skill_md in "$repo"/*/SKILL.md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  link="$dest/$name"
  if [ -L "$link" ]; then
    if [ "$(readlink "$link")" = "$src" ]; then
      echo "ok       $name"
    else
      echo "skipped  $name (already links to $(readlink "$link"))"
    fi
  elif [ -e "$link" ]; then
    echo "skipped  $name (a real file or folder is already there)"
  else
    ln -s "$src" "$link"
    echo "linked   $name"
  fi
done

# Remove links into this repo whose skill was renamed or deleted.
for link in "$dest"/*; do
  [ -L "$link" ] || continue
  target="$(readlink "$link")"
  case "$target" in
    "$repo"/*)
      if [ ! -e "$target/SKILL.md" ]; then
        rm "$link"
        echo "removed  $(basename "$link") (no longer a skill in this repo)"
      fi
      ;;
  esac
done
