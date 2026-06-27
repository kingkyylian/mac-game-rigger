import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/create_split_mesh_review_packet.py"


def load_module():
    assert SCRIPT_PATH.exists(), "scripts/create_split_mesh_review_packet.py is missing"
    spec = importlib.util.spec_from_file_location("create_split_mesh_review_packet", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_review_packet_requires_source_and_rig_split_mesh(tmp_path):
    module = load_module()
    source_smoke = tmp_path / "asset-import-smoke.json"
    workflow_summary = tmp_path / "workflow-summary.json"
    write_json(
        source_smoke,
        {
            "source": {
                "name": "KayKit Adventurers",
                "url": "https://example.invalid/kaykit",
                "license": "CC0",
                "localPath": "/assets/kaykit.glb",
            },
            "metrics": {"meshCount": 3, "suggestedCategory": "humanoid"},
        },
    )
    write_json(workflow_summary, {"meshCount": 2, "qa": {"status": "pass"}, "poseDeformation": {"status": "pass"}})

    result = module.build_review_packet(
        slot_id="H-002",
        source_smoke=source_smoke,
        workflow_summary=workflow_summary,
    )

    assert result["status"] == "pass"
    assert result["sourceMeshCount"] == 3
    assert result["rigMeshCount"] == 2
    assert "# H-002 Split-Mesh Humanoid Review Packet" in result["markdown"]
    assert "Manual review status: not reviewed" in result["markdown"]
    assert "Do not register this slot until deformation score and visual review are set manually." in result["markdown"]


def test_build_review_packet_blocks_single_mesh_workflow(tmp_path):
    module = load_module()
    source_smoke = tmp_path / "asset-import-smoke.json"
    workflow_summary = tmp_path / "workflow-summary.json"
    write_json(source_smoke, {"metrics": {"meshCount": 2, "suggestedCategory": "humanoid"}})
    write_json(workflow_summary, {"meshCount": 1})

    result = module.build_review_packet(
        slot_id="H-002",
        source_smoke=source_smoke,
        workflow_summary=workflow_summary,
    )

    assert result["status"] == "blocked"
    assert result["issues"] == ["rig workflow mesh count must be > 1"]
    assert result["markdown"] is None


def test_cli_writes_review_packet_without_overwriting(tmp_path):
    source_smoke = tmp_path / "asset-import-smoke.json"
    workflow_summary = tmp_path / "workflow-summary.json"
    output = tmp_path / "notes.md"
    write_json(
        source_smoke,
        {
            "source": {"name": "KayKit Adventurers", "url": "https://example.invalid/kaykit", "license": "CC0"},
            "metrics": {"meshCount": 2, "suggestedCategory": "humanoid"},
        },
    )
    write_json(workflow_summary, {"meshCount": 2})

    first = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--slot",
            "H-002",
            "--source-smoke",
            str(source_smoke),
            "--workflow-summary",
            str(workflow_summary),
            "--output",
            str(output),
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    second = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--slot",
            "H-002",
            "--source-smoke",
            str(source_smoke),
            "--workflow-summary",
            str(workflow_summary),
            "--output",
            str(output),
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert first.returncode == 0, first.stderr
    assert json.loads(first.stdout)["status"] == "pass"
    assert output.read_text(encoding="utf-8").startswith("# H-002 Split-Mesh Humanoid Review Packet")
    assert second.returncode == 2
    assert "Output already exists" in second.stderr
