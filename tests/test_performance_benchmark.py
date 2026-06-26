import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/run_performance_benchmark.py"


def test_performance_benchmark_writes_capsule_weight_json_report(tmp_path):
    output_path = tmp_path / "performance.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--vertex-count",
            "64",
            "--vertex-count",
            "128",
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
    assert payload["benchmark"] == "capsule_weight_binding"
    assert payload["status"] == "pass"
    assert [case["vertexCount"] for case in payload["cases"]] == [64, 128]
    for case in payload["cases"]:
        assert case["status"] == "pass"
        assert case["boneCount"] >= 10
        assert case["weightedVertices"] == case["vertexCount"]
        assert case["durationSeconds"] >= 0
        assert case["verticesPerSecond"] > 0


def test_performance_benchmark_fails_when_case_exceeds_runtime_budget(tmp_path):
    output_path = tmp_path / "performance.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--vertex-count",
            "64",
            "--output",
            str(output_path),
            "--max-seconds-per-case",
            "0",
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
