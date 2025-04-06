#!/bin/bash

# Exit immediately on any error
set -e

# === Usage check ===
if [ -z "$1" ]; then
  echo "❗ Usage: $0 <python_version>"
  echo "👉 Example: $0 3.13.2"
  exit 1
fi

# === Config ===
PYTHON_VERSION="$1"
INSTALL_DIR="$HOME/tmp_python_build"
PYTHON_TARBALL="Python-$PYTHON_VERSION.tgz"
PYTHON_SRC_DIR="Python-$PYTHON_VERSION"
PY_EXEC="/usr/local/bin/python${PYTHON_VERSION%.*}"

# === Step 1: Install build dependencies ===
echo "🔧 Installing build dependencies..."
sudo apt update -y
sudo apt install -y build-essential wget \
    zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev \
    libreadline-dev libffi-dev libsqlite3-dev libbz2-dev

# === Step 2: Download and extract source ===
echo "📦 Downloading Python $PYTHON_VERSION..."
mkdir -p "$INSTALL_DIR" && cd "$INSTALL_DIR"
wget -q "https://www.python.org/ftp/python/$PYTHON_VERSION/$PYTHON_TARBALL"
tar -xf "$PYTHON_TARBALL"
cd "$PYTHON_SRC_DIR"

# === Step 3: Build and install ===
echo "⚙️ Configuring build..."
./configure --enable-optimizations

echo "🛠️ Compiling (this may take a few minutes)..."
make -j"$(nproc)"

echo "📥 Installing Python $PYTHON_VERSION..."
sudo make altinstall

# === Step 4: Install pip for the new Python version ===
echo "📦 Installing pip..."
$PY_EXEC -m ensurepip --upgrade
$PY_EXEC -m pip install --upgrade pip

# === Step 5: Cleanup ===
cd ~
rm -rf "$INSTALL_DIR"

# === Step 6: Verify ===
echo "✅ Installed Python version:"
$PY_EXEC --version
echo "✅ Installed pip version:"
$PY_EXEC -m pip --version

echo "🎉 Python $PYTHON_VERSION and pip installed successfully!"
