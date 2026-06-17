#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
ADDON_ROOT = REPO_ROOT / "addon"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import an asset in headless Blender and write basic scene metrics."
    )
    parser.add_argument("--slot", required=True, help="Asset manifest slot id, e.g. H-001.")
    parser.add_argument("--asset", required=True, help="FBX, GLB/GLTF, OBJ, or BLEND asset path.")
    parser.add_argument("--output", required=True, help="JSON output path.")
    parser.add_argument("--source-name", required=True, help="Human-readable source asset name.")
    parser.add_argument("--source-url", required=True, help="Source page or download URL.")
    parser.add_argument("--license", required=True, help="Source asset license.")
    return parser.parse_args(argv)


def blender_script_args() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def reset_scene(bpy_module) -> None:
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


def object_bbox(objects) -> dict[str, float]:
    from mathutils import Vector

    points = []
    for obj in objects:
        if not hasattr(obj, "bound_box"):
            continue
        world = obj.matrix_world
        points.extend(world @ Vector(corner) for corner in obj.bound_box)

    if not points:
        return {"width": 0.0, "depth": 0.0, "height": 0.0}

    min_x = min(point.x for point in points)
    max_x = max(point.x for point in points)
    min_y = min(point.y for point in points)
    max_y = max(point.y for point in points)
    min_z = min(point.z for point in points)
    max_z = max(point.z for point in points)
    return {
        "width": round(max_x - min_x, 4),
        "depth": round(max_y - min_y, 4),
        "height": round(max_z - min_z, 4),
    }


def collect_metrics(bpy_module):
    sys.path.insert(0, str(ADDON_ROOT))
    from mac_game_rigger.core.asset_analysis import MeshStats, suggest_category

    meshes = [obj for obj in bpy_module.context.scene.objects if obj.type == "MESH"]
    armatures = [obj for obj in bpy_module.context.scene.objects if obj.type == "ARMATURE"]
    materials = {
        slot.material.name
        for obj in meshes
        for slot in obj.material_slots
        if slot.material is not None
    }
    bbox = object_bbox(meshes)
    vertex_count = sum(len(obj.data.vertices) for obj in meshes)
    face_count = sum(len(obj.data.polygons) for obj in meshes)
    bone_count = sum(len(obj.data.bones) for obj in armatures)
    stats = MeshStats(
        mesh_count=len(meshes),
        vertex_count=vertex_count,
        face_count=face_count,
        width=bbox["width"],
        depth=bbox["depth"],
        height=bbox["height"],
        has_armature=bool(armatures),
    )

    return {
        "meshCount": len(meshes),
        "armatureCount": len(armatures),
        "boneCount": bone_count,
        "materialCount": len(materials),
        "vertexCount": vertex_count,
        "faceCount": face_count,
        "actionCount": len(bpy_module.data.actions),
        "bbox": bbox,
        "hasArmature": bool(armatures),
        "suggestedCategory": suggest_category(stats),
        "meshNames": [obj.name for obj in meshes],
        "armatureNames": [obj.name for obj in armatures],
    }


def main() -> int:
    args = parse_args(blender_script_args())
    asset_path = Path(args.asset).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if not asset_path.exists():
        print(f"Asset not found: {asset_path}", file=sys.stderr)
        return 2

    import bpy

    reset_scene(bpy)
    import_asset(bpy, asset_path)
    metrics = collect_metrics(bpy)
    payload = {
        "schemaVersion": 1,
        "status": "pass" if metrics["meshCount"] > 0 else "fail",
        "slotId": args.slot,
        "source": {
            "name": args.source_name,
            "url": args.source_url,
            "license": args.license,
            "localPath": str(asset_path),
        },
        "metrics": metrics,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output": str(output_path)}, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
