#!/bin/bash
set -euo pipefail

# ----------------------------
# CONFIG FILE SETUP
# ----------------------------
CONFIG_FILE="$(dirname "$0")/config.sh"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found. Let's set it up."

    read -rp "Enter parent directory where repos will be nested: " PARENT_DIR
    while [ -z "$PARENT_DIR" ]; do
        echo "Parent directory is required."
        read -rp "Enter parent directory where repos will be nested: " PARENT_DIR
    done

    # Replace leading ~ with $HOME for storage
    PARENT_DIR="${PARENT_DIR/#\~/$HOME}"

    cat > "$CONFIG_FILE" <<EOF
PARENT_DIR="$PARENT_DIR"
EOF

    echo "Configuration saved to $CONFIG_FILE"
fi

# Load config
source "$CONFIG_FILE"

# --- Expand any ~ that might still exist ---
PARENT_DIR=$(eval echo "$PARENT_DIR")

# --- Utility function to print paths with ~ ---
print_path() {
    local path="$1"
    if [[ "$path" == "$HOME"* ]]; then
        echo "~${path#$HOME}"
    else
        echo "$path"
    fi
}

echo "Using parent directory: $(print_path "$PARENT_DIR")"

# --- Ensure the repo config file exists ---
REPOS_FILE="$PARENT_DIR/repos.yml"
mkdir -p "$PARENT_DIR"
[ -f "$REPOS_FILE" ] || touch "$REPOS_FILE"

# --- Read active and commented repos safely ---
ACTIVE_PATHS=()
COMMENTED_PATHS=()
while IFS= read -r line || [ -n "$line" ]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^# ]]; then
        COMMENTED_PATHS+=("$(echo "$line" | awk '{print $2}')")
    else
        ACTIVE_PATHS+=("$(echo "$line" | awk '{print $1}')")
    fi
done < "$REPOS_FILE"

# Print paths using ~
echo -n "Active repo paths: "
for p in "${ACTIVE_PATHS[@]}"; do
    echo -n "$(print_path "$PARENT_DIR/$p") "
done
echo

echo -n "Commented out repo paths: "
for p in "${COMMENTED_PATHS[@]}"; do
    [[ -n "$p" ]] && echo -n "$(print_path "$PARENT_DIR/$p") "
done
echo

# --- Recursively find git repos using pure bash ---
find_git_repos() {
    local dir="$1"
    local sub
    dir="${dir%/}"  # Normalize path

    if [ -d "$dir/.git" ]; then
        echo "$dir"
    fi

    for sub in "$dir"/*/; do
        [ -d "$sub" ] || continue
        sub="${sub%/}"  # Normalize path
        find_git_repos "$sub"
    done
}

# Store the list of git repos in a temporary file
TMP_REPOS=$(mktemp)
find_git_repos "$PARENT_DIR" > "$TMP_REPOS"

while IFS= read -r repo_dir; do
    relative_path=${repo_dir#"$PARENT_DIR/"}

    # Add new repos to repos.yml if not listed
    if [[ ! " ${ACTIVE_PATHS[*]} ${COMMENTED_PATHS[*]} " =~ " $relative_path " ]]; then
        remote_url=$(git -C "$repo_dir" config --get remote.origin.url 2>/dev/null)
        if [ -n "$remote_url" ]; then
            echo "Adding new repo to config: $(print_path "$repo_dir") $remote_url"
            echo "$relative_path $remote_url" >> "$REPOS_FILE"
        else
            echo "Warning: repo $(print_path "$repo_dir") has no remote URL, skipping addition to config"
        fi
    fi

    # Delete commented out repos
    if [[ " ${COMMENTED_PATHS[*]} " =~ " $relative_path " ]]; then
        echo "Deleting commented out repo: $(print_path "$repo_dir")"
        rm -rf "$repo_dir"
    fi
done < "$TMP_REPOS"

rm -f "$TMP_REPOS"

# --- Clone or update active repos only ---
while IFS= read -r line || [ -n "$line" ]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" =~ ^# ]] && continue

    relative_path=$(echo "$line" | awk '{print $1}')
    remote_url=$(echo "$line" | awk '{print $2}')
    full_path="$PARENT_DIR/$relative_path"

    if [[ -z "$relative_path" || -z "$remote_url" ]]; then
        echo "Warning: malformed line in config: '$line' (skipping)"
        continue
    fi

    if [ -d "$full_path/.git" ]; then
        continue  # Repo exists, skip
    else
        echo "Cloning missing active repo: $(print_path "$full_path") from $remote_url"
        mkdir -p "$(dirname "$full_path")"
        git clone "$remote_url" "$full_path"
    fi
done < "$REPOS_FILE"

# --- Remove any empty directories that do NOT contain .git ---
echo "Removing empty directories (excluding git repos) under $(print_path "$PARENT_DIR")..."
TMP_EMPTY=$(mktemp)
find -L "$PARENT_DIR" -type d -empty > "$TMP_EMPTY"
while IFS= read -r empty_dir; do
    rmdir "$empty_dir" 2>/dev/null || true
done < "$TMP_EMPTY"
rm -f "$TMP_EMPTY"

echo "Cleanup complete!"
