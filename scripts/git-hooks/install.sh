#!/bin/sh
# Install the tracked git hooks into .git/hooks/.
#
# Run once after cloning the repo, and again whenever a hook file in
# scripts/git-hooks/ is updated (git's hook system doesn't auto-sync).
#
# Usage:
#     bash scripts/git-hooks/install.sh

set -e

ROOT="$(git rev-parse --show-toplevel)"
SRC="$ROOT/scripts/git-hooks"
DST="$ROOT/.git/hooks"

if [ ! -d "$DST" ]; then
    echo "ERROR: $DST does not exist. Are you inside a git repo?"
    exit 1
fi

for hook in pre-commit; do
    if [ -f "$SRC/$hook" ]; then
        cp "$SRC/$hook" "$DST/$hook"
        chmod +x "$DST/$hook"
        echo "Installed: $hook"
    fi
done

echo "Done. Hooks active in $DST/"
