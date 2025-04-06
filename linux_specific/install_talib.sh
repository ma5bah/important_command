#!/bin/bash

# Exit on any error
set -e

PYTHON_EXEC="python3.13"
PIP_EXEC="pip3.13"
TA_VERSION="0.6.1"
TA_SRC="ta-lib-${TA_VERSION}-src.tar.gz"
TA_DIR="ta-lib-${TA_VERSION}"
TA_URL="https://github.com/ta-lib/ta-lib/releases/download/v${TA_VERSION}/${TA_SRC}"

echo "🧹 Step 1: Cleaning up any previous TA-Lib installation..."
sudo rm -rf /tmp/ta-lib*
$PIP_EXEC uninstall TA-Lib -y || true

echo "🔧 Step 2: Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y build-essential wget pkg-config

echo "📦 Step 3: Downloading and building TA-Lib from source..."
cd /tmp
wget -q "$TA_URL"
tar -xzf "$TA_SRC"
cd "$TA_DIR"
CFLAGS="-O0" ./configure --prefix=/usr
make CFLAGS="-O0"
sudo make install

echo "🌿 Step 4: Setting environment variables..."
export TA_INCLUDE_PATH=/usr/include/ta-lib
export TA_LIBRARY_PATH=/usr/lib

echo "🐍 Step 5: Installing TA-Lib Python wrapper with debug flags..."
CFLAGS="-O0" $PIP_EXEC install --no-cache-dir TA-Lib==$TA_VERSION

echo "✅ TA-Lib installation complete for Python 3.13!"
