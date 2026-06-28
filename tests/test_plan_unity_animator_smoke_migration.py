import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/plan_unity_animator_smoke_migration.py"


def load_module():
    assert SCRIPT_PATH.exists(), "scripts/plan_unity_animator_smoke_migration.py is missing"
    spec = importlib.util.spec_from_file_location("plan_unity_animator_smoke_migration", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_unity_import(path: Path, *, configured: bool):
    result = {
        "status": "pass",
        "result": {
            "boneTransformSmoke": {"passed": True},
            "animationClipSmoke": {"passed": True},
        },
    }
    if configured:
        result["result"]["configuredAnimatorSmoke"] = {"passed": True}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result), encoding="utf-8")


def test_find_migration_gaps_returns_only_score3_humanoid_unity_passes_missing_configured_smoke(tmp_path):
    module = load_module()
    manifest = {
        "slots": [
            {
                "id": "H-001",
                "category": "humanoid",
                "evidence": {
                    "deformationScore": 2,
                    "unityImport": {"status": "pass"},
                    "exportUnityFbx": "evidence/H-001/export-unity.fbx",
                },
            },
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
                "id": "H-006",
                "category": "humanoid",
                "evidence": {
                    "deformationScore": 3,
                    "unityImport": {"status": "pass"},
                    "exportUnityFbx": "evidence/H-006/export-unity.fbx",
                },
            },
            {
                "id": "Q-001",
                "category": "quadruped",
                "evidence": {
                    "deformationScore": 3,
                    "unityImport": {"status": "pass"},
                    "exportUnityFbx": "evidence/Q-001/export-unity.fbx",
                },
            },
        ],
    }
    write_unity_import(tmp_path / "evidence/H-003/unity-import.json", configured=False)
    write_unity_import(tmp_path / "evidence/H-006/unity-import.json", configured=True)
    write_unity_import(tmp_path / "evidence/Q-001/unity-import.json", configured=False)

    gaps = module.find_migration_gaps(manifest, tmp_path)

    assert [gap["slot"] for gap in gaps] == ["H-003"]
    assert gaps[0]["fbx"] == "evidence/H-003/export-unity.fbx"


def test_cli_json_reports_no_gaps_for_current_manifest():
    load_module()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            "samples/manifest.json",
            "--evidence-root",
            ".",
            "--unity",
            "/Fake/Unity",
            "--timeout-seconds",
            "240",
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {"gaps": []}


def test_cli_text_reports_no_gaps_for_current_manifest():
    load_module()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            "samples/manifest.json",
            "--evidence-root",
            ".",
            "--unity",
            "/Fake/Unity",
            "--timeout-seconds",
            "240",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "No configured Animator smoke migration gaps found.\n"
