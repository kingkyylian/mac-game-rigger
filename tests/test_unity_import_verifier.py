import json
import os
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/verify_unity_fbx_import.sh"


def test_unity_import_verifier_invokes_editor_and_reads_result_json(tmp_path):
    fbx_path = tmp_path / "sample.fbx"
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")
    fake_unity = tmp_path / "fake-unity"
    fake_unity.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
project_path=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -projectPath)
      project_path="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
mkdir -p "$project_path/Library/MacGameRiggerImportCheck"
cat > "$project_path/Library/MacGameRiggerImportCheck/result.json" <<'JSON'
{"status":"pass","assetPath":"Assets/MacGameRiggerImportCandidate/sample.fbx"}
JSON
""",
        encoding="utf-8",
    )
    fake_unity.chmod(0o755)

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--unity",
            str(fake_unity),
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PATH": os.environ["PATH"]},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["assetPath"] == "Assets/MacGameRiggerImportCandidate/sample.fbx"


def test_unity_import_verifier_reports_missing_editor(tmp_path):
    fbx_path = tmp_path / "sample.fbx"
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--unity",
            str(tmp_path / "missing-unity"),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Unity Editor not found" in result.stderr


def test_unity_import_verifier_reports_editor_failure_log(tmp_path):
    fbx_path = tmp_path / "sample.fbx"
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")
    fake_unity = tmp_path / "fake-unity-fails"
    fake_unity.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
log_path=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -logFile)
      log_path="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
echo "Unity license failure" > "$log_path"
exit 1
""",
        encoding="utf-8",
    )
    fake_unity.chmod(0o755)

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--unity",
            str(fake_unity),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Unity import check failed with exit code 1" in result.stderr
    assert "Unity license failure" in result.stderr
