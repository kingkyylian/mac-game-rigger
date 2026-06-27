import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/verify_split_mesh_humanoid_evidence.py"


def load_module():
    assert SCRIPT_PATH.exists(), "scripts/verify_split_mesh_humanoid_evidence.py is missing"
    spec = importlib.util.spec_from_file_location("verify_split_mesh_humanoid_evidence", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def manifest_for(score=3):
    return {
        "slots": [
            {
                "id": "H-002",
                "category": "humanoid",
                "realAsset": {"sourceName": "Split Character"},
                "evidence": {
                    "deformationScore": score,
                    "visualReview": {"status": "pass"},
                },
            }
        ]
    }


def write_mesh_evidence(root: Path, slot_id: str, *, source_mesh_count: int, rig_mesh_count: int):
    write_json(
        root / f"evidence/{slot_id}/asset-import-smoke.json",
        {"status": "pass", "metrics": {"meshCount": source_mesh_count}},
    )
    write_json(
        root / f"evidence/{slot_id}/workflow-summary.json",
        {"status": "pass", "meshCount": rig_mesh_count},
    )


def test_verify_slot_passes_when_source_and_rig_are_split_mesh(tmp_path):
    module = load_module()
    manifest = manifest_for(score=3)
    write_mesh_evidence(tmp_path, "H-002", source_mesh_count=2, rig_mesh_count=2)

    result = module.verify_slots(manifest, tmp_path, slot_id="H-002")

    assert result["status"] == "pass"
    assert result["passingSlots"] == ["H-002"]


def test_verify_slot_blocks_single_mesh_source_even_when_workflow_is_split(tmp_path):
    module = load_module()
    manifest = manifest_for(score=3)
    write_mesh_evidence(tmp_path, "H-002", source_mesh_count=1, rig_mesh_count=2)

    result = module.verify_slots(manifest, tmp_path, slot_id="H-002")

    assert result["status"] == "blocked"
    assert result["slotResults"][0]["issues"] == ["source import mesh count must be > 1"]


def test_cli_json_passes_current_manifest_after_real_split_mesh_evidence_exists():
    load_module()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            "samples/manifest.json",
            "--evidence-root",
            ".",
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert "H-002" in payload["passingSlots"]
