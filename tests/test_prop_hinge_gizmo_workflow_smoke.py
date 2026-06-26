import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_prop_hinge_gizmo_workflow.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location(
        "verify_prop_hinge_gizmo_workflow",
        SCRIPT_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prop_hinge_gizmo_workflow_script_exposes_evidence_cli():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--output" in result.stdout
    assert "--quiet" in result.stdout


def test_extract_blender_args_reads_options_after_separator():
    module = load_script_module()

    args = module.extract_blender_args(
        [
            "blender",
            "--background",
            "--factory-startup",
            "--python",
            str(SCRIPT_PATH),
            "--",
            "--output",
            "/tmp/prop-hinge-smoke.json",
            "--quiet",
        ]
    )

    assert args == ["--output", "/tmp/prop-hinge-smoke.json", "--quiet"]


def test_build_report_fails_when_any_required_check_fails():
    module = load_script_module()

    report = module.build_report(
        [
            {"name": "addonRegistered", "status": "pass"},
            {"name": "committedLandmarksMatchMovedGuides", "status": "fail"},
        ]
    )

    assert report["status"] == "fail"
    assert report["failedChecks"] == ["committedLandmarksMatchMovedGuides"]
