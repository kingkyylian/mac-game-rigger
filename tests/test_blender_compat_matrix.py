import json
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_blender_compat_matrix.py"


def write_fake_blender(path: Path, *, fail_tests: bool = False) -> None:
    test_exit = "exit 7" if fail_tests else "exit 0"
    path.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
if [ "${{1:-}}" = "--version" ]; then
  cat <<'VERSION'
Blender 4.2.11 LTS
\tbuild platform: Darwin
VERSION
  exit 0
fi
if [ "${{1:-}}" = "--background" ]; then
  echo "fake blender ran $4"
  {test_exit}
fi
echo "unexpected args: $*" >&2
exit 64
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_blender_compat_matrix_reports_blocked_without_blender(tmp_path):
    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--blender",
            str(tmp_path / "missing-blender"),
            "--skip-tests",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["reason"] == "no_blender_executable_found"


def test_blender_compat_matrix_collects_version_without_tests(tmp_path):
    fake_blender = tmp_path / "fake-blender"
    write_fake_blender(fake_blender)

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--blender",
            str(fake_blender),
            "--skip-tests",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["blenders"][0]["version"]["versionLine"] == "Blender 4.2.11 LTS"
    assert payload["blenders"][0]["version"]["platformLine"] == "build platform: Darwin"
    assert payload["blenders"][0]["tests"] == []


def test_blender_compat_matrix_runs_requested_tests(tmp_path):
    fake_blender = tmp_path / "fake-blender"
    write_fake_blender(fake_blender)
    test_dir = tmp_path / "blender_tests"
    test_dir.mkdir()
    test_file = test_dir / "test_sample.py"
    test_file.write_text("print('sample')\n", encoding="utf-8")

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--blender",
            str(fake_blender),
            "--test-glob",
            str(test_file),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    test_result = payload["blenders"][0]["tests"][0]
    assert test_result["path"] == str(test_file)
    assert test_result["status"] == "pass"
    assert "fake blender ran" in test_result["stdoutTail"]


def test_blender_compat_matrix_fails_when_a_test_fails(tmp_path):
    fake_blender = tmp_path / "fake-blender"
    write_fake_blender(fake_blender, fail_tests=True)
    test_dir = tmp_path / "blender_tests"
    test_dir.mkdir()
    test_file = test_dir / "test_sample.py"
    test_file.write_text("print('sample')\n", encoding="utf-8")

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--blender",
            str(fake_blender),
            "--test-glob",
            str(test_file),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "fail"
    assert payload["blenders"][0]["tests"][0]["status"] == "fail"
