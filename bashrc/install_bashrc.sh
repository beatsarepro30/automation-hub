#!/usr/bin/env bash
#
# install_bashrc.sh
# Injects repo bashrc into ~/.bashrc safely

set -euo pipefail

REPO_BASHRC="$(pwd)/bashrc"
INJECT_LINE="if [ -f \"$REPO_BASHRC\" ]; then source \"$REPO_BASHRC\"; else echo \"[WARN] Repo bashrc not found at $REPO_BASHRC\"; fi"

# Load reusable functions
source ./bashrc_utils.sh

# Inject bashrc from repo
inject_bashrc_line "$INJECT_LINE" "automations-hub-bashrc"