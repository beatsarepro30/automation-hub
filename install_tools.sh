set -euo pipefail

# === Config ===
INSTALL_DIR="$HOME/bin"   # Directory to install executables
FZF_REPO="junegunn/fzf"
JQ_REPO="jqlang/jq"

# === Detect OS and Arch ===
detect_os_arch() {
    local os arch
    os=$(uname -s)
    case "$os" in
        Linux*)   os="linux" ;;
        Darwin*)  os="macos" ;;
        MINGW*|MSYS*|CYGWIN*) os="windows" ;;
        *)        echo "Unsupported OS: $os" >&2; exit 1 ;;
    esac

    arch=$(uname -m)
    case "$arch" in
        x86_64) arch="amd64" ;;
        aarch64|arm64) arch="arm64" ;;
        *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;
    esac

    echo "$os" "$arch"
}

read OS ARCH < <(detect_os_arch)

mkdir -p "$INSTALL_DIR"

# === Function to fetch latest release asset URL from GitHub ===
get_latest_url() {
    local repo="$1"
    local pattern="$2"
    local api_url="https://api.github.com/repos/$repo/releases/latest"

    local url
    url=$(curl -fsSL "$api_url" \
          | grep -Po '"browser_download_url": "\K[^"]+' \
          | grep -i "$pattern" \
          | head -n1)

    echo "$url"
}

# === Generic installer function ===
install_command_if_missing() {
    local cmd_name="$1"
    local repo="$2"
    local pattern="${3:-${OS}-${ARCH}}"

    if command -v "$cmd_name" &>/dev/null; then
        echo "$cmd_name is already installed"
        return
    fi

    echo "$cmd_name not found. Downloading latest release..."
    local url
    url=$(get_latest_url "$repo" "$pattern")

    if [[ -z "$url" ]]; then
        echo "Could not find a release for $cmd_name ($OS-$ARCH)" >&2
        exit 1
    fi

    echo "Downloading $url..."
    
    tmp_dir=$(mktemp -d)
    trap '[[ -n "$tmp_dir" ]] && rm -rf "$tmp_dir"' EXIT

    local download_path exe_file
    download_path="$tmp_dir/$(basename "$url")"
    curl -fsSL -L "$url" -o "$download_path"

    if [[ "$download_path" == *.zip ]]; then
        echo "Extracting $download_path..."
        unzip -q "$download_path" -d "$tmp_dir"

        exe_file=$(find "$tmp_dir" -type f \( -name "*.exe" -o -name "$cmd_name" \) | head -n1)
        if [[ -z "$exe_file" ]]; then
            echo "No executable found in $download_path" >&2
            exit 1
        fi
    else
        exe_file="$download_path"
    fi

    chmod +x "$exe_file"

    if [[ $INSTALL_DIR == /usr/* ]]; then
        sudo mv -f "$exe_file" "$INSTALL_DIR/$cmd_name"
    else
        mv -f "$exe_file" "$INSTALL_DIR/$cmd_name"
    fi

    echo "$cmd_name installed to $INSTALL_DIR/$cmd_name"
}


# === Install tools ===
install_command_if_missing "jq" "$JQ_REPO"
install_command_if_missing "fzf" "$FZF_REPO" "fzf-.*-${OS}_${ARCH}"

echo "Installation complete. You may need to restart your shell or run 'source ~/.bashrc' to update PATH."
