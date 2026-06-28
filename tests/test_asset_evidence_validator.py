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


def mark_complete(
    slot,
    *,
    score=4,
    unity="pass",
    unreal=None,
    visual_review="pass",
    visual_review_notes="manual review passed",
):
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
        "previewNeutralSide": f"evidence/{slot['id']}/preview-neutral-side.png",
        "previewPoseSide": f"evidence/{slot['id']}/preview-pose-side.png",
        "exportUnityFbx": f"evidence/{slot['id']}/export-unity.fbx",
        "notes": f"evidence/{slot['id']}/notes.md",
        "deformationScore": score,
        "unityImport": {"status": unity},
    }
    if visual_review is not None:
        evidence["visualReview"] = {"status": visual_review}
        if visual_review_notes is not None:
            evidence["visualReview"]["notes"] = visual_review_notes
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
    if (evidence.get("unityImport") or {}).get("status") == "pass":
        write_unity_import_result(evidence_root, slot["id"])
    preview_rows = [
        [30, 30, 30, 220],
        [30, 220, 220, 30],
        [30, 220, 220, 30],
        [30, 30, 30, 220],
    ]
    for key in ("previewNeutral", "previewNeutralSide", "previewPoseSide"):
        write_test_png(evidence_root / evidence[key], rows=preview_rows)
    humanoid_diagnostics = None
    if slot.get("category") == "humanoid":
        humanoid_diagnostics = {
            "status": "pass",
            "coverageRatios": {
                "core": 0.60,
                "arm": 0.15,
                "leg": 0.18,
                "foot": 0.07,
            },
            "warnings": [],
        }
    write_workflow_summary(
        evidence_root,
        slot["id"],
        pose_status="pass",
        humanoid_diagnostics=humanoid_diagnostics,
    )


def write_unity_import_result(
    evidence_root,
    slot_id,
    *,
    status="pass",
    instantiated=True,
    skinned_mesh_renderer_count=1,
    mesh_filter_count=0,
    bone_transform_smoke="valid",
    animation_clip_smoke="valid",
    configured_animator_smoke="valid",
    humanoid_avatar_smoke=None,
    bounds_smoke="valid",
    bounds_max_dimension=1.8,
):
    path = evidence_root / f"evidence/{slot_id}/unity-import.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": status,
        "assetPath": "Assets/MacGameRiggerImportCandidate/export-unity.fbx",
        "instantiated": instantiated,
        "childCount": 20,
        "rendererCount": 1,
        "skinnedMeshRendererCount": skinned_mesh_renderer_count,
        "meshFilterCount": mesh_filter_count,
        "modelImporter": {
            "available": True,
            "animationType": "Generic",
            "importAnimation": True,
            "globalScale": 1,
        },
    }
    if bone_transform_smoke == "valid":
        result["boneTransformSmoke"] = {
            "passed": True,
            "boneCandidateCount": 17,
            "testedBone": "Hips",
            "rotationDeltaDegrees": 4.99997,
        }
    elif bone_transform_smoke is not None:
        result["boneTransformSmoke"] = bone_transform_smoke
    if animation_clip_smoke == "valid":
        result["animationClipSmoke"] = {
            "passed": True,
            "sampledBone": "Hips",
            "sampledRotationDeltaDegrees": 7.5,
        }
    elif animation_clip_smoke is not None:
        result["animationClipSmoke"] = animation_clip_smoke
    if configured_animator_smoke == "valid":
        result["configuredAnimatorSmoke"] = {
            "passed": True,
            "animatorCount": 1,
            "controllerAssigned": True,
            "stateCount": 1,
            "sampledBone": "Hips",
            "sampledRotationDeltaDegrees": 7.5,
        }
    elif configured_animator_smoke is not None:
        result["configuredAnimatorSmoke"] = configured_animator_smoke
    if humanoid_avatar_smoke == "valid":
        result["humanoidAvatarSmoke"] = {
            "passed": True,
            "avatarIsValid": True,
            "avatarIsHuman": True,
            "mappedHumanBoneCount": 15,
            "requiredHumanBoneCount": 15,
        }
    elif humanoid_avatar_smoke is not None:
        result["humanoidAvatarSmoke"] = humanoid_avatar_smoke
    if bounds_smoke == "valid":
        result["boundsSmoke"] = {
            "passed": True,
            "boundsCenter": {"x": 0.0, "y": 0.9, "z": 0.0},
            "boundsSize": {"x": 0.8, "y": bounds_max_dimension, "z": 0.5},
            "boundsHeight": bounds_max_dimension,
            "maxDimension": bounds_max_dimension,
        }
    elif bounds_smoke is not None:
        result["boundsSmoke"] = bounds_smoke
    path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "status": status,
                "result": result,
            }
        ),
        encoding="utf-8",
    )


