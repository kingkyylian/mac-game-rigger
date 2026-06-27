import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/plan_split_mesh_humanoid_intake.py"


def load_module():
    assert SCRIPT_PATH.exists(), "scripts/plan_split_mesh_humanoid_intake.py is missing"
    spec = importlib.util.spec_from_file_location("plan_split_mesh_humanoid_intake", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_find_open_humanoid_slots_prefers_empty_humanoid_slots():
    module = load_module()
    manifest = {
        "slots": [
            {"id": "H-001", "category": "humanoid", "realAsset": {"sourceName": "used"}, "evidence": {}},
            {"id": "H-002", "category": "humanoid", "realAsset": None, "evidence": {}},
            {"id": "Q-001", "category": "quadruped", "realAsset": None, "evidence": {}},
            {"id": "H-003", "category": "humanoid", "realAsset": None, "evidence": {"qaReport": "x"}},
        ],
    }

    slots = module.find_open_humanoid_slots(manifest)

    assert [slot["id"] for slot in slots] == ["H-002"]


def test_build_intake_plan_includes_source_smoke_workflow_and_register_commands():
    module = load_module()
    manifest = {
        "slots": [
            {
                "id": "H-002",
                "category": "humanoid",
                "realAsset": None,
                "evidence": {},
            }
        ],
    }

    plan = module.build_intake_plan(
        manifest,
        slot_id="H-002",
        asset=Path("local_assets/H-002/split-character.glb"),
        source_name="Split Character",
        source_url="https://example.invalid/split-character",
        license_name="CC0",
        blender="blender",
        manifest_path="custom/manifest.json",
    )

    assert plan["slot"] == "H-002"
    assert plan["asset"] == "local_assets/H-002/split-character.glb"
    assert plan["commands"]["sourceImportSmoke"][:6] == [
        "blender",
        "--background",
        "--factory-startup",
        "--python",
        "tools/blender_asset_import_smoke.py",
        "--",
    ]
    assert plan["commands"]["workflow"][0:6] == [
        "blender",
        "--background",
        "--factory-startup",
        "--python",
        "tools/blender_asset_workflow.py",
        "--",
    ]
    assert plan["commands"]["registerEvidence"][0:4] == [
        "scripts/register_asset_evidence.py",
        "--slot",
        "H-002",
        "--source-name",
    ]
    assert plan["commands"]["generateEvidenceReport"][1:3] == ["--manifest", "custom/manifest.json"]
    assert plan["acceptance"]["sourceImportMeshCount"] == ">1"
    assert plan["acceptance"]["rigWorkflowMeshCount"] == ">1"


def test_load_candidate_registry_and_apply_candidate_defaults():
    module = load_module()

    candidates = module.load_candidate_registry(REPO_ROOT / "samples/split_mesh_humanoid_candidates.json")
    candidate = module.find_candidate(candidates, "kaykit-adventurers")

    assert candidate["sourceName"] == "KayKit Adventurers"
    assert candidate["license"] == "CC0"
    assert "GLTF" in candidate["formats"]


def test_cli_candidate_prefills_source_metadata_for_asset_plan():
    load_module()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            "samples/manifest.json",
            "--candidate",
            "kaykit-adventurers",
            "--asset",
            "local_assets/H-002/kaykit-adventurer.glb",
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["candidate"]["id"] == "kaykit-adventurers"
    assert payload["commands"]["candidatePreflight"] == [
        "scripts/preflight_split_mesh_candidate.py",
        "--candidate",
        "kaykit-adventurers",
        "--source-smoke",
        "evidence/H-007/asset-import-smoke.json",
        "--json",
    ]
    assert "--source-name" in payload["commands"]["sourceImportSmoke"]
    assert "KayKit Adventurers" in payload["commands"]["sourceImportSmoke"]
    assert "--license" in payload["commands"]["sourceImportSmoke"]
    assert "CC0" in payload["commands"]["sourceImportSmoke"]


def test_cli_json_reports_current_open_humanoid_slots_without_asset():
    load_module()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            "samples/manifest.json",
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "needs_asset"
    assert payload["openHumanoidSlots"] == ["H-007", "H-008"]
    assert payload["recommendedSlot"] == "H-007"
