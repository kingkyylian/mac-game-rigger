#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UNREAL_EDITOR="${UNREAL_EDITOR:-}"
FBX_PATH=""
PROJECT_PATH=""
TIMEOUT_SECONDS="${UNREAL_IMPORT_TIMEOUT_SECONDS:-240}"
DRY_RUN=0
PREPARE_ONLY=0
PREPARED_PROJECT_PATH=""
PREPARED_PROJECT_FILE=""
PREPARED_COPIED_FBX=""
PREPARED_SCRIPT_PATH=""
PREPARED_CONFIG_PATH=""
PREPARED_RESULT_PATH=""
PREPARED_SAVED_DIR=""

usage() {
  cat <<'USAGE'
Usage: scripts/verify_unreal_fbx_import.sh --fbx path/to/model.fbx [--unreal /path/to/UnrealEditor] [--project path/to/project] [--timeout-seconds 240] [--dry-run] [--prepare-only]

Validates Unreal import verification inputs. --prepare-only creates a throwaway
Unreal project workspace, copies the FBX, writes import config, and installs the
Unreal Python import script without requiring Unreal Editor. Without --dry-run
or --prepare-only, this script prepares the workspace, runs Unreal Editor with
the Python import script, and emits the script's machine-readable result JSON.
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
    --project)
      PROJECT_PATH="$2"
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
    --prepare-only)
      PREPARE_ONLY=1
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

