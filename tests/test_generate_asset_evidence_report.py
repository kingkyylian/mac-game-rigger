import copy
import json
from pathlib import Path
import subprocess
import struct
import zlib


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_asset_evidence_report.py"
BASE_MANIFEST = REPO_ROOT / "samples" / "manifest.json"


def load_manifest():
    return json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))


def clear_registered_assets(manifest):
    for slot in manifest["slots"]:
        slot["realAsset"] = None
        slot["evidence"] = {}
    return manifest


def write_manifest(tmp_path, manifest):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def write_test_png(path):
    rows = [
        [30, 30, 30, 220],
        [30, 220, 220, 30],
        [30, 220, 220, 30],
        [30, 30, 30, 220],
    ]
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


def mark_complete(slot, evidence_root, *, score=4, unity="pass", unreal="blocked"):
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
        "unrealImport": {"status": unreal},
    }
    for key in ("qaReport", "exportUnityFbx", "notes"):
        path = evidence_root / evidence[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(key, encoding="utf-8")
    write_test_png(evidence_root / evidence["previewNeutral"])
    slot["evidence"] = evidence


def run_report(manifest_path, evidence_root, *extra):
    return subprocess.run(
        [
            str(SCRIPT_PATH),
            "--manifest",
            str(manifest_path),
            "--evidence-root",
            str(evidence_root),
            *extra,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_generate_asset_evidence_report_shows_blocked_empty_manifest(tmp_path):
    manifest_path = write_manifest(tmp_path, clear_registered_assets(load_manifest()))

    result = run_report(manifest_path, tmp_path)

    assert result.returncode == 0
    assert "# Asset Evidence Progress Report" in result.stdout
    assert "Production trial gate: **blocked**" in result.stdout
    assert "`completeRealAssetsAtLeast10`" in result.stdout
    assert "| H-001 | humanoid | missing | missing |" in result.stdout


def test_generate_asset_evidence_report_writes_output_file(tmp_path):
    manifest_path = write_manifest(tmp_path, clear_registered_assets(load_manifest()))
    output_path = tmp_path / "report.md"

    result = run_report(manifest_path, tmp_path, "--output", str(output_path))

    assert result.returncode == 0
    assert result.stdout == ""
    assert output_path.read_text(encoding="utf-8").startswith("# Asset Evidence Progress Report")


def test_generate_asset_evidence_report_shows_complete_slot_and_file_check(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path)
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "Evidence file check: **enabled**" in result.stdout
    assert "| H-001 | humanoid | pass | pass | 4 | pass | blocked |" in result.stdout
    assert "- Real assets registered: 1" in result.stdout
    assert "- Complete evidence entries: 1" in result.stdout
