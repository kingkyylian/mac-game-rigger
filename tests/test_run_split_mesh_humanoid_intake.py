import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/run_split_mesh_humanoid_intake.py"


def load_module():
    assert SCRIPT_PATH.exists(), "scripts/run_split_mesh_humanoid_intake.py is missing"
    spec = importlib.util.spec_from_file_location("run_split_mesh_humanoid_intake", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_runner_plan_orders_preflight_before_workflow():
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
    candidate = {
        "id": "kaykit-adventurers",
        "sourceName": "KayKit Adventurers",
        "sourceUrl": "https://example.invalid/kaykit",
        "license": "CC0",
    }

    plan = module.build_runner_plan(
        manifest,
        slot_id="H-002",
        asset=Path("local_assets/H-002/kaykit.glb"),
        candidate=candidate,
        source_name="KayKit Adventurers",
        source_url="https://example.invalid/kaykit",
        license_name="CC0",
        blender="blender",
        manifest_path="samples/manifest.json",
        evidence_root=Path("."),
    )

    assert [phase["name"] for phase in plan["phases"]] == [
        "sourceImportSmoke",
        "candidatePreflight",
        "workflow",
    ]
    assert plan["registration"]["status"] == "manual_review_required"
    assert plan["reviewPacket"] == [
        "scripts/create_split_mesh_review_packet.py",
        "--slot",
        "H-002",
        "--source-smoke",
        "evidence/H-002/asset-import-smoke.json",
        "--workflow-summary",
        "evidence/H-002/workflow-summary.json",
        "--output",
        "evidence/H-002/notes.md",
        "--json",
    ]
    assert plan["registration"]["command"][0:3] == [
        "scripts/register_asset_evidence.py",
        "--slot",
        "H-002",
    ]
    assert plan["strictVerifier"] == [
        "scripts/verify_split_mesh_humanoid_evidence.py",
        "--manifest",
        "samples/manifest.json",
        "--evidence-root",
        ".",
        "--slot",
        "H-002",
        "--json",
    ]


def test_build_runner_plan_blocks_non_empty_slot():
    module = load_module()
    manifest = {
        "slots": [
            {
                "id": "H-003",
                "category": "humanoid",
                "realAsset": {"sourceName": "Already Registered"},
                "evidence": {"qaReport": "evidence/H-003/qa-report.json"},
            }
        ],
    }
    candidate = {
        "id": "kaykit-adventurers",
        "sourceName": "KayKit Adventurers",
        "sourceUrl": "https://example.invalid/kaykit",
        "license": "CC0",
    }

    try:
        module.build_runner_plan(
            manifest,
            slot_id="H-003",
            asset=Path("local_assets/H-003/kaykit.glb"),
            candidate=candidate,
            source_name="KayKit Adventurers",
            source_url="https://example.invalid/kaykit",
            license_name="CC0",
            blender="blender",
            manifest_path="samples/manifest.json",
            evidence_root=Path("."),
        )
    except ValueError as exc:
        assert str(exc) == "Slot H-003 is not empty"
    else:
        raise AssertionError("expected non-empty slot to be blocked")


def test_run_phases_stops_before_registration_without_manual_score(tmp_path):
    module = load_module()
    summary_path = tmp_path / "workflow-summary.json"
    summary_path.write_text(json.dumps({"meshCount": 2}), encoding="utf-8")
    plan = {
        "phases": [
            {"name": "sourceImportSmoke", "command": ["fake-source"]},
            {"name": "candidatePreflight", "command": ["fake-preflight"]},
            {"name": "workflow", "command": ["fake-workflow"]},
        ],
        "workflowSummary": str(summary_path),
        "reviewPacket": ["fake-review-packet"],
        "registration": {
            "status": "manual_review_required",
            "command": ["scripts/register_asset_evidence.py", "--slot", "H-002"],
        },
        "strictVerifier": ["scripts/verify_split_mesh_humanoid_evidence.py", "--slot", "H-002", "--json"],
    }
    calls = []

    def fake_runner(command):
        calls.append(command)
        return module.CommandResult(returncode=0, stdout="", stderr="")

    result = module.run_phases(plan, runner=fake_runner)

    assert calls == [["fake-source"], ["fake-preflight"], ["fake-workflow"], ["fake-review-packet"]]
    assert result["status"] == "needs_registration_review"
    assert result["reviewPacket"]["returncode"] == 0
    assert result["registrationCommand"] == ["scripts/register_asset_evidence.py", "--slot", "H-002"]
    assert result["nextCommand"] == ["scripts/verify_split_mesh_humanoid_evidence.py", "--slot", "H-002", "--json"]


def test_run_phases_blocks_when_workflow_mesh_count_collapses_to_single_mesh(tmp_path):
    module = load_module()
    summary_path = tmp_path / "workflow-summary.json"
    summary_path.write_text(json.dumps({"meshCount": 1}), encoding="utf-8")
    plan = {
        "phases": [
            {"name": "sourceImportSmoke", "command": ["fake-source"]},
            {"name": "candidatePreflight", "command": ["fake-preflight"]},
            {"name": "workflow", "command": ["fake-workflow"]},
        ],
        "workflowSummary": str(summary_path),
        "reviewPacket": ["fake-review-packet"],
        "registration": {
            "status": "manual_review_required",
            "command": ["scripts/register_asset_evidence.py", "--slot", "H-002"],
        },
        "strictVerifier": ["scripts/verify_split_mesh_humanoid_evidence.py", "--slot", "H-002", "--json"],
    }

    result = module.run_phases(
        plan,
        runner=lambda command: module.CommandResult(returncode=0, stdout="", stderr=""),
    )

    assert result["status"] == "blocked"
    assert result["failedPhase"] == "workflowSplitMeshCheck"
    assert result["issues"] == ["rig workflow mesh count must be > 1"]
    assert result["registrationCommand"] == ["scripts/register_asset_evidence.py", "--slot", "H-002"]


def test_run_phases_fails_when_review_packet_generation_fails(tmp_path):
    module = load_module()
    summary_path = tmp_path / "workflow-summary.json"
    summary_path.write_text(json.dumps({"meshCount": 2}), encoding="utf-8")
    plan = {
        "phases": [
            {"name": "sourceImportSmoke", "command": ["fake-source"]},
            {"name": "candidatePreflight", "command": ["fake-preflight"]},
            {"name": "workflow", "command": ["fake-workflow"]},
        ],
        "workflowSummary": str(summary_path),
        "reviewPacket": ["fake-review-packet"],
        "registration": {
            "status": "manual_review_required",
            "command": ["scripts/register_asset_evidence.py", "--slot", "H-002"],
        },
        "strictVerifier": ["scripts/verify_split_mesh_humanoid_evidence.py", "--slot", "H-002", "--json"],
    }

    def fake_runner(command):
        if command == ["fake-review-packet"]:
            return module.CommandResult(returncode=2, stdout="", stderr="Output already exists")
        return module.CommandResult(returncode=0, stdout="", stderr="")

    result = module.run_phases(plan, runner=fake_runner)

    assert result["status"] == "failed"
    assert result["failedPhase"] == "reviewPacket"
    assert result["reviewPacket"]["stderr"] == "Output already exists"


def test_cli_dry_run_json_outputs_runner_plan():
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
            "--dry-run",
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
    assert payload["workflowSummary"] == "evidence/H-002/workflow-summary.json"
    assert payload["reviewPacket"][0] == "scripts/create_split_mesh_review_packet.py"
    assert [phase["name"] for phase in payload["phases"]] == [
        "sourceImportSmoke",
        "candidatePreflight",
        "workflow",
    ]
    assert payload["registration"]["status"] == "manual_review_required"


def test_cli_reports_non_empty_slot_without_traceback():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manifest",
            "samples/manifest.json",
            "--candidate",
            "kaykit-adventurers",
            "--slot",
            "H-003",
            "--asset",
            "local_assets/H-003/kaykit.glb",
            "--dry-run",
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Slot H-003 is not empty" in result.stderr
    assert "Traceback" not in result.stderr