prepare_unreal_workspace() {
  local project_path="$PROJECT_PATH"
  if [ -z "$project_path" ]; then
    project_path="$(mktemp -d "${TMPDIR:-/tmp}/mac-game-rigger-unreal-import.XXXXXX")/MacGameRiggerImportCheck"
  fi

  local import_dir="$project_path/Import"
  local python_dir="$project_path/Content/Python"
  local saved_dir="$project_path/Saved/MacGameRiggerImportCheck"
  local copied_fbx="$import_dir/$(basename "$FBX_PATH")"
  local script_source="$REPO_ROOT/tools/unreal_import_check/MacGameRiggerFbxImportCheck.py"
  local script_path="$python_dir/MacGameRiggerFbxImportCheck.py"
  local config_path="$saved_dir/import-config.json"
  local result_path="$saved_dir/import-result.json"
  local project_file="$project_path/$(basename "$project_path").uproject"

  if [ ! -f "$script_source" ]; then
    echo "Unreal import script template not found: $script_source" >&2
    exit 70
  fi

  mkdir -p "$import_dir" "$python_dir" "$saved_dir"
  cp "$FBX_PATH" "$copied_fbx"
  cp "$script_source" "$script_path"

  python3 - "$project_file" "$config_path" "$copied_fbx" "$result_path" <<'PY'
import json
import sys
from pathlib import Path

project_file = Path(sys.argv[1])
config_path = Path(sys.argv[2])
copied_fbx = Path(sys.argv[3])
result_path = Path(sys.argv[4])

project_payload = {
    "FileVersion": 3,
    "EngineAssociation": "",
    "Category": "MacGameRigger",
    "Description": "Temporary Mac Game Rigger FBX import verification project.",
}
project_file.write_text(json.dumps(project_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

config_payload = {
    "fbxPath": str(copied_fbx),
    "resultPath": str(result_path),
    "destinationPath": "/Game/MacGameRiggerImportCandidate",
}
config_path.write_text(json.dumps(config_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

  PREPARED_PROJECT_PATH="$project_path"
  PREPARED_PROJECT_FILE="$project_file"
  PREPARED_COPIED_FBX="$copied_fbx"
  PREPARED_SCRIPT_PATH="$script_path"
  PREPARED_CONFIG_PATH="$config_path"
  PREPARED_RESULT_PATH="$result_path"
  PREPARED_SAVED_DIR="$saved_dir"
}

print_prepared_workspace_json() {
  printf '{"status":"prepared","projectPath":%s,"projectFile":%s,"copiedFbx":%s,"scriptPath":%s,"configPath":%s,"resultPath":%s}\n' \
    "$(json_escape "$PREPARED_PROJECT_PATH")" \
    "$(json_escape "$PREPARED_PROJECT_FILE")" \
    "$(json_escape "$PREPARED_COPIED_FBX")" \
    "$(json_escape "$PREPARED_SCRIPT_PATH")" \
    "$(json_escape "$PREPARED_CONFIG_PATH")" \
    "$(json_escape "$PREPARED_RESULT_PATH")"
}

run_unreal_editor() {
  local stdout_log="$PREPARED_SAVED_DIR/unreal-stdout.log"
  local stderr_log="$PREPARED_SAVED_DIR/unreal-stderr.log"
  local run_result="$PREPARED_SAVED_DIR/unreal-run-result.json"

  MAC_GAME_RIGGER_UNREAL_CONFIG="$PREPARED_CONFIG_PATH" python3 - \
    "$UNREAL_EDITOR" \
    "$PREPARED_PROJECT_FILE" \
    "$PREPARED_SCRIPT_PATH" \
    "$TIMEOUT_SECONDS" \
    "$stdout_log" \
    "$stderr_log" \
    "$run_result" <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys

editor = sys.argv[1]
project_file = sys.argv[2]
script_path = sys.argv[3]
timeout_seconds = int(sys.argv[4])
stdout_log = Path(sys.argv[5])
stderr_log = Path(sys.argv[6])
run_result = Path(sys.argv[7])

command = [
    editor,
    project_file,
    "-unattended",
    "-nop4",
    "-nosplash",
    f"-ExecutePythonScript={script_path}",
]

payload = {
    "command": command,
    "timedOut": False,
    "unrealExitCode": None,
    "stdoutLog": str(stdout_log),
    "stderrLog": str(stderr_log),
}

try:
    with stdout_log.open("w", encoding="utf-8") as stdout_handle, stderr_log.open(
        "w", encoding="utf-8"
    ) as stderr_handle:
        completed = subprocess.run(
            command,
            env=os.environ.copy(),
            text=True,
            stdout=stdout_handle,
            stderr=stderr_handle,
            timeout=timeout_seconds,
            check=False,
        )
    payload["unrealExitCode"] = completed.returncode
except subprocess.TimeoutExpired:
    payload["timedOut"] = True
    payload["unrealExitCode"] = 124

run_result.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

print_unreal_import_result() {
  local run_result="$PREPARED_SAVED_DIR/unreal-run-result.json"

  python3 - \
    "$PREPARED_RESULT_PATH" \
    "$run_result" \
    "$PREPARED_PROJECT_PATH" \
    "$PREPARED_PROJECT_FILE" \
    "$PREPARED_COPIED_FBX" \
    "$PREPARED_SCRIPT_PATH" \
    "$PREPARED_CONFIG_PATH" \
    "$UNREAL_EDITOR" <<'PY'
import json
from pathlib import Path
import sys

result_path = Path(sys.argv[1])
run_result_path = Path(sys.argv[2])

run_result = json.loads(run_result_path.read_text(encoding="utf-8"))
if result_path.exists():
    payload = json.loads(result_path.read_text(encoding="utf-8"))
else:
    payload = {
        "status": "fail",
        "reason": "unreal_result_missing",
    }

payload.update(
    {
        "projectPath": sys.argv[3],
        "projectFile": sys.argv[4],
        "copiedFbx": sys.argv[5],
        "scriptPath": sys.argv[6],
        "configPath": sys.argv[7],
        "resultPath": str(result_path),
        "unrealEditor": sys.argv[8],
        "unrealExitCode": run_result["unrealExitCode"],
        "timedOut": run_result["timedOut"],
        "stdoutLog": run_result["stdoutLog"],
        "stderrLog": run_result["stderrLog"],
        "command": run_result["command"],
    }
)

print(json.dumps(payload, sort_keys=True))
raise SystemExit(0 if payload.get("status") == "pass" and run_result["unrealExitCode"] == 0 else 1)
PY
}

if [ "$PREPARE_ONLY" -eq 1 ]; then
  prepare_unreal_workspace
  print_prepared_workspace_json
  exit 0
fi

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

prepare_unreal_workspace
run_unreal_editor
print_unreal_import_result
