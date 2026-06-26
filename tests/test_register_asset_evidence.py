import json
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTER_SCRIPT = REPO_ROOT / "scripts" / "register_asset_evidence.py"
VALIDATOR_SCRIPT = REPO_ROOT / "scripts" / "validate_asset_evidence.py"
BASE_MANIFEST = REPO_ROOT / "samples" / "manifest.json"


def clear_registered_assets(manifest):
    for slot in manifest["slots"]:
        slot["realAsset"] = None
        slot["evidence"] = {}
    return manifest


def copy_manifest(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest = clear_registered_assets(json.loads(BASE_MANIFEST.read_text(encoding="utf-8")))
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def write_evidence_files(root, slot_id="H-001"):
    paths = {
        "qa": f"evidence/{slot_id}/qa-report.json",
        "preview": f"evidence/{slot_id}/preview-neutral.png",
        "preview_side": f"evidence/{slot_id}/preview-neutral-side.png",
        "pose_side": f"evidence/{slot_id}/preview-pose-side.png",
        "fbx": f"evidence/{slot_id}/export-unity.fbx",
        "notes": f"evidence/{slot_id}/notes.md",
    }
    for relative_path in paths.values():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative_path, encoding="utf-8")
    return paths


def register_command(manifest_path, evidence_root, paths, *extra):
    command = [
        str(REGISTER_SCRIPT),
        "--manifest",
        str(manifest_path),
        "--slot",
        "H-001",
        "--source-name",
        "Internal Hero",
        "--source-url",
        "https://example.invalid/source",
        "--license",
        "internal-test",
        "--external-path",
        "/external/assets/H-001.glb",
        "--qa-report",
        paths["qa"],
        "--preview-neutral",
        paths["preview"],
        "--export-unity-fbx",
        paths["fbx"],
        "--notes",
        paths["notes"],
        "--deformation-score",
        "4",
        "--unity-status",
        "pass",
        "--unreal-status",
        "blocked",
        "--evidence-root",
        str(evidence_root),
    ]
    if "preview_side" in paths:
        command.extend(["--preview-neutral-side", paths["preview_side"]])
    if "pose_side" in paths:
        command.extend(["--preview-pose-side", paths["pose_side"]])
    command.extend(extra)
    return command


def test_register_asset_evidence_updates_manifest_and_validates_files(tmp_path):
    manifest_path = copy_manifest(tmp_path)
    paths = write_evidence_files(tmp_path)

    result = subprocess.run(
        register_command(manifest_path, tmp_path, paths, "--check-files"),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == {"status": "registered", "slot": "H-001"}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slot = next(slot for slot in manifest["slots"] if slot["id"] == "H-001")
    assert slot["realAsset"]["sourceName"] == "Internal Hero"
    assert slot["realAsset"]["canCommitBinary"] is False
    assert slot["evidence"]["deformationScore"] == 4
    assert slot["evidence"]["previewNeutralSide"] == "evidence/H-001/preview-neutral-side.png"
    assert slot["evidence"]["previewPoseSide"] == "evidence/H-001/preview-pose-side.png"
    assert slot["evidence"]["unityImport"]["status"] == "pass"
    assert slot["evidence"]["unrealImport"]["status"] == "blocked"

    validation = subprocess.run(
        [
            str(VALIDATOR_SCRIPT),
            "--manifest",
            str(manifest_path),
            "--evidence-root",
            str(tmp_path),
            "--check-evidence-files",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert validation.returncode == 0


def test_register_asset_evidence_records_visual_review_status(tmp_path):
    manifest_path = copy_manifest(tmp_path)
    paths = write_evidence_files(tmp_path)
    command = register_command(
        manifest_path,
        tmp_path,
        paths,
        "--unity-status",
        "blocked",
        "--visual-review-status",
        "pass",
        "--visual-review-notes",
        "front and side pose previews are acceptable",
    )

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slot = next(slot for slot in manifest["slots"] if slot["id"] == "H-001")
    assert slot["evidence"]["visualReview"]["status"] == "pass"
    assert slot["evidence"]["visualReview"]["notes"] == "front and side pose previews are acceptable"


def test_register_asset_evidence_dry_run_does_not_modify_manifest(tmp_path):
    manifest_path = copy_manifest(tmp_path)
    original = manifest_path.read_text(encoding="utf-8")
    paths = write_evidence_files(tmp_path)

    result = subprocess.run(
        register_command(manifest_path, tmp_path, paths, "--dry-run"),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert manifest_path.read_text(encoding="utf-8") == original
    payload = json.loads(result.stdout)
    slot = next(slot for slot in payload["slots"] if slot["id"] == "H-001")
    assert slot["realAsset"]["sourceName"] == "Internal Hero"


def test_register_asset_evidence_rejects_unknown_slot(tmp_path):
    manifest_path = copy_manifest(tmp_path)
    paths = write_evidence_files(tmp_path)
    command = register_command(manifest_path, tmp_path, paths)
    command[command.index("--slot") + 1] = "NOPE-001"

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Slot not found" in result.stderr


def test_register_asset_evidence_requires_force_to_overwrite(tmp_path):
    manifest_path = copy_manifest(tmp_path)
    paths = write_evidence_files(tmp_path)

    first = subprocess.run(
        register_command(manifest_path, tmp_path, paths),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    second = subprocess.run(
        register_command(manifest_path, tmp_path, paths),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert first.returncode == 0
    assert second.returncode == 73
    assert "already has realAsset or evidence" in second.stderr


def test_register_asset_evidence_check_files_rejects_missing_paths(tmp_path):
    manifest_path = copy_manifest(tmp_path)
    paths = {
        "qa": "evidence/H-001/qa-report.json",
        "preview": "evidence/H-001/preview-neutral.png",
        "fbx": "evidence/H-001/export-unity.fbx",
        "notes": "evidence/H-001/notes.md",
    }

    result = subprocess.run(
        register_command(manifest_path, tmp_path, paths, "--check-files"),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 66
    assert "Missing evidence files" in result.stderr


def test_register_asset_evidence_keeps_external_evidence_as_storage_reference(tmp_path):
    manifest_path = copy_manifest(tmp_path)
    paths = {
        "qa": "s3://rig-evidence/H-001/qa-report.json",
        "preview": "s3://rig-evidence/H-001/preview-neutral.png",
        "fbx": "s3://rig-evidence/H-001/export-unity.fbx",
        "notes": "s3://rig-evidence/H-001/notes.md",
    }

    result = subprocess.run(
        register_command(manifest_path, tmp_path, paths, "--check-files"),
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slot = next(slot for slot in manifest["slots"] if slot["id"] == "H-001")
    assert slot["evidence"]["qaReport"] == {
        "storageReference": "s3://rig-evidence/H-001/qa-report.json"
    }
    validation = subprocess.run(
        [
            str(VALIDATOR_SCRIPT),
            "--manifest",
            str(manifest_path),
            "--evidence-root",
            str(tmp_path),
            "--check-evidence-files",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert validation.returncode == 0
