#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = REPO_ROOT / "addon"


def humanoid_landmarks_from_bbox(bbox: dict[str, float]) -> dict[str, tuple[float, float, float]]:
    min_x = bbox["min_x"]
    max_x = bbox["max_x"]
    min_y = bbox["min_y"]
    max_y = bbox["max_y"]
    min_z = bbox["min_z"]
    max_z = bbox["max_z"]
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    width = max(max_x - min_x, 0.1)
    depth = max(max_y - min_y, 0.1)
    height = max(max_z - min_z, 0.1)

    def z(factor: float) -> float:
        return min_z + (height * factor)

    left_x = center_x + (width * 0.22)
    right_x = center_x - (width * 0.22)
    shoulder_left_x = center_x + (width * 0.34)
    shoulder_right_x = center_x - (width * 0.34)
    hand_left_x = center_x + (width * 0.48)
    hand_right_x = center_x - (width * 0.48)
    toe_y = center_y - (depth * 0.35)

    return {
        "hips": (center_x, center_y, z(0.48)),
        "spine": (center_x, center_y, z(0.58)),
        "chest": (center_x, center_y, z(0.70)),
        "neck": (center_x, center_y, z(0.84)),
        "head": (center_x, center_y, z(0.95)),
        "shoulder.L": (shoulder_left_x, center_y, z(0.75)),
        "upper_arm.L": (left_x, center_y, z(0.64)),
        "lower_arm.L": (center_x + (width * 0.38), center_y, z(0.50)),
        "hand.L": (hand_left_x, center_y, z(0.38)),
        "shoulder.R": (shoulder_right_x, center_y, z(0.75)),
        "upper_arm.R": (right_x, center_y, z(0.64)),
        "lower_arm.R": (center_x - (width * 0.38), center_y, z(0.50)),
        "hand.R": (hand_right_x, center_y, z(0.38)),
        "upper_leg.L": (left_x, center_y, z(0.29)),
        "lower_leg.L": (left_x, center_y, z(0.14)),
        "foot.L": (left_x, center_y - (depth * 0.12), z(0.03)),
        "toe.L": (left_x, toe_y, z(0.03)),
        "upper_leg.R": (right_x, center_y, z(0.29)),
        "lower_leg.R": (right_x, center_y, z(0.14)),
        "foot.R": (right_x, center_y - (depth * 0.12), z(0.03)),
        "toe.R": (right_x, toe_y, z(0.03)),
    }


def pose_preview_operator_name() -> str:
    return "pose_arm_raise"


def preview_material_name() -> str:
    return "MGR_Evidence_Preview_Material"


def orientation_normalization_plan_from_dimensions(
    dimensions: tuple[float, float, float],
) -> dict[str, str | float] | None:
    width_x, depth_y, height_z = dimensions
    if depth_y > height_z and depth_y > width_x:
        return {
            "sourceUpAxis": "y",
            "rotationAxis": "X",
            "rotationRadians": math.pi / 2,
        }
    return None


