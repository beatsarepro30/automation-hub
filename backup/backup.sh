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
# REMOVE OLD BACKUPS (robust)
# ----------------------------
MAX_BACKUPS=3
backups=()  # Initialize array
for dir in "$DEST"/backup_*; do
    [ -d "$dir" ] || continue
    backups+=("$dir")
done

IFS=$'\n' backups=($(printf "%s\n" "${backups[@]}" | sort))

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
# SYNC PHASE (recursive, git-aware)
# ----------------------------
echo
echo "--- SYNC PHASE ---"

sync_dir() {
    local src_dir="$1"
    local dest_dir="$2"

    # Skip git repos
    if [ -d "$src_dir/.git" ]; then
        echo "  Skipping git repo: ${src_dir#$SRC/}"
        return
    fi

    mkdir -p "$dest_dir"

    for entry in "$src_dir"/*; do
        [ -e "$entry" ] || continue
        local rel_path="${entry#$SRC/}"

        if [ -d "$entry" ]; then
            sync_dir "$entry" "$dest_dir/$(basename "$entry")"
        elif [ -f "$entry" ]; then
            echo "  Copying file: $rel_path"
            mkdir -p "$(dirname "$dest_dir/$(basename "$entry")")"
            cp -p "$entry" "$dest_dir/$(basename "$entry")"
        fi
    done
}

sync_dir "$SRC" "$NEW_BACKUP"

# ----------------------------
# CLEANUP PHASE (recursive, git-aware)
# ----------------------------
echo
echo "--- CLEANUP PHASE (removing stale files) ---"

cleanup_dir() {
    local backup_dir="$1"
    local src_dir="$2"

    for entry in "$backup_dir"/*; do
        [ -e "$entry" ] || continue
        local rel_path="${entry#$NEW_BACKUP/}"
        local corresponding_src="$src_dir/${entry#$backup_dir/}"

        if [ -d "$corresponding_src/.git" ]; then
            continue
        fi

        if [ ! -e "$corresponding_src" ]; then
            echo "  Removing stale: $rel_path"
            rm -rf "$entry"
        elif [ -d "$entry" ]; then
            cleanup_dir "$entry" "$corresponding_src"
        else
            echo "  Keeping: $rel_path"
        fi
    done
}

cleanup_dir "$NEW_BACKUP" "$SRC"

# ----------------------------
# END HEADER
# ----------------------------
echo
echo "----- Sync finished: $(date) -----"
echo "================================================================="
echo
