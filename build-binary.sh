#!/bin/bash
# Build standalone binary for Raspberry Pi using PyInstaller

set -e

echo "=== ZlsNasDisplay Binary Build Script ==="
echo ""

# Check if running on correct architecture
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
    echo "WARNING: Current architecture is $ARCH"
    echo "Binary should be built on Raspberry Pi (aarch64) for best compatibility"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "Building version: $VERSION"
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist
echo ""

# Build binary with PyInstaller
echo "Building binary with PyInstaller..."
poetry run pyinstaller zlsnasdisplay.spec
echo ""

# Check binary
if [ ! -f "dist/zlsnasdisplay" ]; then
    echo "ERROR: Binary not created!"
    exit 1
fi

BINARY_SIZE=$(du -h dist/zlsnasdisplay | cut -f1)
echo "Binary created successfully: $BINARY_SIZE"
echo ""

# Create tarball for distribution
echo "Creating distribution tarball..."
mkdir -p release-binary/zlsnasdisplay-${VERSION}
cp dist/zlsnasdisplay release-binary/zlsnasdisplay-${VERSION}/
cp README.md LICENSE release-binary/zlsnasdisplay-${VERSION}/

cd release-binary
tar -czf zlsnasdisplay-${VERSION}-linux-aarch64.tar.gz zlsnasdisplay-${VERSION}
cd ..

TARBALL_SIZE=$(du -h release-binary/zlsnasdisplay-${VERSION}-linux-aarch64.tar.gz | cut -f1)
echo "Tarball created: release-binary/zlsnasdisplay-${VERSION}-linux-aarch64.tar.gz ($TARBALL_SIZE)"
echo ""

# Test binary
echo "Testing binary..."
timeout 2 ./dist/zlsnasdisplay 2>&1 | head -5 || true
echo ""

echo "=== Build Complete ==="
echo ""
echo "Binary: dist/zlsnasdisplay"
echo "Tarball: release-binary/zlsnasdisplay-${VERSION}-linux-aarch64.tar.gz"
echo ""
echo "To upload to GitHub release:"
echo "  gh release upload v${VERSION} release-binary/zlsnasdisplay-${VERSION}-linux-aarch64.tar.gz"
echo ""
