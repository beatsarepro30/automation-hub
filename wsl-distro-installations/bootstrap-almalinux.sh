#!/usr/bin/env bash
set -euo pipefail

# ==========================================
# AlmaLinux / RHEL WSL Bootstrap Script
# Must be run as root (sudo su -)
# ==========================================

echo "=== Updating system packages ==="
dnf upgrade -y
dnf install -y dnf-plugins-core

echo "=== Installing core CLI tools ==="
dnf install -y \
  git wget unzip tar nano vim tree jq htop fzf less which findutils rsync \
  net-tools iproute bind-utils socat nmap-ncat

echo "=== Setting Git credential helper ==="
git config --global credential.helper store

echo "=== Installing development tools and Python ==="
dnf groupinstall -y "Development Tools"
dnf install -y \
  python3 python3-pip python3-devel gcc make openssl-devel libffi-devel zlib-devel

pip3 install --upgrade pip setuptools wheel

echo "=== Installing quality of life tools ==="
dnf install -y neofetch ripgrep bat exa || true

echo "=== Installing bash completion and optional zsh ==="
dnf install -y bash-completion zsh || true

echo "=== Bootstrap complete! ==="
echo
echo "✅ Recommended next steps:"
echo "  1. Edit /etc/wsl.conf to enable systemd:"
echo "     [boot]"
echo "     systemd=true"
echo "  2. Restart WSL: wsl --shutdown && wsl"
echo "  3. Verify installations:"
echo "     git --version && python3 --version && pip3 --version && htop --version"
echo

exit 0
