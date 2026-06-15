#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UNITY_EDITOR="${UNITY_EDITOR:-}"
TIMEOUT_SECONDS="${UNITY_IMPORT_TIMEOUT_SECONDS:-180}"
FBX_PATH=""
PROJECT_PATH=""

usage() {
  cat <<'USAGE'
Usage: scripts/verify_unity_fbx_import.sh --fbx path/to/model.fbx [--unity /path/to/Unity] [--project /path/to/temp-project] [--timeout-seconds 180]

Verifies that Unity can import an exported FBX by running a batchmode Unity project
with the MacGameRiggerFbxImportCheck editor script.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --fbx)
      FBX_PATH="$2"
      shift 2
      ;;
    --unity)
      UNITY_EDITOR="$2"
      shift 2
      ;;
    --project)
      PROJECT_PATH="$2"
      shift 2
      ;;
    --timeout-seconds)
      TIMEOUT_SECONDS="$2"
      shift 2
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

find_unity_editor() {
  if [ -n "$UNITY_EDITOR" ]; then
    printf '%s\n' "$UNITY_EDITOR"
    return
  fi
  if command -v unity >/dev/null 2>&1; then
    command -v unity
    return
  fi
  if command -v Unity >/dev/null 2>&1; then
    command -v Unity
    return
  fi
  find /Applications/Unity -path "*/Unity.app/Contents/MacOS/Unity" -type f 2>/dev/null | sort -r | head -n 1
}

UNITY_EDITOR="$(find_unity_editor)"
if [ -z "$UNITY_EDITOR" ] || [ ! -x "$UNITY_EDITOR" ]; then
  echo "Unity Editor not found. Install Unity Editor or pass --unity /path/to/Unity.app/Contents/MacOS/Unity." >&2
  exit 2
fi

if [ -z "$PROJECT_PATH" ]; then
  PROJECT_PATH="$(mktemp -d "${TMPDIR:-/tmp}/mac-game-rigger-unity-import.XXXXXX")"
fi

mkdir -p "$PROJECT_PATH/Assets/Editor" "$PROJECT_PATH/Assets/MacGameRiggerImportCandidate"
cp "$REPO_ROOT/tools/unity_import_check/Assets/Editor/MacGameRiggerFbxImportCheck.cs" "$PROJECT_PATH/Assets/Editor/"
cp "$FBX_PATH" "$PROJECT_PATH/Assets/MacGameRiggerImportCandidate/$(basename "$FBX_PATH")"

RESULT_PATH="$PROJECT_PATH/Library/MacGameRiggerImportCheck/result.json"
LOG_PATH="$PROJECT_PATH/unity-import-check.log"

set +e
"$UNITY_EDITOR" \
  -batchmode \
  -quit \
  -nographics \
  -projectPath "$PROJECT_PATH" \
  -executeMethod MacGameRiggerFbxImportCheck.Run \
  -logFile "$LOG_PATH" &
unity_pid=$!
elapsed=0
while kill -0 "$unity_pid" >/dev/null 2>&1; do
  if [ "$elapsed" -ge "$TIMEOUT_SECONDS" ]; then
    kill "$unity_pid" >/dev/null 2>&1
    sleep 1
    if kill -0 "$unity_pid" >/dev/null 2>&1; then
      kill -9 "$unity_pid" >/dev/null 2>&1
    fi
    wait "$unity_pid" >/dev/null 2>&1
    echo "Unity import check timed out after $TIMEOUT_SECONDS seconds" >&2
    if [ -f "$LOG_PATH" ]; then
      tail -n 80 "$LOG_PATH" >&2
    fi
    exit 124
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done
wait "$unity_pid"
unity_status=$?
set -e

if [ "$unity_status" -ne 0 ]; then
  echo "Unity import check failed with exit code $unity_status" >&2
  if [ -f "$LOG_PATH" ]; then
    tail -n 80 "$LOG_PATH" >&2
  fi
  exit "$unity_status"
fi

if [ ! -f "$RESULT_PATH" ]; then
  echo "Unity import check did not produce result JSON: $RESULT_PATH" >&2
  if [ -f "$LOG_PATH" ]; then
    tail -n 80 "$LOG_PATH" >&2
  fi
  exit 1
fi

cat "$RESULT_PATH"
