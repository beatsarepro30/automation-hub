#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_FILE="$SCRIPT_DIR/my_cron_jobs"
LOG_FILE="$SCRIPT_DIR/my_cron_jobs.log"

echo "==== $(date) ====" >> "$LOG_FILE"

# -------------------------
# Detect Platform
# -------------------------
OS=$(uname -s)
PLATFORM=""

if [[ "$OS" == "Linux" || "$OS" == "Darwin" ]]; then
    PLATFORM="unix"
else
    echo "Unsupported OS: $OS" | tee -a "$LOG_FILE"
    exit 1
fi

echo "Detected platform: $PLATFORM" | tee -a "$LOG_FILE"

# -------------------------
# Install Unix Cron Jobs
# -------------------------
if [[ "$PLATFORM" == "unix" ]]; then
    if [ -f "$CRON_FILE" ]; then
        crontab -l > "$SCRIPT_DIR/current_cron" 2>/dev/null || true
        cat "$CRON_FILE" >> "$SCRIPT_DIR/current_cron"
        crontab "$SCRIPT_DIR/current_cron"
        echo "Unix cron jobs installed" | tee -a "$LOG_FILE"
    fi
fi

echo "==== Done ====" | tee -a "$LOG_FILE"