def camera_plan_from_bbox(
    bbox: dict[str, float],
    *,
    axis: str = "y",
) -> dict[str, tuple[float, float, float] | float]:
    center_x = (bbox["min_x"] + bbox["max_x"]) / 2.0
    center_y = (bbox["min_y"] + bbox["max_y"]) / 2.0
    center_z = (bbox["min_z"] + bbox["max_z"]) / 2.0
    height = max(bbox["max_z"] - bbox["min_z"], 0.1)
    width = max(bbox["max_x"] - bbox["min_x"], 0.1)
    depth = max(bbox["max_y"] - bbox["min_y"], 0.1)
    distance = max(height * 1.6, width * 2.5, depth * 3.0, 6.0)
    if axis == "x":
        camera_location = (bbox["min_x"] - distance, center_y, center_z)
        key_light_location = (bbox["min_x"] - (distance * 0.6), center_y, center_z + height)
    elif axis == "y":
        camera_location = (center_x, bbox["min_y"] - distance, center_z)
        key_light_location = (center_x, bbox["min_y"] - (distance * 0.6), center_z + height)
    else:
        raise ValueError(f"Unsupported camera axis: {axis}")
    target = (center_x, center_y, center_z)
    return {
        "cameraLocation": camera_location,
        "target": target,
        "keyLightLocation": key_light_location,
        "orthographicScale": max(height * 1.8, width * 2.0, 1.0),
        "clipEnd": (distance * 2.0) + max(height, width, depth),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Mac Game Rigger humanoid workflow on a real asset."
    )
    parser.add_argument("--asset", required=True, help="Source FBX, GLB/GLTF, OBJ, or BLEND path.")
    parser.add_argument("--evidence-dir", required=True, help="Evidence output directory.")
    parser.add_argument("--summary", required=True, help="Workflow summary JSON path.")
    parser.add_argument("--camera-axis", choices=("x", "y"), default="x", help="Axis used for evidence previews.")
    return parser.parse_args(argv)


def blender_script_args() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def reset_scene(bpy_module) -> None:
    if bpy_module.ops.object.mode_set.poll():
        bpy_module.ops.object.mode_set(mode="OBJECT")
    bpy_module.ops.object.select_all(action="SELECT")
    bpy_module.ops.object.delete()


def import_asset(bpy_module, asset_path: Path) -> None:
    suffix = asset_path.suffix.lower()
    if suffix == ".fbx":
        bpy_module.ops.import_scene.fbx(filepath=str(asset_path))
        return
    if suffix in {".glb", ".gltf"}:
        bpy_module.ops.import_scene.gltf(filepath=str(asset_path))
        return
    if suffix == ".obj":
        bpy_module.ops.wm.obj_import(filepath=str(asset_path))
        return
    if suffix == ".blend":
        bpy_module.ops.wm.open_mainfile(filepath=str(asset_path))
        return
    raise ValueError(f"Unsupported asset format: {asset_path.suffix}")


def mesh_bbox(bpy_module) -> dict[str, float]:
    from mathutils import Vector

    points = []
    for obj in bpy_module.context.scene.objects:
        if obj.type != "MESH":
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        raise ValueError("Imported asset contains no mesh objects")

    return {
        "min_x": min(point.x for point in points),
        "max_x": max(point.x for point in points),
        "min_y": min(point.y for point in points),
        "max_y": max(point.y for point in points),
        "min_z": min(point.z for point in points),
        "max_z": max(point.z for point in points),
    }


def strip_source_rig(bpy_module) -> dict[str, int]:
    removed_armatures = 0
    removed_modifiers = 0
    removed_groups = 0

    for obj in list(bpy_module.context.scene.objects):
        if obj.type == "ARMATURE":
            bpy_module.data.objects.remove(obj, do_unlink=True)
            removed_armatures += 1

    for obj in bpy_module.context.scene.objects:
        if obj.type != "MESH":
            continue
        obj.parent = None
        for modifier in tuple(obj.modifiers):
            if modifier.type == "ARMATURE":
                obj.modifiers.remove(modifier)
                removed_modifiers += 1
        for vertex_group in tuple(obj.vertex_groups):
            obj.vertex_groups.remove(vertex_group)
            removed_groups += 1

    return {
        "removedArmatures": removed_armatures,
        "removedArmatureModifiers": removed_modifiers,
        "removedVertexGroups": removed_groups,
    }


def normalize_mesh_orientation(bpy_module) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    if bpy_module.ops.object.mode_set.poll():
        bpy_module.ops.object.mode_set(mode="OBJECT")

    for obj in bpy_module.context.scene.objects:
        if obj.type != "MESH":
            continue
        plan = orientation_normalization_plan_from_dimensions(tuple(obj.dimensions))
        if plan is None:
            continue
        bpy_module.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy_module.context.view_layer.objects.active = obj
        obj.rotation_euler.rotate_axis(plan["rotationAxis"], plan["rotationRadians"])
        bpy_module.ops.object.transform_apply(location=False, rotation=True, scale=False)
        obj.select_set(False)
        applied.append(
            {
                "objectName": obj.name,
                "sourceUpAxis": plan["sourceUpAxis"],
                "rotationAxis": plan["rotationAxis"],
                "rotationRadians": plan["rotationRadians"],
            }
        )

    return applied


