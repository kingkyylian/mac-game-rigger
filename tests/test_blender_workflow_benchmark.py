import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/run_blender_workflow_benchmark.py"


def write_fake_blender(path: Path, *, exit_code: int = 0) -> None:
    path.write_text(
        f"""#!/usr/bin/env python3
import json
from pathlib import Path
import sys

args = sys.argv
script_args = args[args.index("--") + 1:] if "--" in args else []
def value_after(flag):
    return script_args[script_args.index(flag) + 1]

summary_path = Path(value_after("--summary"))
asset_path = Path(value_after("--asset"))
vertex_count = 0
if asset_path.exists():
    if asset_path.suffix == ".gltf":
        payload = json.loads(asset_path.read_text(encoding="utf-8"))
        vertex_count = sum(
            accessor["count"]
            for accessor in payload.get("accessors", [])
            if accessor.get("type") == "VEC3"
        )
    else:
        vertex_count = sum(
            1
            for line in asset_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.startswith("v ")
        )
summary_path.parent.mkdir(parents=True, exist_ok=True)
summary_path.write_text(json.dumps({{
    "schemaVersion": 1,
    "status": "pass",
    "template": value_after("--template"),
    "assetPath": value_after("--asset"),
    "meshCount": 1,
    "poseDeformation": {{"status": "pass"}},
    "qa": {{
        "vertex_count": vertex_count,
        "unweighted_vertices": 0,
        "over_limit_vertices": 0,
        "warnings": [],
        "errors": []
    }},
    "artifacts": {{"exportUnityFbx": str(summary_path.parent / "export-unity.fbx")}}
}}) + "\\n", encoding="utf-8")
print(json.dumps({{"status": "pass", "summary": str(summary_path)}}))
raise SystemExit({exit_code})
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_blender_workflow_benchmark_writes_report_for_successful_case(tmp_path):
    fake_blender = tmp_path / "fake_blender.py"
    write_fake_blender(fake_blender)
    asset_path = tmp_path / "character.fbx"
    asset_path.write_text("fake asset", encoding="utf-8")
    output_path = tmp_path / "workflow-benchmark.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--blender",
            str(fake_blender),
            "--asset",
            str(asset_path),
            "--template",
            "humanoid",
            "--evidence-root",
            str(tmp_path / "evidence"),
            "--output",
            str(output_path),
            "--max-seconds-per-case",
            "10",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == 1
    assert payload["benchmark"] == "blender_asset_workflow"
    assert payload["status"] == "pass"
    assert len(payload["cases"]) == 1
    case = payload["cases"][0]
    assert case["status"] == "pass"
    assert case["asset"] == str(asset_path)
    assert case["template"] == "humanoid"
    assert case["exitCode"] == 0
    assert case["durationSeconds"] >= 0
    assert case["summaryExists"] is True
    assert case["workflowSummary"]["poseDeformationStatus"] == "pass"
    assert case["workflowSummary"]["qa"]["unweighted_vertices"] == 0
    assert Path(case["evidenceDir"]).exists()


def test_blender_workflow_benchmark_fails_when_blender_case_fails(tmp_path):
    fake_blender = tmp_path / "fake_blender.py"
    write_fake_blender(fake_blender, exit_code=9)
    asset_path = tmp_path / "character.fbx"
    asset_path.write_text("fake asset", encoding="utf-8")
    output_path = tmp_path / "workflow-benchmark.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--blender",
            str(fake_blender),
            "--asset",
            str(asset_path),
            "--evidence-root",
            str(tmp_path / "evidence"),
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
    assert payload["cases"][0]["status"] == "fail"
    assert payload["cases"][0]["exitCode"] == 9


def test_blender_workflow_benchmark_generates_synthetic_humanoid_cases(tmp_path):
    fake_blender = tmp_path / "fake_blender.py"
    write_fake_blender(fake_blender)
    output_path = tmp_path / "workflow-benchmark.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--blender",
            str(fake_blender),
            "--synthetic-humanoid-vertices",
            "10000",
            "--synthetic-humanoid-vertices",
            "50000",
            "--synthetic-humanoid-vertices",
            "100000",
            "--evidence-root",
            str(tmp_path / "evidence"),
            "--output",
            str(output_path),
            "--max-seconds-per-case",
            "10",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert [case["syntheticSpec"]["vertexCount"] for case in payload["cases"]] == [
        10000,
        50000,
        100000,
    ]
    for case in payload["cases"]:
        asset_path = Path(case["asset"])
        assert asset_path.exists()
        assert asset_path.suffix == ".obj"
        assert case["template"] == "humanoid"
        assert case["workflowSummary"]["qa"]["vertex_count"] == case["syntheticSpec"]["vertexCount"]


def test_blender_workflow_benchmark_generates_synthetic_template_family_cases(tmp_path):
    fake_blender = tmp_path / "fake_blender.py"
    write_fake_blender(fake_blender)
    output_path = tmp_path / "workflow-benchmark.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--blender",
            str(fake_blender),
            "--synthetic-multimesh-humanoid-vertices",
            "240",
            "--synthetic-quadruped-vertices",
            "300",
            "--synthetic-tail-creature-vertices",
            "360",
            "--synthetic-prop-hinge-vertices",
            "180",
            "--evidence-root",
            str(tmp_path / "evidence"),
            "--output",
            str(output_path),
            "--max-seconds-per-case",
            "10",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    cases = payload["cases"]
    assert [case["template"] for case in cases] == [
        "humanoid",
        "quadruped",
        "tail_creature",
        "prop_hinge",
    ]
    assert [case["syntheticSpec"]["type"] for case in cases] == [
        "synthetic_multimesh_humanoid",
        "synthetic_quadruped",
        "synthetic_tail_creature",
        "synthetic_prop_hinge",
    ]
    assert [case["syntheticSpec"]["vertexCount"] for case in cases] == [240, 300, 360, 180]
    assert cases[0]["syntheticSpec"]["meshCount"] > 1
    for case in cases:
        assert Path(case["asset"]).exists()
        assert case["workflowSummary"]["qa"]["vertex_count"] == case["syntheticSpec"]["vertexCount"]
