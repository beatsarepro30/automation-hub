#!/bin/bash
set -euo pipefail

# ----------------------------
# LOCKFILE (prevent overlapping runs)
# ----------------------------
LOCKFILE="/tmp/sync.lock"
if [ -f "$LOCKFILE" ] && kill -0 "$(cat "$LOCKFILE")" 2>/dev/null; then
    echo "Another sync is running. Exiting."
    exit 1
fi
echo $$ > "$LOCKFILE"
trap 'rm -f "$LOCKFILE"' EXIT

# ----------------------------
# CONFIG FILE SETUP
# ----------------------------
CONFIG_FILE="$(dirname "$0")/sync_config.sh"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found. Let's set it up."

    read -rp "Enter source directory: " SRC_INPUT
    while [ -z "$SRC_INPUT" ]; do
        echo "Source directory is required."
        read -rp "Enter source directory: " SRC_INPUT
    done

    read -rp "Enter backup destination: " DEST_INPUT
    while [ -z "$DEST_INPUT" ]; do
        echo "Backup destination is required."
        read -rp "Enter backup destination: " DEST_INPUT
    done

    SRC_INPUT="$(realpath "$SRC_INPUT")"
    DEST_INPUT="$(realpath "$DEST_INPUT")"

    cat > "$CONFIG_FILE" <<EOF
SYNC_SRC="$SRC_INPUT"
SYNC_DEST="$DEST_INPUT"
EOF

    echo "Configuration saved to $CONFIG_FILE"
fi

# Load config
source "$CONFIG_FILE"
SRC="$(realpath "$SYNC_SRC")"
DEST="$(realpath "$SYNC_DEST")"

# ----------------------------
# BACKUP SETUP
# ----------------------------
TODAY=$(date +%Y-%m-%d)
NEW_BACKUP="$DEST/backup_$TODAY"

mkdir -p "$NEW_BACKUP"

# ----------------------------
# REMOVE OLD BACKUPS
# ----------------------------
MAX_BACKUPS=3
mapfile -t backups < <(ls -1dt "$DEST"/backup_20* 2>/dev/null | sort)

if [ "${#backups[@]}" -gt "$MAX_BACKUPS" ]; then
    DEL_COUNT=$(( ${#backups[@]} - MAX_BACKUPS ))
    echo "Deleting $DEL_COUNT oldest backup(s)"
    for ((i=0;i<DEL_COUNT;i++)); do
        echo "Deleting: ${backups[i]}"
        rm -rf "${backups[i]}"
    done
fi

# ----------------------------
# LOGGING WITH SIZE MANAGEMENT
# ----------------------------
LOGFILE="$DEST/sync.log"
MAX_LOG_SIZE=$((5 * 1024 * 1024))        # 5 MB max size
TARGET_LOG_SIZE=$((MAX_LOG_SIZE / 2))    # Shrink to 50% of max size

# Shrink log if it exceeds MAX_LOG_SIZE
if [ -f "$LOGFILE" ]; then
    LOGSIZE=$(stat -c%s "$LOGFILE")
    if [ "$LOGSIZE" -gt "$MAX_LOG_SIZE" ]; then
        echo "Log exceeded $MAX_LOG_SIZE bytes, shrinking to $TARGET_LOG_SIZE bytes..."
        tail -c "$TARGET_LOG_SIZE" "$LOGFILE" > "$LOGFILE.tmp" && mv "$LOGFILE.tmp" "$LOGFILE"
    fi
fi

# Redirect stdout/stderr to log
exec >> "$LOGFILE" 2>&1

echo
echo "================================================================="
echo "SYNC START: $(date)"
echo "Source: $SRC"
echo "Backup: $NEW_BACKUP"
echo "================================================================="

# ----------------------------
# SYNC PHASE
# ----------------------------
echo
echo "--- SYNC PHASE ---"

find "$SRC" -mindepth 1 \( -name ".git" -prune -o -print0 \) |
while IFS= read -r -d '' path; do
    rel_path="${path#$SRC/}"

    if [ -f "$path" ]; then
        echo "  Copying file: $rel_path"
        mkdir -p "$(dirname "$NEW_BACKUP/$rel_path")"
        cp -p "$path" "$NEW_BACKUP/$rel_path"
    elif [ -d "$path" ]; then
        echo "  Creating dir: $rel_path"
        mkdir -p "$NEW_BACKUP/$rel_path"
    fi
done

# ----------------------------
# CLEANUP PHASE
# ----------------------------
echo
echo "--- CLEANUP PHASE (removing stale files) ---"

find "$NEW_BACKUP" -mindepth 1 -print0 |
while IFS= read -r -d '' dpath; do
    rel="${dpath#$NEW_BACKUP/}"

    if [ ! -e "$SRC/$rel" ]; then
        echo "  Removing stale: $rel"
        rm -rf "$dpath"
    else
        echo "  Keeping: $rel"
    fi
done

# ----------------------------
# END HEADER
# ----------------------------
echo
echo "----- Sync finished: $(date) -----"
echo "================================================================="
echo
