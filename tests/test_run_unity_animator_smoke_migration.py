import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/run_unity_animator_smoke_migration.py"


def load_module():
    assert SCRIPT_PATH.exists(), "scripts/run_unity_animator_smoke_migration.py is missing"
    spec = importlib.util.spec_from_file_location("run_unity_animator_smoke_migration", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_manifest(tmp_path: Path) -> Path:
    manifest = {
        "slots": [
            {
                "id": "H-003",
                "category": "humanoid",
                "evidence": {
                    "deformationScore": 3,
                    "unityImport": {"status": "pass"},
                    "exportUnityFbx": "evidence/H-003/export-unity.fbx",
                },
            },
            {
                "id": "H-004",
                "category": "humanoid",
                "evidence": {
                    "deformationScore": 3,
                    "unityImport": {"status": "pass"},
                    "exportUnityFbx": "evidence/H-004/export-unity.fbx",
                },
            },
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def write_unity_import_without_configured_smoke(tmp_path: Path, slot_id: str):
    path = tmp_path / "evidence" / slot_id / "unity-import.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": "pass",
                "result": {
                    "boneTransformSmoke": {"passed": True},
                    "animationClipSmoke": {"passed": True},
                },
            }
        ),
        encoding="utf-8",
    )


def test_cli_dry_run_lists_planned_slots_without_running_recorder(tmp_path):
    load_module()
    manifest_path = write_manifest(tmp_path)
    for slot in ("H-003", "H-004"):
        write_unity_import_without_configured_smoke(tmp_path, slot)
    fake_recorder = tmp_path / "fake-recorder"
    fake_recorder.write_text("#!/usr/bin/env bash\nexit 99\n", encoding="utf-8")
    fake_recorder.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest_path),
            "--evidence-root",
            str(tmp_path),
            "--unity",
            "/Fake/Unity",
            "--recorder",
            str(fake_recorder),
            "--skip-preflight",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "DRY RUN" in result.stdout
    assert "H-003" in result.stdout
    assert "H-004" in result.stdout


def test_cli_stops_on_first_recorder_failure(tmp_path):
    load_module()
    manifest_path = write_manifest(tmp_path)
    for slot in ("H-003", "H-004"):
        write_unity_import_without_configured_smoke(tmp_path, slot)
    fake_recorder = tmp_path / "fake-recorder"
    calls_path = tmp_path / "calls.txt"
    fake_recorder.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
echo "$*" >> {calls_path}
echo "Unity licensing/bootstrap failure detected" >&2
exit 124
""",
        encoding="utf-8",
    )
    fake_recorder.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest_path),
            "--evidence-root",
            str(tmp_path),
            "--unity",
            "/Fake/Unity",
            "--recorder",
            str(fake_recorder),
            "--skip-preflight",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 124
    assert "H-003 failed" in result.stderr
    calls = calls_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(calls) == 1
    assert "--fbx evidence/H-003/export-unity.fbx" in calls[0]


def test_cli_runs_all_gaps_when_recorder_succeeds(tmp_path):
    load_module()
    manifest_path = write_manifest(tmp_path)
    for slot in ("H-003", "H-004"):
        write_unity_import_without_configured_smoke(tmp_path, slot)
    fake_recorder = tmp_path / "fake-recorder"
    calls_path = tmp_path / "calls.txt"
    fake_recorder.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
echo "$*" >> {calls_path}
""",
        encoding="utf-8",
    )
    fake_recorder.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest_path),
            "--evidence-root",
            str(tmp_path),
            "--unity",
            "/Fake/Unity",
            "--recorder",
            str(fake_recorder),
            "--skip-preflight",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    calls = calls_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(calls) == 2
    assert "--fbx evidence/H-003/export-unity.fbx" in calls[0]
    assert "--fbx evidence/H-004/export-unity.fbx" in calls[1]


def test_cli_runs_preflight_before_recorders(tmp_path):
    load_module()
    manifest_path = write_manifest(tmp_path)
    write_unity_import_without_configured_smoke(tmp_path, "H-003")
    fake_recorder = tmp_path / "fake-recorder"
    fake_health = tmp_path / "fake-health"
    calls_path = tmp_path / "calls.txt"
    fake_health.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
echo "health:$*" >> {calls_path}
""",
        encoding="utf-8",
    )
    fake_recorder.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
echo "record:$*" >> {calls_path}
""",
        encoding="utf-8",
    )
    fake_health.chmod(0o755)
    fake_recorder.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest_path),
            "--evidence-root",
            str(tmp_path),
            "--unity",
            "/Fake/Unity",
            "--recorder",
            str(fake_recorder),
            "--health-checker",
            str(fake_health),
            "--preflight-timeout-seconds",
            "7",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    calls = calls_path.read_text(encoding="utf-8").strip().splitlines()
    assert calls[0] == (
        "health:--unity /Fake/Unity --timeout-seconds 7 "
        "--output build/unity-batchmode-health.json"
    )
    assert calls[1].startswith("record:--fbx evidence/H-003/export-unity.fbx")


def test_cli_allows_custom_preflight_output_path(tmp_path):
    load_module()
    manifest_path = write_manifest(tmp_path)
    write_unity_import_without_configured_smoke(tmp_path, "H-003")
    fake_recorder = tmp_path / "fake-recorder"
    fake_health = tmp_path / "fake-health"
    calls_path = tmp_path / "calls.txt"
    fake_health.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
echo "health:$*" >> {calls_path}
""",
        encoding="utf-8",
    )
    fake_recorder.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
echo "record:$*" >> {calls_path}
""",
        encoding="utf-8",
    )
    fake_health.chmod(0o755)
    fake_recorder.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest_path),
            "--evidence-root",
            str(tmp_path),
            "--unity",
            "/Fake/Unity",
            "--recorder",
            str(fake_recorder),
            "--health-checker",
            str(fake_health),
            "--preflight-output",
            "reports/unity-health.json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    calls = calls_path.read_text(encoding="utf-8").strip().splitlines()
    assert calls[0] == (
        "health:--unity /Fake/Unity --timeout-seconds 90 "
        "--output reports/unity-health.json"
    )


def test_cli_stops_before_recorders_when_preflight_fails(tmp_path):
    load_module()
    manifest_path = write_manifest(tmp_path)
    write_unity_import_without_configured_smoke(tmp_path, "H-003")
    fake_recorder = tmp_path / "fake-recorder"
    fake_health = tmp_path / "fake-health-fails"
    calls_path = tmp_path / "calls.txt"
    fake_health.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
echo "health:$*" >> {calls_path}
echo "Unity licensing/bootstrap failure detected" >&2
exit 124
""",
        encoding="utf-8",
    )
    fake_recorder.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
echo "record:$*" >> {calls_path}
""",
        encoding="utf-8",
    )
    fake_health.chmod(0o755)
    fake_recorder.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest_path),
            "--evidence-root",
            str(tmp_path),
            "--unity",
            "/Fake/Unity",
            "--recorder",
            str(fake_recorder),
            "--health-checker",
            str(fake_health),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 124
    assert "Unity preflight failed with exit code 124" in result.stderr
    assert calls_path.read_text(encoding="utf-8").strip().startswith("health:")
    assert "record:" not in calls_path.read_text(encoding="utf-8")
