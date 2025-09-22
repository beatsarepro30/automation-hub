#!/usr/bin/env bash
#
# install-bashrc.sh
# Injects repo bashrc into ~/.bashrc safely

set -euo pipefail

TARGET="$HOME/.bashrc"
BACKUP="$HOME/.bashrc.bak"
REPO_BASHRC="$(pwd)/bashrc"

INJECT_LINE="if [ -f \"$REPO_BASHRC\" ]; then source \"$REPO_BASHRC\"; else echo \"[WARN] Repo bashrc not found at $REPO_BASHRC\"; fi"

# 1. Check that the repo bashrc exists
if [ ! -f "$REPO_BASHRC" ]; then
    echo "[ERROR] Repo bashrc not found at $REPO_BASHRC"
    exit 1
fi

# 2. Make a backup if it doesn’t exist yet
if [ ! -f "$BACKUP" ]; then
    cp "$TARGET" "$BACKUP"
    echo "[INFO] Backup created at $BACKUP"
fi

# 3. Add inject line if not already present
if grep -Fxq "$INJECT_LINE" "$TARGET"; then
    echo "[INFO] Already installed. Nothing to do."
else
    echo "" >> "$TARGET"
    echo "# >>> custom repo bashrc >>>" >> "$TARGET"
    echo "$INJECT_LINE" >> "$TARGET"
    echo "# <<< custom repo bashrc <<<" >> "$TARGET"
    echo "[INFO] Installed successfully."
fi
