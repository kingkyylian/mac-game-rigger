#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import traceback


REPO_ROOT = Path(__file__).resolve().parents[1]
LANDMARK_PREFIX = "MGR_Landmark_"
GIZMO_PREFIX = "MGR_Gizmo_"
POINT_TOLERANCE = 0.0001


def extract_blender_args(argv: list[str]) -> list[str]:
    if "--" in argv:
        return argv[argv.index("--") + 1 :]
    return argv[1:]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the prop hinge gizmo guide workflow inside Blender."
    )
    parser.add_argument(
        "--output",
        help="Write the JSON smoke report to this path.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print JSON to stdout. Use with --output for evidence runs.",
    )
    return parser.parse_args(argv)


def build_report(
    checks: list[dict[str, object]],
    *,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    failed_checks = [
        str(check["name"])
        for check in checks
        if check.get("status") != "pass"
    ]
    return {
        "schemaVersion": 1,
        "kind": "prop_hinge_gizmo_workflow_smoke",
        "status": "pass" if not failed_checks else "fail",
        "failedChecks": failed_checks,
        "checks": checks,
        "details": details or {},
    }


def run_workflow() -> dict[str, object]:
    import bpy

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    import addon.mac_game_rigger as mac_game_rigger
    from addon.mac_game_rigger.ui import operators as ui_ops

    checks: list[dict[str, object]] = []
    details: dict[str, object] = {"repoRoot": str(REPO_ROOT)}
    registered = False

    try:
        mac_game_rigger.register()
        registered = True
        checks.append(pass_check("addonRegistered"))

        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()

        scene = bpy.context.scene
        scene.mgr_current_template = "humanoid"
        poll_humanoid = ui_ops.MGR_GGT_prop_hinge_orientation.poll(bpy.context)
        scene.mgr_current_template = "prop_hinge"
        poll_prop_hinge = ui_ops.MGR_GGT_prop_hinge_orientation.poll(bpy.context)
        checks.append(
            pass_fail_check(
                "gizmoPollsOnlyForPropHinge",
                (poll_humanoid is False) and (poll_prop_hinge is True),
                {
                    "humanoid": poll_humanoid,
                    "prop_hinge": poll_prop_hinge,
                    "idname": ui_ops.MGR_GGT_prop_hinge_orientation.bl_idname,
                },
            )
        )

        scene.mgr_prop_hinge_pivot_x = 0.12
        scene.mgr_prop_hinge_base_x = 0.24
        scene.mgr_prop_hinge_axis = "x"
        scene.mgr_prop_hinge_open_angle = 0.72
        scene.mgr_prop_hinge_swing_direction = "negative"
        scene.mgr_prop_hinge_rotation_axis = "y"

        mesh = create_test_prop_mesh(bpy)
        details["mesh"] = {
            "name": mesh.name,
            "dimensions": rounded_point(mesh.dimensions),
        }

        generate_result = bpy.ops.mgr.generate_prop_hinge_landmarks()
        checks.append(operator_check("generatePropHingeLandmarks", generate_result))

        pivot = bpy.data.objects.get(f"{GIZMO_PREFIX}prop_hinge_pivot")
        swing_tip = bpy.data.objects.get(f"{GIZMO_PREFIX}prop_hinge_swing_tip")
        checks.append(
            pass_fail_check(
                "guideObjectsCreated",
                pivot is not None and swing_tip is not None,
                {
                    "pivot": object_location(pivot),
                    "swing_tip": object_location(swing_tip),
                },
            )
        )

        base = bpy.data.objects.get(f"{LANDMARK_PREFIX}base")
        if base is not None and pivot is not None and swing_tip is not None:
            moved_pivot = (-1.38, 0.08, 0.7)
            moved_swing_tip = (1.64, 0.22, 0.72)
            pivot.location = moved_pivot
            swing_tip.location = moved_swing_tip
            details["movedGuides"] = {
                "pivot": rounded_point(moved_pivot),
                "swing_tip": rounded_point(moved_swing_tip),
            }

        commit_result = bpy.ops.mgr.commit_prop_hinge_guides()
        checks.append(operator_check("commitPropHingeGuides", commit_result))

        expected_landmarks = expected_committed_landmarks(base, pivot, swing_tip)
        actual_landmarks = collect_landmark_locations(bpy)
        details["expectedLandmarks"] = expected_landmarks
        details["actualLandmarks"] = actual_landmarks
        checks.append(
            pass_fail_check(
                "committedLandmarksMatchMovedGuides",
                landmarks_match(expected_landmarks, actual_landmarks),
            )
        )

        generate_armature_result = bpy.ops.mgr.generate_armature()
        checks.append(operator_check("generateArmature", generate_armature_result))
        armature = bpy.data.objects.get("MGR_Armature")
        checks.append(
            pass_fail_check(
                "propHingeArmatureCreated",
                armature is not None and armature.type == "ARMATURE",
                {"boneCount": len(armature.data.bones) if armature is not None else 0},
            )
        )

        pose_result = bpy.ops.mgr.pose_prop_hinge_open()
        checks.append(operator_check("posePropHingeOpen", pose_result))
        details["poseMessage"] = scene.get("mgr_pose_test_message", "")

    finally:
        if registered:
            mac_game_rigger.unregister()

    return build_report(checks, details=details)


def create_test_prop_mesh(bpy):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.6))
    mesh = bpy.context.object
    mesh.name = "MGR_PropHingeSmoke_Mesh"
    mesh.dimensions = (4.0, 0.5, 1.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    return mesh


def pass_check(name: str, details: dict[str, object] | None = None) -> dict[str, object]:
    check: dict[str, object] = {"name": name, "status": "pass"}
    if details is not None:
        check["details"] = details
    return check


def pass_fail_check(
    name: str,
    passed: bool,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    check: dict[str, object] = {"name": name, "status": "pass" if passed else "fail"}
    if details is not None:
        check["details"] = details
    return check


def operator_check(name: str, result) -> dict[str, object]:
    result_values = sorted(str(value) for value in result)
    return pass_fail_check(
        name,
        "FINISHED" in result_values,
        {"result": result_values},
    )


def object_location(obj) -> list[float] | None:
    if obj is None:
        return None
    return rounded_point(obj.location)


def rounded_point(point) -> list[float]:
    return [round(float(point[index]), 4) for index in range(3)]


def expected_committed_landmarks(base, pivot, swing_tip) -> dict[str, list[float]]:
    if base is None or pivot is None or swing_tip is None:
        return {}
    pivot_point = rounded_point(pivot.location)
    swing_tip_point = rounded_point(swing_tip.location)
    moving_part = [
        round(pivot_point[index] + ((swing_tip_point[index] - pivot_point[index]) * 0.45), 4)
        for index in range(3)
    ]
    return {
        "base": rounded_point(base.location),
        "hinge": pivot_point,
        "moving_part": moving_part,
        "moving_tip": swing_tip_point,
    }


def collect_landmark_locations(bpy) -> dict[str, list[float]]:
    return {
        obj.name.removeprefix(LANDMARK_PREFIX): rounded_point(obj.location)
        for obj in bpy.context.scene.objects
        if obj.name.startswith(LANDMARK_PREFIX)
    }


def landmarks_match(
    expected: dict[str, list[float]],
    actual: dict[str, list[float]],
) -> bool:
    if not expected:
        return False
    for name, expected_point in expected.items():
        actual_point = actual.get(name)
        if actual_point is None:
            return False
        for expected_value, actual_value in zip(expected_point, actual_point):
            if abs(expected_value - actual_value) > POINT_TOLERANCE:
                return False
    return True


def write_report(path: str | None, report: dict[str, object]) -> None:
    if not path:
        return
    output_path = Path(path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    raw_argv = sys.argv if argv is None else argv
    args = parse_args(extract_blender_args(raw_argv))
    try:
        report = run_workflow()
    except Exception as exc:
        report = build_report(
            [
                {
                    "name": "unhandledException",
                    "status": "fail",
                    "details": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    },
                }
            ]
        )

    write_report(args.output, report)
    if not args.quiet:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
