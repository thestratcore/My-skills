#!/usr/bin/env bash
# On-demand sync: local MySKILLS is the source of truth; push it to origin.
# Usage: ./sync.sh ["commit message"]
set -euo pipefail
cd "$(dirname "$0")"
git fetch origin --quiet
behind=$(git rev-list --count HEAD..origin/main)
if [ "$behind" -gt 0 ]; then
  # Remote has commits local lacks: archive them, then overwrite (local wins).
  tag="archive/remote-$(date +%Y%m%d-%H%M%S)"
  git tag "$tag" origin/main
  git push origin "$tag"
  echo "Remote had $behind commit(s) not in local; archived as $tag"
fi
git add -A
if ! git diff --cached --quiet; then
  git commit -q -m "${1:-chore(skills): sync local skills $(date +%F)}"
fi
if [ "$behind" -gt 0 ]; then
  git push --force-with-lease=main:origin/main origin main
else
  git push origin main
fi
git status -sb | head -1
