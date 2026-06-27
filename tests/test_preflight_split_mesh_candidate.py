import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/preflight_split_mesh_candidate.py"


def load_module():
    assert SCRIPT_PATH.exists(), "scripts/preflight_split_mesh_candidate.py is missing"
    spec = importlib.util.spec_from_file_location("preflight_split_mesh_candidate", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_smoke(path: Path, *, mesh_count: int, suggested_category="humanoid", status="pass"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": status,
                "metrics": {
                    "meshCount": mesh_count,
                    "suggestedCategory": suggested_category,
                    "meshNames": ["Body", "Hair"][:mesh_count],
                },
            }
        ),
        encoding="utf-8",
    )


def test_preflight_passes_split_mesh_humanoid_source_smoke(tmp_path):
    module = load_module()
    smoke = tmp_path / "asset-import-smoke.json"
    write_smoke(smoke, mesh_count=2)
    candidate = {
        "id": "kaykit-adventurers",
        "sourceName": "KayKit Adventurers",
        "sourceUrl": "https://example.invalid",
        "license": "CC0",
    }

    result = module.preflight_candidate(candidate, smoke)

    assert result["status"] == "pass"
    assert result["sourceMeshCount"] == 2
    assert result["candidate"]["id"] == "kaykit-adventurers"


def test_preflight_blocks_single_mesh_source_smoke(tmp_path):
    module = load_module()
    smoke = tmp_path / "asset-import-smoke.json"
    write_smoke(smoke, mesh_count=1)
    candidate = {
        "id": "kaykit-adventurers",
        "sourceName": "KayKit Adventurers",
        "sourceUrl": "https://example.invalid",
        "license": "CC0",
    }

    result = module.preflight_candidate(candidate, smoke)

    assert result["status"] == "blocked"
    assert result["issues"] == ["source import mesh count must be > 1"]


def test_cli_json_prefills_candidate_and_blocks_missing_smoke(tmp_path):
    load_module()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--candidate",
            "kaykit-adventurers",
            "--source-smoke",
            str(tmp_path / "missing.json"),
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["candidate"]["id"] == "kaykit-adventurers"
    assert payload["issues"] == ["source import smoke JSON is missing or invalid"]


def test_cli_reports_unknown_candidate_without_traceback(tmp_path):
    load_module()

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--candidate",
            "missing-candidate",
            "--source-smoke",
            str(tmp_path / "asset-import-smoke.json"),
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Candidate not found: missing-candidate" in result.stderr
    assert "Traceback" not in result.stderr
