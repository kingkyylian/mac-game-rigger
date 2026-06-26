import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/check_unity_batchmode_health.py"


def load_module():
    assert SCRIPT_PATH.exists(), "scripts/check_unity_batchmode_health.py is missing"
    spec = importlib.util.spec_from_file_location("check_unity_batchmode_health", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_cli_passes_when_unity_batchmode_exits_cleanly(tmp_path):
    load_module()
    fake_unity = tmp_path / "fake-unity-ok"
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
echo "Unity batchmode healthy" > "$log_path"
""",
        encoding="utf-8",
    )
    fake_unity.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--unity",
            str(fake_unity),
            "--timeout-seconds",
            "5",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Unity batchmode health check passed" in result.stdout


def test_cli_classifies_licensing_bootstrap_failure_from_log(tmp_path):
    load_module()
    fake_unity = tmp_path / "fake-unity-licensing-fails"
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
cat > "$log_path" <<'LOG'
[Licensing::Module] Timed-out after 60.00s, waiting for channel: "LicenseClient-kyylian"
[Licensing::Module] Error: 'com.unity.editor.headless' was not found.
LOG
exit 1
""",
        encoding="utf-8",
    )
    fake_unity.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--unity",
            str(fake_unity),
            "--timeout-seconds",
            "5",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Unity batchmode health check failed with exit code 1" in result.stderr
    assert "Unity licensing/bootstrap failure detected" in result.stderr


def test_cli_writes_machine_readable_failure_report(tmp_path):
    load_module()
    fake_unity = tmp_path / "fake-unity-licensing-fails"
    output_path = tmp_path / "unity-health.json"
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
cat > "$log_path" <<'LOG'
[Licensing::Module] Timed-out after 60.00s, waiting for channel: "LicenseClient-kyylian"
[Licensing::Module] Error: 'com.unity.editor.headless' was not found.
LOG
exit 1
""",
        encoding="utf-8",
    )
    fake_unity.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--unity",
            str(fake_unity),
            "--timeout-seconds",
            "5",
            "--output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "fail"
    assert payload["exitCode"] == 1
    assert payload["timedOut"] is False
    assert payload["unity"] == str(fake_unity)
    assert "com.unity.editor.headless" in payload["logTail"]
    assert "Unity licensing/bootstrap failure detected" in payload["hint"]


def test_cli_reports_timeout_with_log_tail(tmp_path):
    load_module()
    fake_unity = tmp_path / "fake-unity-hangs"
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
echo "Unity still initializing" > "$log_path"
sleep 5
""",
        encoding="utf-8",
    )
    fake_unity.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--unity",
            str(fake_unity),
            "--timeout-seconds",
            "1",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 124
    assert "Unity batchmode health check timed out after 1 seconds" in result.stderr
    assert "Unity still initializing" in result.stderr
