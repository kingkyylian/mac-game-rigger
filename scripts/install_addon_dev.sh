#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="$REPO_ROOT/addon/mac_game_rigger"
BLENDER_VERSION="${BLENDER_VERSION:-4.2}"
ADDONS_DIR="$HOME/Library/Application Support/Blender/$BLENDER_VERSION/scripts/addons"
ADDON_DIR="$ADDONS_DIR/mac_game_rigger"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "Add-on source directory not found: $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$ADDONS_DIR"

if [ -L "$ADDON_DIR" ]; then
  rm "$ADDON_DIR"
elif [ -e "$ADDON_DIR" ]; then
  echo "Refusing to replace non-symlink path: $ADDON_DIR" >&2
  exit 1
fi

ln -s "$SOURCE_DIR" "$ADDON_DIR"

echo "Linked Mac Game Rigger add-on:"
echo "$ADDON_DIR -> $SOURCE_DIR"
