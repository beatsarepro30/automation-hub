#!/usr/bin/env bash
#
# install_bashrc.sh
# Injects repo bashrc into ~/.bashrc safely

set -euo pipefail

# Load reusable functions
source ./bashrc_utils.sh

# List of bashrc files to inject
declare -A BASHRC_FILES=(
    ["automations-hub-bashrc"]="$(pwd)/bashrc"
    ["terraform-bashrc"]="$(pwd)/bashrc_terraform"
)

# Inject each bashrc
for id in "${!BASHRC_FILES[@]}"; do
    file_path="${BASHRC_FILES[$id]}"
    inject_line="if [ -f \"$file_path\" ]; then source \"$file_path\"; else echo \"[WARN] Repo bashrc not found at $file_path\"; fi"
    inject_bashrc_line "$inject_line" "$id"
done