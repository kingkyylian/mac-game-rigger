#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION="0.1.0"
PACKAGE_NAME="MacGameRigger-${VERSION}"
BUILD_DIR="$REPO_ROOT/build/package/$PACKAGE_NAME"
DIST_DIR="$REPO_ROOT/dist"
ZIP_PATH="$DIST_DIR/${PACKAGE_NAME}.zip"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

rsync -a \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  "$REPO_ROOT/addon/mac_game_rigger" \
  "$BUILD_DIR/"

rsync -a "$REPO_ROOT/docs" "$BUILD_DIR/"
rsync -a "$REPO_ROOT/samples" "$BUILD_DIR/"
rsync -a \
  --exclude "__pycache__/" \
  "$REPO_ROOT/scripts" \
  "$BUILD_DIR/"
cp "$REPO_ROOT/README.md" "$BUILD_DIR/README.md"
cp "$REPO_ROOT/pyproject.toml" "$BUILD_DIR/pyproject.toml"

rm -f "$ZIP_PATH"
(
  cd "$REPO_ROOT/build/package"
  zip -qr "$ZIP_PATH" "$PACKAGE_NAME"
)

echo "$ZIP_PATH"
