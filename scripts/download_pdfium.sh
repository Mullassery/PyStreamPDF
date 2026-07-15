#!/bin/bash
# Download PDFium binary for the current platform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LIB_DIR="$PROJECT_ROOT/lib"

# Detect OS and architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

# Use a simpler approach: try to find a pre-built binary via system package manager
# For development, we'll provide instructions to install via Homebrew/apt

mkdir -p "$LIB_DIR"

echo "📦 PDFium is required to build StreamPDF."
echo ""
echo "Installation instructions:"
echo ""

case "$OS" in
    Darwin)
        echo "macOS (via Homebrew):"
        echo "  brew install pdfium-render"
        echo ""
        echo "Or manually:"
        echo "  1. Download from https://github.com/bblanchon/pdfium-binaries/releases"
        echo "  2. Place libpdfium.dylib in $LIB_DIR/"
        exit 0
        ;;
    Linux)
        echo "Linux (via apt):"
        echo "  sudo apt-get install libpdfium"
        echo ""
        echo "Or manually:"
        echo "  1. Download from https://github.com/bblanchon/pdfium-binaries/releases"
        echo "  2. Place libpdfium.so in $LIB_DIR/"
        exit 0
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac
