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


def write_test_png(path, rows=None):
    if rows is None:
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


def mark_complete(
    slot,
    evidence_root,
    *,
    score=4,
    unity="pass",
    unreal="blocked",
    visual_review=None,
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
        "exportUnityFbx": f"evidence/{slot['id']}/export-unity.fbx",
        "notes": f"evidence/{slot['id']}/notes.md",
        "deformationScore": score,
        "unityImport": {"status": unity},
        "unrealImport": {"status": unreal},
    }
    if visual_review is not None:
        evidence["visualReview"] = {"status": visual_review}
    for key in ("qaReport", "exportUnityFbx", "notes"):
        path = evidence_root / evidence[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(key, encoding="utf-8")
    if unity == "pass":
        write_unity_import_result(evidence_root, slot["id"])
    write_test_png(evidence_root / evidence["previewNeutral"])
    slot["evidence"] = evidence


def write_unity_import_result(
    evidence_root,
    slot_id,
    *,
    bounds_max_dimension=1.8,
    configured_animator_smoke=None,
):
    path = evidence_root / f"evidence/{slot_id}/unity-import.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "status": "pass",
        "assetPath": "Assets/MacGameRiggerImportCandidate/export-unity.fbx",
        "instantiated": True,
        "childCount": 20,
        "rendererCount": 1,
        "skinnedMeshRendererCount": 1,
        "meshFilterCount": 0,
        "boundsSmoke": {
            "passed": True,
            "boundsCenter": {"x": 0.0, "y": 0.9, "z": 0.0},
            "boundsSize": {"x": 0.8, "y": bounds_max_dimension, "z": 0.5},
            "boundsHeight": bounds_max_dimension,
            "maxDimension": bounds_max_dimension,
        },
        "boneTransformSmoke": {
            "passed": True,
            "boneCandidateCount": 17,
            "testedBone": "Hips",
            "rotationDeltaDegrees": 4.99997,
        },
        "animationClipSmoke": {
            "passed": True,
            "sampledBone": "Hips",
            "sampledBonePath": "MGR_Armature/Hips",
            "sampledRotationDeltaDegrees": 7.5,
        },
        "modelImporter": {
            "available": True,
            "animationType": "Generic",
            "importAnimation": True,
            "globalScale": 1,
        },
    }
    if configured_animator_smoke is not None:
        result["configuredAnimatorSmoke"] = configured_animator_smoke
    path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "status": "pass",
                "result": result,
            }
        ),
        encoding="utf-8",
    )


