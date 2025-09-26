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
        crontab "$CRON_FILE"
        echo "Unix cron jobs overwritten with $CRON_FILE" | tee -a "$LOG_FILE"
    else
        echo "Cron file not found: $CRON_FILE" | tee -a "$LOG_FILE"
        exit 1
    fi
fi

echo "==== Done ====" | tee -a "$LOG_FILE"
