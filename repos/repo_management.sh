#!/bin/bash

# Base directory where all repos will be nested
PARENT_DIR="$HOME/tmp"

# Config file listing repos to keep
CONFIG_FILE="$HOME/repos_config.yml"

# Ensure the config file exists
touch "$CONFIG_FILE"

echo "Reading config from $CONFIG_FILE..."
echo "Parent directory: $PARENT_DIR"

# Expand ~ for safety
expand_path() {
    eval echo "$1"
}

# Read active repos (ignore commented and blank lines)
mapfile -t ACTIVE_PATHS < <(grep -vE '^\s*#' "$CONFIG_FILE" | awk 'NF {print $1}')

# Read commented out repos (lines starting with # and not blank)
mapfile -t COMMENTED_PATHS < <(grep -E '^\s*#' "$CONFIG_FILE" | awk 'NF {print $2}')

echo "Active repo paths: ${ACTIVE_PATHS[*]}"
echo "Commented out repo paths: ${COMMENTED_PATHS[*]}"

# Recursively find git repos under PARENT_DIR
while IFS= read -r repo_dir; do
    # Compute path relative to PARENT_DIR
    relative_path=${repo_dir#"$PARENT_DIR/"}

    # If repo is not in config (active or commented), add it
    if [[ ! " ${ACTIVE_PATHS[*]} ${COMMENTED_PATHS[*]} " =~ " $relative_path " ]]; then
        remote_url=$(git -C "$repo_dir" config --get remote.origin.url 2>/dev/null)
        if [ -n "$remote_url" ]; then
            echo "Adding new repo to config: $relative_path $remote_url"
            echo "$relative_path $remote_url" >> "$CONFIG_FILE"
        else
            echo "Warning: repo $relative_path has no remote URL, skipping addition to config"
        fi
    fi

    # If repo is commented out, delete it
    if [[ " ${COMMENTED_PATHS[*]} " =~ " $relative_path " ]]; then
        echo "Deleting commented out repo: $relative_path"
        rm -rf "$repo_dir"
    fi
done < <(
    # Find all directories containing .git recursively
    find "$PARENT_DIR" -type d -name ".git" -prune -exec dirname {} \;
)

# Clone or update active repos only
while IFS= read -r line; do
    # Skip empty or whitespace-only lines silently
    [[ -z "$line" || "$line" =~ ^[[:space:]]*$ ]] && continue

    # Skip commented lines
    [[ "$line" =~ ^# ]] && continue

    relative_path=$(echo "$line" | awk '{print $1}')
    remote_url=$(echo "$line" | awk '{print $2}')

    full_path="$PARENT_DIR/$relative_path"

    # Skip lines that don't have both fields
    if [[ -z "$relative_path" || -z "$remote_url" ]]; then
        echo "Warning: malformed line in config: '$line' (skipping)"
        continue
    fi

    if [ -d "$full_path/.git" ]; then
        continue  # Repo exists, skip
    else
        echo "Cloning missing active repo: $relative_path from $remote_url"
        mkdir -p "$(dirname "$full_path")"
        git clone "$remote_url" "$full_path"
    fi
done < "$CONFIG_FILE"

echo "Cleanup complete!"
