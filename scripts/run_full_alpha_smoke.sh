#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BLENDER_BIN="${BLENDER_BIN:-}"
UNITY_EDITOR="${UNITY_EDITOR:-}"
UNITY_FBX=""
SKIP_BLENDER=0

usage() {
  cat <<'USAGE'
Usage: scripts/run_full_alpha_smoke.sh [--blender /path/to/blender] [--skip-blender] [--unity-fbx path/to/export.fbx] [--unity /path/to/Unity]

Runs the local alpha release gate:
  - manifest JSON validation
  - Python unit tests
  - Python compileall
  - optional Blender headless tests
  - add-on package build and package content check
  - optional Unity FBX import verification
USAGE
}

log_step() {
  printf '\n==> %s\n' "$1"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --blender)
      BLENDER_BIN="$2"
      shift 2
      ;;
    --skip-blender)
      SKIP_BLENDER=1
      shift
      ;;
    --unity-fbx)
      UNITY_FBX="$2"
      shift 2
      ;;
    --unity)
      UNITY_EDITOR="$2"
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

cd "$REPO_ROOT"

log_step "Validate sample manifest JSON"
python3 -m json.tool samples/manifest.json >/dev/null
scripts/validate_asset_evidence.py --manifest samples/manifest.json --quiet

log_step "Run Python unit tests"
python3 -m pytest tests -q

log_step "Run compileall"
python3 -m compileall addon/mac_game_rigger tests
python3 -m py_compile scripts/run_blender_compat_matrix.py
python3 -m py_compile scripts/validate_asset_evidence.py

if [ "$SKIP_BLENDER" -eq 0 ]; then
  if [ -z "$BLENDER_BIN" ] && command -v blender >/dev/null 2>&1; then
    BLENDER_BIN="$(command -v blender)"
  fi

  if [ -n "$BLENDER_BIN" ] && [ -x "$BLENDER_BIN" ]; then
    log_step "Run Blender headless tests with $BLENDER_BIN"
    while IFS= read -r test_path; do
      printf 'Running %s\n' "$test_path"
      "$BLENDER_BIN" --background --factory-startup --python "$test_path"
    done < <(find blender_tests -name 'test_*.py' -type f | sort)
  else
    log_step "Skip Blender headless tests"
    echo "Blender executable not found. Pass --blender /path/to/blender or set BLENDER_BIN."
  fi
else
  log_step "Skip Blender headless tests"
  echo "Skipped by --skip-blender."
fi

log_step "Build add-on package"
ZIP_PATH="$(scripts/package_addon.sh)"
echo "$ZIP_PATH"

log_step "Check package contents"
zip_listing="$(unzip -Z1 "$ZIP_PATH")"
required_package_paths=(
  "mac_game_rigger/__init__.py"
  "docs/release-checklist.md"
  "docs/alpha-smoke-results.md"
  "docs/alpha-gap-roadmap.md"
  "docs/install-guide.md"
  "docs/blender-compatibility-matrix.md"
  "samples/manifest.json"
  "scripts/run_full_alpha_smoke.sh"
  "scripts/validate_asset_evidence.py"
  "scripts/run_blender_compat_matrix.py"
)

for required_path in "${required_package_paths[@]}"; do
  case "$zip_listing" in
    *"$required_path"*) ;;
    *)
      echo "Missing package path: $required_path" >&2
      exit 1
      ;;
  esac
done

if [ -n "$UNITY_FBX" ]; then
  log_step "Run Unity import verification"
  unity_args=(--fbx "$UNITY_FBX")
  if [ -n "$UNITY_EDITOR" ]; then
    unity_args+=(--unity "$UNITY_EDITOR")
  fi
  scripts/verify_unity_fbx_import.sh "${unity_args[@]}"
else
  log_step "Skip Unity import verification"
  echo "Pass --unity-fbx path/to/export.fbx to run Unity import verification."
fi

log_step "Alpha smoke gate completed"