def add_landmarks(bpy_module, landmarks: dict[str, tuple[float, float, float]]) -> None:
    for name, location in landmarks.items():
        bpy_module.ops.object.empty_add(type="SPHERE", location=location)
        landmark = bpy_module.context.object
        landmark.name = f"MGR_Landmark_{name}"
        landmark.empty_display_size = 0.08


def select_meshes(bpy_module) -> list[Any]:
    meshes = [obj for obj in bpy_module.context.scene.objects if obj.type == "MESH"]
    bpy_module.ops.object.select_all(action="DESELECT")
    for mesh in meshes:
        mesh.select_set(True)
    if meshes:
        bpy_module.context.view_layer.objects.active = meshes[0]
    return meshes


def apply_preview_material(bpy_module) -> None:
    material = bpy_module.data.materials.get(preview_material_name())
    if material is None:
        material = bpy_module.data.materials.new(preview_material_name())
    material.diffuse_color = (0.78, 0.78, 0.74, 1.0)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    for node in tuple(nodes):
        nodes.remove(node)
    output = nodes.new(type="ShaderNodeOutputMaterial")
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs["Color"].default_value = (0.78, 0.78, 0.74, 1.0)
    emission.inputs["Strength"].default_value = 1.0
    material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])

    for obj in bpy_module.context.scene.objects:
        if obj.type != "MESH":
            continue
        obj.data.materials.clear()
        obj.data.materials.append(material)


def remove_existing_preview_camera_and_light(bpy_module) -> None:
    for obj in list(bpy_module.context.scene.objects):
        if obj.name.startswith(("MGR_Workflow_Camera", "MGR_Workflow_Key_Light")):
            bpy_module.data.objects.remove(obj, do_unlink=True)


def setup_camera_and_light(
    bpy_module,
    bbox: dict[str, float],
    *,
    axis: str,
) -> dict[str, tuple[float, float, float] | float]:
    from mathutils import Vector

    plan = camera_plan_from_bbox(bbox, axis=axis)
    height = max(bbox["max_z"] - bbox["min_z"], 0.1)
    target = Vector(plan["target"])
    remove_existing_preview_camera_and_light(bpy_module)

    world = bpy_module.context.scene.world
    if world is not None:
        world.color = (0.08, 0.08, 0.08)

    bpy_module.ops.object.light_add(type="AREA", location=plan["keyLightLocation"])
    light = bpy_module.context.object
    light.name = "MGR_Workflow_Key_Light"
    light.data.energy = 900
    light.data.size = max(height, 2.0)

    bpy_module.ops.object.camera_add(location=plan["cameraLocation"])
    camera = bpy_module.context.object
    camera.name = "MGR_Workflow_Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = plan["orthographicScale"]
    camera.data.clip_end = plan["clipEnd"]
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy_module.context.scene.camera = camera
    return plan


def run_operator(label: str, operator_call) -> str:
    result = operator_call()
    if result != {"FINISHED"}:
        raise RuntimeError(f"{label} failed with {result}")
    return "FINISHED"


def render_preview_frame(
    bpy_module,
    preview_path: Path,
    *,
    axis: str,
) -> dict[str, Any]:
    current_bbox = mesh_bbox(bpy_module)
    camera_plan = setup_camera_and_light(bpy_module, current_bbox, axis=axis)
    bpy_module.context.scene.mgr_preview_output_path = str(preview_path)
    run_operator("render_front_preview", bpy_module.ops.mgr.render_front_preview)
    return {
        "bbox": current_bbox,
        "camera": camera_plan,
    }


