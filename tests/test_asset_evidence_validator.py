import copy
import json
from pathlib import Path
import subprocess
import struct
import zlib


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_asset_evidence.py"
MANIFEST_PATH = REPO_ROOT / "samples" / "manifest.json"


def load_base_manifest():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def clear_registered_assets(manifest):
    for slot in manifest["slots"]:
        slot["realAsset"] = None
        slot["evidence"] = {}
    return manifest


def write_manifest(tmp_path, manifest):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def mark_complete(slot, *, score=4, unity="pass", unreal=None):
    slot["realAsset"] = {
        "sourceName": f"{slot['id']} sample",
        "sourceUrl": "https://example.invalid/sample",
        "license": "internal-test",
        "canCommitBinary": False,
        "externalPath": f"/external/assets/{slot['targetFilename']}",
    }
    evidence = {
        "qaReport": f"evidence/{slot['id']}/qa-report.json",
        "previewNeutral": f"evidence/{slot['id']}/preview-neutral.png",
        "exportUnityFbx": f"evidence/{slot['id']}/export-unity.fbx",
        "notes": f"evidence/{slot['id']}/notes.md",
        "deformationScore": score,
        "unityImport": {"status": unity},
    }
    if unreal is not None:
        evidence["unrealImport"] = {"status": unreal}
    slot["evidence"] = evidence


def write_test_png(path, rows):
    height = len(rows)
    width = len(rows[0])
    raw = b"".join(b"\x00" + bytes(row) for row in rows)

    def chunk(kind, payload):
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def create_evidence_files(evidence_root, slot):
    evidence = slot["evidence"]
    for key in ("qaReport", "exportUnityFbx", "notes"):
        path = evidence_root / evidence[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{slot['id']} {key}\n", encoding="utf-8")
    write_test_png(
        evidence_root / evidence["previewNeutral"],
        rows=[
            [30, 30, 30, 220],
            [30, 220, 220, 30],
            [30, 220, 220, 30],
            [30, 30, 30, 220],
        ],
    )


def run_validator(manifest_path, *args):
    return subprocess.run(
        [str(SCRIPT_PATH), "--manifest", str(manifest_path), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_asset_evidence_validator_allows_empty_manifest_but_blocks_trial(tmp_path):
    manifest_path = write_manifest(tmp_path, clear_registered_assets(load_base_manifest()))

    result = run_validator(manifest_path)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schemaStatus"] == "pass"
    assert payload["realAssetCount"] == 0
    assert payload["productionTrialGate"]["status"] == "blocked"


def test_asset_evidence_validator_require_trial_exits_nonzero_when_gate_missing(tmp_path):
    manifest_path = write_manifest(tmp_path, clear_registered_assets(load_base_manifest()))

    result = run_validator(manifest_path, "--require-production-trial")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert "completeRealAssetsAtLeast10" in payload["productionTrialGate"]["missing"]


def test_asset_evidence_validator_reports_incomplete_real_asset(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    slot["realAsset"] = {
        "sourceName": "Incomplete sample",
        "sourceUrl": "https://example.invalid/sample",
        "license": "internal-test",
        "canCommitBinary": False,
        "externalPath": "/external/assets/sample.glb",
    }
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_validator(manifest_path)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schemaStatus"] == "pass"
    assert payload["realAssetCount"] == 1
    assert payload["completeEvidenceCount"] == 0
    issues = payload["incompleteRealAssets"][0]["issues"]
    assert any("deformationScore" in issue for issue in issues)
    assert any("QA report" in issue for issue in issues)


def test_asset_evidence_validator_fails_bad_real_asset_schema(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    manifest["slots"][0]["realAsset"] = {"sourceName": "Bad sample"}
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_validator(manifest_path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["schemaStatus"] == "fail"
    assert any("realAsset.license" in issue for issue in payload["structuralIssues"])


def test_asset_evidence_validator_passes_production_trial_gate(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    required_ids = {
        "H-001",
        "H-002",
        "H-003",
        "H-006",
        "H-009",
        "H-010",
        "Q-001",
        "Q-002",
        "C-001",
        "P-001",
    }
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] in required_ids:
            mark_complete(
                next_slot,
                score=4,
                unity="pass" if slot["id"] in {"H-001", "H-002", "Q-001"} else "not tested",
                unreal="blocked" if slot["id"] == "H-001" else None,
            )
            create_evidence_files(tmp_path, next_slot)
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_validator(
        manifest_path,
        "--evidence-root",
        str(tmp_path),
        "--require-production-trial",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["productionTrialGate"]["status"] == "pass"
    assert payload["productionTrialGate"]["completeRealAssetCount"] == 10
    assert payload["productionTrialGate"]["requirements"]["unityImportPassesAtLeast3"] is True
    assert payload["productionTrialGate"]["requirements"]["unrealPassOrExplicitBlocker"] is True


def test_asset_evidence_validator_require_trial_fails_missing_evidence_files(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    required_ids = {
        "H-001",
        "H-002",
        "H-003",
        "H-006",
        "H-009",
        "H-010",
        "Q-001",
        "Q-002",
        "C-001",
        "P-001",
    }
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] in required_ids:
            mark_complete(
                next_slot,
                score=4,
                unity="pass" if slot["id"] in {"H-001", "H-002", "Q-001"} else "not tested",
                unreal="blocked" if slot["id"] == "H-001" else None,
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_validator(
        manifest_path,
        "--evidence-root",
        str(tmp_path),
        "--require-production-trial",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["evidenceFileCheck"] == "enabled"
    incomplete = payload["incompleteRealAssets"]
    assert incomplete
    assert any("file not found" in issue for slot in incomplete for issue in slot["issues"])


def test_asset_evidence_validator_rejects_blank_preview_png(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=4, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_test_png(
        tmp_path / slot["evidence"]["previewNeutral"],
        rows=[
            [80, 80, 80, 80],
            [80, 80, 80, 80],
            [80, 80, 80, 80],
            [80, 80, 80, 80],
        ],
    )
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_validator(
        manifest_path,
        "--evidence-root",
        str(tmp_path),
        "--check-evidence-files",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    incomplete = payload["incompleteRealAssets"]
    assert incomplete
    assert any("preview image appears blank" in issue for issue in incomplete[0]["issues"])
