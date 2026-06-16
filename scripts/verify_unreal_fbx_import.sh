#!/usr/bin/env bash
set -euo pipefail

UNREAL_EDITOR="${UNREAL_EDITOR:-}"
FBX_PATH=""
TIMEOUT_SECONDS="${UNREAL_IMPORT_TIMEOUT_SECONDS:-240}"
DRY_RUN=0

usage() {
  cat <<'USAGE'
Usage: scripts/verify_unreal_fbx_import.sh --fbx path/to/model.fbx [--unreal /path/to/UnrealEditor] [--timeout-seconds 240] [--dry-run]

Validates Unreal import verification inputs. The real batch import commandlet is
not implemented yet; without --dry-run this script returns a machine-readable
blocked result after confirming the FBX and Unreal Editor path.
USAGE
}

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --fbx)
      FBX_PATH="$2"
      shift 2
      ;;
    --unreal)
      UNREAL_EDITOR="$2"
      shift 2
      ;;
    --timeout-seconds)
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

if [ -z "$FBX_PATH" ]; then
  echo "Missing required --fbx path" >&2
  usage >&2
  exit 64
fi

if [ ! -f "$FBX_PATH" ]; then
  echo "FBX file not found: $FBX_PATH" >&2
  exit 66
fi

case "$TIMEOUT_SECONDS" in
  ''|*[!0-9]*)
    echo "Invalid --timeout-seconds value: $TIMEOUT_SECONDS" >&2
    exit 64
    ;;
esac

if [ "$TIMEOUT_SECONDS" -lt 1 ]; then
  echo "Invalid --timeout-seconds value: $TIMEOUT_SECONDS" >&2
  exit 64
fi

find_unreal_editor() {
  if [ -n "$UNREAL_EDITOR" ]; then
    printf '%s\n' "$UNREAL_EDITOR"
    return
  fi
  if command -v UnrealEditor >/dev/null 2>&1; then
    command -v UnrealEditor
    return
  fi
  find /Applications "/Users/Shared/Epic Games" \
    -path "*/UnrealEditor.app/Contents/MacOS/UnrealEditor" \
    -type f 2>/dev/null | sort -r | head -n 1
}

UNREAL_EDITOR="$(find_unreal_editor)"
if [ -z "$UNREAL_EDITOR" ] || [ ! -x "$UNREAL_EDITOR" ]; then
  echo "Unreal Editor not found. Install Unreal Editor or pass --unreal /path/to/UnrealEditor.app/Contents/MacOS/UnrealEditor." >&2
  exit 2
fi

escaped_editor="$(json_escape "$UNREAL_EDITOR")"
escaped_fbx="$(json_escape "$FBX_PATH")"

if [ "$DRY_RUN" -eq 1 ]; then
  printf '{"status":"ready","unrealEditor":%s,"fbx":%s,"timeoutSeconds":%s}\n' \
    "$escaped_editor" "$escaped_fbx" "$TIMEOUT_SECONDS"
  exit 0
fi

printf '{"status":"blocked","reason":"unreal_batch_import_not_implemented","unrealEditor":%s,"fbx":%s,"timeoutSeconds":%s}\n' \
  "$escaped_editor" "$escaped_fbx" "$TIMEOUT_SECONDS"
exit 78

