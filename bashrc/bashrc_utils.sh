#!/usr/bin/env bash
#
# bashrc-utils.sh
# Reusable functions for safely updating ~/.bashrc with backups

set -euo pipefail

TARGET="$HOME/.bashrc"
BACKUP="$HOME/.bashrc.bak"

# Backup ~/.bashrc if different
backup_bashrc() {
    if [ -f "$TARGET" ]; then
        if [ ! -f "$BACKUP" ] || ! cmp -s "$TARGET" "$BACKUP"; then
            cp "$TARGET" "$BACKUP"
            echo "[INFO] Backup of ~/.bashrc created/updated at $BACKUP"
        else
            echo "[INFO] No changes detected — backup not updated"
        fi
    else
        echo "[WARN] No ~/.bashrc found to back up"
    fi
}

# Inject a line into ~/.bashrc (if not already present)
inject_bashrc_line() {
    # Backup ~/.bashrc (only if different)
    backup_bashrc
    local line="$1"
    local tag="${2:-custom}"  # optional tag for clarity

    if grep -Fxq "$line" "$TARGET" 2>/dev/null; then
        echo "[INFO] Already present in $TARGET: $line"
    else
        {
            echo ""
            echo "# >>> injected by $tag >>>"
            echo "$line"
            echo "# <<< injected by $tag <<<"
        } >> "$TARGET"
        echo "[INFO] Added line to $TARGET: $line"
    fi
}
