#!/usr/bin/env bash
#
# bashrc-utils.sh
# Reusable functions for safely updating ~/.bashrc with backups

set -euo pipefail

TARGET="${HOME}/.bashrc"
BACKUP="${HOME}/.bashrc.bak"

# Backup ~/.bashrc if different
backup_bashrc() {
    if [[ -f "$TARGET" ]]; then
        if [[ ! -f "$BACKUP" ]] || ! cmp -s "$TARGET" "$BACKUP"; then
            cp "$TARGET" "$BACKUP" || return 1
            echo "[INFO] Backup of ~/.bashrc created/updated at $BACKUP"
        else
            echo "[INFO] No changes detected — backup not updated"
        fi
    else
        echo "[WARN] No ~/.bashrc found to back up"
        return 1
    fi
}

# Inject a line into ~/.bashrc (if not already present)
inject_bashrc_line() {
    local line="$1"
    local tag="${2:-custom}"  # optional tag for clarity

    # Backup ~/.bashrc (only if different)
    backup_bashrc || return 1

    if grep -Fxq "$line" "$TARGET" 2>/dev/null; then
        echo "[INFO] Already present in $TARGET: $line"
        return 0
    fi
    
    {
        echo ""
        echo "# >>> injected by $tag >>>"
        echo "$line"
        echo "# <<< injected by $tag <<<"
    } >> "$TARGET" || return 1
    
    echo "[INFO] Added line to $TARGET: $line"
}