def write_workflow_summary(
    evidence_root,
    slot_id,
    *,
    mesh_count=None,
    pose_status="fail",
    max_axis_expansion=4.25,
    allowed_axes=None,
    weight_diagnostics=None,
    prop_diagnostics=None,
    humanoid_diagnostics=None,
):
    expanded_axes = ["x"] if pose_status == "fail" else []
    summary_path = evidence_root / f"evidence/{slot_id}/workflow-summary.json"
    payload = {
        "poseDeformation": {
            "status": pose_status,
            "maxAxisExpansionRatio": max_axis_expansion,
            "expandedAxes": expanded_axes,
            "warningAxes": [],
        }
    }
    if mesh_count is not None:
        payload["meshCount"] = mesh_count
        payload["qa"] = {"mesh_count": mesh_count}
    if allowed_axes is not None:
        payload["poseDeformation"]["allowedExpandedAxes"] = allowed_axes
    if weight_diagnostics is not None:
        payload["weightDiagnostics"] = weight_diagnostics
    if prop_diagnostics is not None:
        payload["propDiagnostics"] = prop_diagnostics
    if humanoid_diagnostics is not None:
        payload["humanoidDiagnostics"] = humanoid_diagnostics
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


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
            write_workflow_summary(
                tmp_path,
                "H-001",
                pose_status="pass",
                max_axis_expansion=1.8,
                humanoid_diagnostics={
                    "status": "pass",
                    "warnings": [],
                },
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "Evidence file check: **enabled**" in result.stdout
    assert "| H-001 | humanoid | pass | pass | 4 |  | pass 1.8x |  | pass | blocked |" in result.stdout
    assert "- Real assets registered: 1" in result.stdout
    assert "- Complete evidence entries: 1" in result.stdout


def test_generate_asset_evidence_report_shows_pose_deformation_summary(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=2, visual_review="fail")
            write_workflow_summary(tmp_path, "H-001")
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "| Slot | Category | Real Asset | Evidence | Score | Meshes | Pose QA | Visual | Unity | Unreal | Preview | Weight | Warnings | Issues |" in result.stdout
    assert "| H-001 | humanoid | pass | pass | 2 |  | fail 4.25x x | fail | pass | blocked |" in result.stdout


def test_generate_asset_evidence_report_shows_allowed_pose_expansion_axes(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "P-001":
            mark_complete(next_slot, tmp_path, score=3, visual_review="pass")
            write_workflow_summary(
                tmp_path,
                "P-001",
                pose_status="pass",
                max_axis_expansion=4.4073,
                allowed_axes=["y"],
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "| P-001 | prop | pass | pass | 3 |  | pass 4.4073x allowed:y | pass | pass | blocked |" in result.stdout


def test_generate_asset_evidence_report_shows_preview_silhouette_summary(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=2, visual_review="fail")
            write_workflow_summary(tmp_path, "H-001")
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "| Slot | Category | Real Asset | Evidence | Score | Meshes | Pose QA | Visual | Unity | Unreal | Preview | Weight | Warnings | Issues |" in result.stdout
    assert "| H-001 | humanoid | pass | pass | 2 |  | fail 4.25x x | fail | pass | blocked | fg 37.5% fill 50.0% |" in result.stdout


def test_generate_asset_evidence_report_shows_side_preview_lean_summary(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=2, visual_review="fail")
            next_slot["evidence"]["previewNeutralSide"] = "evidence/H-001/preview-neutral-side.png"
            next_slot["evidence"]["previewPoseSide"] = "evidence/H-001/preview-pose-side.png"
            write_test_png(tmp_path / next_slot["evidence"]["previewNeutralSide"])
            write_test_png(
                tmp_path / next_slot["evidence"]["previewPoseSide"],
                rows=[
                    [220, 30, 30, 30],
                    [220, 30, 30, 30],
                    [30, 30, 30, 220],
                    [30, 30, 30, 220],
                ],
            )
            write_workflow_summary(tmp_path, "H-001")
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "side 3->4px 1.33x lean 0.75" in result.stdout


def test_generate_asset_evidence_report_shows_weight_region_summary(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=2, visual_review="fail")
            write_workflow_summary(
                tmp_path,
                "H-001",
                weight_diagnostics={
                    "regions": {
                        "core": {"dominantVertices": 20},
                        "neckHead": {"dominantVertices": 3},
                        "upperArm": {"dominantVertices": 8},
                        "lowerArm": {"dominantVertices": 6},
                        "upperLeg": {"dominantVertices": 10},
                        "lowerLeg": {"dominantVertices": 9},
                        "foot": {"dominantVertices": 2},
                    }
                },
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "| Slot | Category | Real Asset | Evidence | Score | Meshes | Pose QA | Visual | Unity | Unreal | Preview | Weight | Warnings | Issues |" in result.stdout
    assert "core 20 neck 3 arm 14 leg 19 foot 2" in result.stdout


def test_generate_asset_evidence_report_shows_unity_scale_warnings(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=3, visual_review="pass")
            write_unity_import_result(tmp_path, "H-001", bounds_max_dimension=20)
            write_workflow_summary(
                tmp_path,
                "H-001",
                pose_status="pass",
                humanoid_diagnostics={"status": "pass", "warnings": []},
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "Unity import maxDimension 20 exceeds humanoid warning limit" in result.stdout
    assert "| H-001 | humanoid | pass | pass | 3 |  | pass 4.25x | pass | pass | blocked |" in result.stdout


def test_generate_asset_evidence_report_shows_missing_configured_animator_smoke_warning(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=3, visual_review="pass")
            write_workflow_summary(
                tmp_path,
                "H-001",
                pose_status="pass",
                humanoid_diagnostics={"status": "pass", "warnings": []},
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "Unity import configuredAnimatorSmoke is not recorded yet" in result.stdout
    assert "| H-001 | humanoid | pass | pass | 3 |  | pass 4.25x | pass | pass | blocked |" in result.stdout


def test_generate_asset_evidence_report_shows_configured_animator_strict_gate(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=3, visual_review="pass")
            write_workflow_summary(
                tmp_path,
                "H-001",
                pose_status="pass",
                humanoid_diagnostics={"status": "pass", "warnings": []},
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "## Strict Quality Gates" in result.stdout
    assert "| `configuredAnimatorSmokeForHumanoidScore3` | blocked | H-001 |" in result.stdout


def test_generate_asset_evidence_report_blocks_missing_real_separate_mesh_humanoid(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=3, visual_review="pass")
            write_workflow_summary(
                tmp_path,
                "H-001",
                mesh_count=1,
                pose_status="pass",
                humanoid_diagnostics={"status": "pass", "warnings": []},
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "| `realSeparateMeshHumanoidEvidence` | blocked | H-001 |" in result.stdout
    assert (
        "| Slot | Category | Real Asset | Evidence | Score | Meshes | Pose QA | Visual | "
        "Unity | Unreal | Preview | Weight | Warnings | Issues |"
    ) in result.stdout
    assert "| H-001 | humanoid | pass | pass | 3 | 1 | pass" in result.stdout


def test_generate_asset_evidence_report_passes_real_separate_mesh_humanoid_gate(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=3, visual_review="pass")
            write_workflow_summary(
                tmp_path,
                "H-001",
                mesh_count=2,
                pose_status="pass",
                humanoid_diagnostics={"status": "pass", "warnings": []},
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "| `realSeparateMeshHumanoidEvidence` | pass |  |" in result.stdout
    assert "| H-001 | humanoid | pass | pass | 3 | 2 | pass" in result.stdout


def test_generate_asset_evidence_report_strict_gate_blocks_failed_configured_animator_smoke(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=3, visual_review="pass")
            write_unity_import_result(
                tmp_path,
                "H-001",
                configured_animator_smoke={"passed": False},
            )
            write_workflow_summary(
                tmp_path,
                "H-001",
                pose_status="pass",
                humanoid_diagnostics={"status": "pass", "warnings": []},
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "| `configuredAnimatorSmokeForHumanoidScore3` | blocked | H-001 |" in result.stdout
    assert "Unity import configuredAnimatorSmoke.passed must be true" in result.stdout


def test_generate_asset_evidence_report_shows_prop_weight_region_summary(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "P-001":
            mark_complete(next_slot, tmp_path, score=3, visual_review="pass")
            write_workflow_summary(
                tmp_path,
                "P-001",
                pose_status="pass",
                max_axis_expansion=1.0,
                weight_diagnostics={
                    "regions": {
                        "propBase": {"dominantVertices": 144},
                        "propHinge": {"dominantVertices": 12},
                        "propMovingPart": {"dominantVertices": 204},
                    }
                },
                prop_diagnostics={"status": "pass", "warnings": []},
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "prop base 144 hinge 12 moving 204 prop qa pass" in result.stdout


def test_generate_asset_evidence_report_shows_prop_diagnostic_warnings(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "P-001":
            mark_complete(next_slot, tmp_path, score=3, visual_review="pass")
            write_workflow_summary(
                tmp_path,
                "P-001",
                pose_status="pass",
                max_axis_expansion=1.0,
                weight_diagnostics={
                    "regions": {
                        "propBase": {"dominantVertices": 140},
                        "propHinge": {"dominantVertices": 1},
                        "propMovingPart": {"dominantVertices": 219},
                    }
                },
                prop_diagnostics={
                    "status": "warn",
                    "warnings": ["weakPropHingeCoverage"],
                },
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "prop qa warn weakPropHingeCoverage" in result.stdout


def test_generate_asset_evidence_report_shows_humanoid_diagnostic_warnings(tmp_path):
    manifest = clear_registered_assets(load_manifest())
    slots = []
    for slot in manifest["slots"]:
        next_slot = copy.deepcopy(slot)
        if slot["id"] == "H-001":
            mark_complete(next_slot, tmp_path, score=2, visual_review="fail")
            write_workflow_summary(
                tmp_path,
                "H-001",
                pose_status="pass",
                max_axis_expansion=1.207,
                weight_diagnostics={
                    "regions": {
                        "core": {"dominantVertices": 615},
                        "lowerLeg": {"dominantVertices": 63},
                        "foot": {"dominantVertices": 15},
                    }
                },
                humanoid_diagnostics={
                    "status": "warn",
                    "warnings": ["weakHumanoidFootCoverage"],
                },
            )
        slots.append(next_slot)
    manifest["slots"] = slots
    manifest_path = write_manifest(tmp_path, manifest)

    result = run_report(manifest_path, tmp_path, "--check-evidence-files")

    assert result.returncode == 0
    assert "humanoid qa warn weakHumanoidFootCoverage" in result.stdout
