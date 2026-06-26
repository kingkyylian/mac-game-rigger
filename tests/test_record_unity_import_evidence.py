import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/record_unity_import_evidence.py"


def load_module():
    assert SCRIPT_PATH.exists(), "scripts/record_unity_import_evidence.py is missing"
    spec = importlib.util.spec_from_file_location("record_unity_import_evidence", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_default_output_path_uses_fbx_slot_directory():
    module = load_module()

    output_path = module.default_output_path(Path("evidence/H-003/export-unity.fbx"))

    assert output_path == Path("evidence/H-003/unity-import.json")


def test_wrap_unity_import_result_preserves_verifier_payload_and_metadata():
    module = load_module()
    verifier_payload = {
        "status": "pass",
        "configuredAnimatorSmoke": {
            "passed": True,
            "sampledBone": "Hips",
        },
    }

    wrapped = module.wrap_unity_import_result(
        verifier_payload,
        checked_on="2026-06-25",
        unity_editor="/Applications/Unity/Unity",
        fbx=Path("evidence/H-003/export-unity.fbx"),
        verification_command=[
            "scripts/verify_unity_fbx_import.sh",
            "--fbx",
            "evidence/H-003/export-unity.fbx",
            "--unity",
            "/Applications/Unity/Unity",
            "--timeout-seconds",
            "240",
        ],
    )

    assert wrapped == {
        "schemaVersion": 1,
        "status": "pass",
        "checkedOn": "2026-06-25",
        "unityEditor": "/Applications/Unity/Unity",
        "fbx": "evidence/H-003/export-unity.fbx",
        "verificationCommand": (
            "scripts/verify_unity_fbx_import.sh --fbx evidence/H-003/export-unity.fbx "
            "--unity /Applications/Unity/Unity --timeout-seconds 240"
        ),
        "result": verifier_payload,
    }


def test_cli_runs_verifier_and_writes_wrapped_unity_import_evidence(tmp_path):
    load_module()
    fbx_path = tmp_path / "evidence/H-003/export-unity.fbx"
    fbx_path.parent.mkdir(parents=True)
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")
    verifier = tmp_path / "fake-verify-unity"
    verifier.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '{"status":"pass","configuredAnimatorSmoke":{"passed":true}}'
""",
        encoding="utf-8",
    )
    verifier.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--unity",
            "/Fake/Unity",
            "--timeout-seconds",
            "240",
            "--verifier",
            str(verifier),
            "--checked-on",
            "2026-06-25",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    output_path = tmp_path / "evidence/H-003/unity-import.json"
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == 1
    assert payload["status"] == "pass"
    assert payload["checkedOn"] == "2026-06-25"
    assert payload["unityEditor"] == "/Fake/Unity"
    assert payload["fbx"] == str(fbx_path)
    assert payload["verificationCommand"] == (
        f"{verifier} --fbx {fbx_path} --unity /Fake/Unity --timeout-seconds 240"
    )
    assert payload["result"]["configuredAnimatorSmoke"]["passed"] is True


def test_cli_preserves_existing_evidence_when_verifier_fails(tmp_path):
    load_module()
    fbx_path = tmp_path / "evidence/H-003/export-unity.fbx"
    fbx_path.parent.mkdir(parents=True)
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")
    output_path = tmp_path / "evidence/H-003/unity-import.json"
    output_path.write_text('{"status":"pass"}\n', encoding="utf-8")
    verifier = tmp_path / "fake-verify-unity-fails"
    verifier.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
echo "Unity license unavailable" >&2
exit 1
""",
        encoding="utf-8",
    )
    verifier.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--unity",
            "/Fake/Unity",
            "--verifier",
            str(verifier),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Unity license unavailable" in result.stderr
    assert output_path.read_text(encoding="utf-8") == '{"status":"pass"}\n'


def test_cli_classifies_unity_licensing_bootstrap_failures(tmp_path):
    load_module()
    fbx_path = tmp_path / "evidence/H-003/export-unity.fbx"
    fbx_path.parent.mkdir(parents=True)
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")
    verifier = tmp_path / "fake-verify-unity-licensing-fails"
    verifier.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
cat >&2 <<'LOG'
Unity import check timed out after 240 seconds
[Licensing::Module] Timed-out after 60.00s, waiting for channel: "LicenseClient-kyylian"
[Licensing::Module] Error: 'com.unity.editor.headless' was not found.
LOG
exit 124
""",
        encoding="utf-8",
    )
    verifier.chmod(0o755)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--unity",
            "/Fake/Unity",
            "--verifier",
            str(verifier),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 124
    assert "Unity licensing/bootstrap failure detected" in result.stderr
    assert "Open Unity Hub or the Unity Editor once to refresh licensing" in result.stderr