def write_workflow_summary(
    evidence_root,
    slot_id,
    *,
    pose_status="pass",
    humanoid_diagnostics=None,
):
    path = evidence_root / f"evidence/{slot_id}/workflow-summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "poseDeformation": {
            "status": pose_status,
            "maxAxisExpansionRatio": 4.5 if pose_status == "fail" else 1.8,
            "expandedAxes": ["x"] if pose_status == "fail" else [],
            "warningAxes": [],
        }
    }
    if humanoid_diagnostics is not None:
        payload["humanoidDiagnostics"] = humanoid_diagnostics
    path.write_text(json.dumps(payload), encoding="utf-8")


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


def test_asset_evidence_validator_reports_preview_silhouette_diagnostics(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=2, unity="blocked", unreal="blocked", visual_review="fail")
    create_evidence_files(tmp_path, slot)
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_validator(
        manifest_path,
        "--evidence-root",
        str(tmp_path),
        "--check-evidence-files",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    h001 = next(slot for slot in payload["slots"] if slot["id"] == "H-001")
    neutral = h001["previewDiagnostics"]["previewNeutral"]
    assert neutral["imageSize"] == {"width": 4, "height": 4}
    assert neutral["foregroundBounds"] == {"x": 1, "y": 0, "width": 3, "height": 4}
    assert neutral["foregroundPixelRatio"] == 0.375
    assert neutral["foregroundFillRatio"] == 0.5


def test_asset_evidence_validator_reports_preview_vertical_center_shift(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=2, unity="blocked", unreal="blocked", visual_review="fail")
    create_evidence_files(tmp_path, slot)
    write_test_png(
        tmp_path / slot["evidence"]["previewPoseSide"],
        rows=[
            [220, 30, 30, 30],
            [220, 30, 30, 30],
            [30, 30, 30, 220],
            [30, 30, 30, 220],
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
    h001 = next(slot for slot in payload["slots"] if slot["id"] == "H-001")
    pose_side = h001["previewDiagnostics"]["previewPoseSide"]
    assert pose_side["verticalCenterShiftRatio"] == 0.75


def test_asset_evidence_validator_checks_side_preview_files_when_present(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=2, unity="blocked", unreal="blocked", visual_review="fail")
    create_evidence_files(tmp_path, slot)
    slot["evidence"]["previewNeutralSide"] = "evidence/H-001/missing-preview-neutral-side.png"
    slot["evidence"]["previewPoseSide"] = "evidence/H-001/missing-preview-pose-side.png"
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
    issues = incomplete[0]["issues"]
    assert any("preview evidence file not found: evidence/H-001/missing-preview-neutral-side.png" in issue for issue in issues)
    assert any("preview evidence file not found: evidence/H-001/missing-preview-pose-side.png" in issue for issue in issues)


def test_asset_evidence_validator_blocks_score_three_plus_with_failed_pose_qa(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=4, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_workflow_summary(tmp_path, slot["id"], pose_status="fail")
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
    assert any("poseDeformation.status=fail" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_blocks_score_three_plus_humanoid_with_warning_diagnostics(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=4, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_workflow_summary(
        tmp_path,
        slot["id"],
        pose_status="pass",
        humanoid_diagnostics={
            "status": "warn",
            "coverageRatios": {
                "core": 0.90,
                "arm": 0.0,
                "leg": 0.09,
                "foot": 0.0,
            },
            "warnings": ["weakHumanoidFootCoverage"],
        },
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
    assert any(
        "humanoidDiagnostics.status=warn is not allowed for score >=3" in issue
        and "weakHumanoidFootCoverage" in issue
        for issue in incomplete[0]["issues"]
    )


def test_asset_evidence_validator_blocks_score_three_plus_without_visual_or_engine_pass(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=4, unity="blocked", unreal="blocked", visual_review=None)
    create_evidence_files(tmp_path, slot)
    write_workflow_summary(tmp_path, slot["id"], pose_status="pass")
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
    assert any("visualReview.status=pass or engine import pass" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_rejects_invalid_visual_review_status(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=2, unity="blocked", unreal="blocked", visual_review="maybe")
    create_evidence_files(tmp_path, slot)
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
    assert any("invalid visualReview.status" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_requires_notes_for_score_three_plus_visual_pass(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(
        slot,
        score=4,
        unity="blocked",
        unreal="blocked",
        visual_review="pass",
        visual_review_notes=None,
    )
    create_evidence_files(tmp_path, slot)
    del slot["evidence"]["previewNeutralSide"]
    del slot["evidence"]["previewPoseSide"]
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
    assert any("visualReview.notes is required" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_requires_side_previews_for_score_three_plus_visual_pass(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(
        slot,
        score=4,
        unity="blocked",
        unreal="blocked",
        visual_review="pass",
        visual_review_notes="front and side pose previews are acceptable",
    )
    create_evidence_files(tmp_path, slot)
    del slot["evidence"]["previewNeutralSide"]
    del slot["evidence"]["previewPoseSide"]
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
    assert any("side preview evidence is required" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_blocks_score_three_unity_pass_without_skinned_import(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        skinned_mesh_renderer_count=0,
        mesh_filter_count=1,
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
    assert any("Unity import skinnedMeshRendererCount must be >= 1" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_blocks_score_three_unity_pass_without_bone_transform_smoke(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        bone_transform_smoke={"passed": False, "boneCandidateCount": 0},
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
    assert any("Unity import boneTransformSmoke.passed must be true" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_blocks_score_three_unity_pass_without_animation_clip_smoke(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        animation_clip_smoke={"passed": False, "sampledRotationDeltaDegrees": 0},
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
    assert any("Unity import animationClipSmoke.passed must be true" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_blocks_score_three_humanoid_unity_pass_without_configured_animator_smoke(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        configured_animator_smoke={"passed": False, "controllerAssigned": False, "stateCount": 0},
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
    assert any("Unity import configuredAnimatorSmoke.passed must be true" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_warns_for_missing_configured_animator_smoke_without_blocking_evidence(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        configured_animator_smoke=None,
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
    slot_payload = next(item for item in payload["slots"] if item["id"] == slot["id"])
    assert slot_payload["evidenceComplete"] is True
    assert slot_payload["issues"] == []
    assert any("Unity import configuredAnimatorSmoke is not recorded yet" in warning for warning in slot_payload["warnings"])


def test_asset_evidence_validator_strict_flag_blocks_missing_configured_animator_smoke(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        configured_animator_smoke=None,
    )
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_validator(
        manifest_path,
        "--evidence-root",
        str(tmp_path),
        "--check-evidence-files",
        "--require-configured-animator-smoke",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    slot_payload = next(item for item in payload["slots"] if item["id"] == slot["id"])
    assert slot_payload["evidenceComplete"] is False
    assert any(
        "Unity import configuredAnimatorSmoke is required for humanoid score >=3" in issue
        for issue in slot_payload["issues"]
    )


def test_asset_evidence_validator_blocks_invalid_humanoid_avatar_smoke_when_recorded(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        humanoid_avatar_smoke={
            "passed": False,
            "avatarIsValid": False,
            "avatarIsHuman": False,
            "mappedHumanBoneCount": 6,
            "requiredHumanBoneCount": 15,
        },
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
    assert any("Unity import humanoidAvatarSmoke.passed must be true" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_warns_for_missing_humanoid_avatar_smoke_without_blocking_evidence(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        humanoid_avatar_smoke=None,
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
    slot_payload = next(item for item in payload["slots"] if item["id"] == slot["id"])
    assert slot_payload["evidenceComplete"] is True
    assert any("Unity import humanoidAvatarSmoke is not recorded yet" in warning for warning in slot_payload["warnings"])


def test_asset_evidence_validator_blocks_score_three_unity_pass_without_bounds_smoke(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        bounds_smoke={"passed": False, "maxDimension": 0},
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
    assert any("Unity import boundsSmoke.passed must be true" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_warns_for_large_unity_scale_without_blocking_evidence(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        bounds_max_dimension=20,
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
    slot_payload = next(item for item in payload["slots"] if item["id"] == slot["id"])
    assert slot_payload["evidenceComplete"] is True
    assert slot_payload["issues"] == []
    assert any("Unity import maxDimension 20 exceeds humanoid warning limit" in warning for warning in slot_payload["warnings"])


def test_asset_evidence_validator_blocks_score_three_unity_pass_with_severe_scale_anomaly(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=3, unity="pass", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_unity_import_result(
        tmp_path,
        slot["id"],
        bounds_max_dimension=540,
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
    assert any("Unity import maxDimension 540 exceeds humanoid severe limit" in issue for issue in incomplete[0]["issues"])


def test_asset_evidence_validator_allows_failed_pose_qa_for_low_score_evidence(tmp_path):
    manifest = clear_registered_assets(load_base_manifest())
    slot = manifest["slots"][0]
    mark_complete(slot, score=2, unity="blocked", unreal="blocked")
    create_evidence_files(tmp_path, slot)
    write_workflow_summary(tmp_path, slot["id"], pose_status="fail")
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_validator(
        manifest_path,
        "--evidence-root",
        str(tmp_path),
        "--check-evidence-files",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    h001 = next(slot for slot in payload["slots"] if slot["id"] == "H-001")
    assert h001["evidenceComplete"] is True
    assert h001["issues"] == []