def run_pose_preview(bpy_module, preview_pose_path: Path, *, axis: str) -> dict[str, Any]:
    operator_name = pose_preview_operator_name()
    run_operator(operator_name, getattr(bpy_module.ops.mgr, operator_name))
    frame = render_preview_frame(bpy_module, preview_pose_path, axis=axis)
    frame["operator"] = operator_name
    return frame


def main() -> int:
    args = parse_args(blender_script_args())
    asset_path = Path(args.asset).expanduser().resolve()
    evidence_dir = Path(args.evidence_dir).expanduser().resolve()
    summary_path = Path(args.summary).expanduser().resolve()
    if not asset_path.exists():
        print(f"Asset not found: {asset_path}", file=sys.stderr)
        return 2

    import bpy

    sys.path.insert(0, str(ADDON_ROOT))
    import mac_game_rigger

    evidence_dir.mkdir(parents=True, exist_ok=True)
    qa_path = evidence_dir / "qa-report.json"
    preview_neutral_path = evidence_dir / "preview-neutral.png"
    preview_pose_path = evidence_dir / "preview-pose.png"
    unity_export_path = evidence_dir / "export-unity.fbx"

    reset_scene(bpy)
    import_asset(bpy, asset_path)
    orientation_result = normalize_mesh_orientation(bpy)
    strip_result = strip_source_rig(bpy)
    imported_bbox = mesh_bbox(bpy)
    apply_preview_material(bpy)
    setup_camera_and_light(bpy, imported_bbox, axis=args.camera_axis)

    mac_game_rigger.register()
    try:
        bpy.context.scene.mgr_current_template = "humanoid"
        add_landmarks(bpy, humanoid_landmarks_from_bbox(imported_bbox))
        run_operator("generate_armature", bpy.ops.mgr.generate_armature)
        run_operator("fix_bone_rolls", bpy.ops.mgr.fix_bone_rolls)

        meshes = select_meshes(bpy)
        run_operator("apply_capsule_weights", bpy.ops.mgr.apply_capsule_weights)
        select_meshes(bpy)
        run_operator("cleanup_weights", bpy.ops.mgr.cleanup_weights)

        bpy.context.scene.mgr_qa_report_path = str(qa_path)
        run_operator("write_qa_report", bpy.ops.mgr.write_qa_report)

        neutral_preview = render_preview_frame(
            bpy,
            preview_neutral_path,
            axis=args.camera_axis,
        )
        pose_preview = run_pose_preview(
            bpy,
            preview_pose_path,
            axis=args.camera_axis,
        )
        run_operator("reset_pose", bpy.ops.mgr.reset_pose)

        select_meshes(bpy)
        bpy.context.scene.mgr_unity_export_path = str(unity_export_path)
        run_operator("export_unity_fbx", bpy.ops.mgr.export_unity_fbx)

        qa_payload = json.loads(qa_path.read_text(encoding="utf-8"))
        export_qa_path = unity_export_path.with_suffix(".qa.json")
        summary = {
            "schemaVersion": 1,
            "status": "pass",
            "assetPath": str(asset_path),
            "stripSourceRig": strip_result,
            "orientationNormalization": orientation_result,
            "meshCount": len(meshes),
            "bbox": imported_bbox,
            "artifacts": {
                "qaReport": str(qa_path),
                "previewNeutral": str(preview_neutral_path),
                "previewPose": str(preview_pose_path),
                "exportUnityFbx": str(unity_export_path),
                "exportQaReport": str(export_qa_path),
            },
            "posePreview": {
                "operator": pose_preview["operator"],
            },
            "camera": {
                "axis": args.camera_axis,
            },
            "previewFrames": {
                "neutral": neutral_preview,
                "pose": pose_preview,
            },
            "qa": qa_payload,
        }
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "pass", "summary": str(summary_path)}, sort_keys=True))
        return 0
    finally:
        mac_game_rigger.unregister()


if __name__ == "__main__":
    raise SystemExit(main())
