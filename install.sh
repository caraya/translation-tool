#!/bin/bash
set -e

# Define paths
APP_NAME="translation-tool"
DIST_DIR="dist/$APP_NAME"
INSTALL_LIB="/usr/local/lib/$APP_NAME"
INSTALL_BIN="/usr/local/bin/$APP_NAME"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

echo "Installing $APP_NAME..."

# Check if build exists
if [ ! -d "$DIST_DIR" ]; then
    echo "Error: Build artifact '$DIST_DIR' not found."
    echo "Please run: pyinstaller --onedir --name translation-tool run.py"
    exit 1
fi

# 1. Remove old installation
if [ -d "$INSTALL_LIB" ]; then
    echo "Removing existing installation at $INSTALL_LIB..."
    rm -rf "$INSTALL_LIB"
fi

if [ -L "$INSTALL_BIN" ] || [ -f "$INSTALL_BIN" ]; then
    echo "Removing existing symlink at $INSTALL_BIN..."
    rm -f "$INSTALL_BIN"
fi

# Ensure parent directories exist
mkdir -p /usr/local/lib
mkdir -p /usr/local/bin

# 2. Copy new files
echo "Copying files to /usr/local/lib..."
# Copy the directory into /usr/local/lib/
cp -R "$DIST_DIR" /usr/local/lib/

# 3. Create wrapper script
echo "Creating wrapper script at $INSTALL_BIN..."
cat <<EOF > "$INSTALL_BIN"
#!/bin/bash
# Wrapper script for translation-tool to set library paths for torchcodec
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:/usr/local/lib:\$DYLD_LIBRARY_PATH"
exec "$INSTALL_LIB/$APP_NAME" "\$@"
EOF

chmod +x "$INSTALL_BIN"

echo "Installation complete!"
echo "You can now run '$APP_NAME --help' from anywhere."
