import json
import sys
from pathlib import Path
import tempfile
import traceback

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "addon"))

import mac_game_rigger  # noqa: E402


def reset_scene():
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def add_landmark(name, location):
    bpy.ops.object.empty_add(type="SPHERE", location=location)
    bpy.context.object.name = f"MGR_Landmark_{name}"


def seed_full_humanoid():
    template_path = REPO_ROOT / "addon/mac_game_rigger/templates/humanoid.json"
    required = tuple(json.loads(template_path.read_text(encoding="utf-8"))["required_landmarks"])
    for index, name in enumerate(required):
        x = -0.4 if name.endswith(".R") else 0.4 if name.endswith(".L") else 0.0
        add_landmark(name, (x, index * 0.01, 0.5 + index * 0.08))


def run_test():
    reset_scene()
    bpy.context.scene.mgr_current_template = "humanoid"
    seed_full_humanoid()
    assert bpy.ops.mgr.generate_armature() == {"FINISHED"}
    armature = bpy.data.objects["MGR_Armature"]

    bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0.0, 0.0, 1.0))
    mesh = bpy.context.object
    mesh.name = "MGR_Unity_Export_Mesh"

    export_path = Path(tempfile.gettempdir()) / "mac_game_rigger_unity_export.fbx"
    qa_path = export_path.with_suffix(".qa.json")
    for path in (export_path, qa_path):
        if path.exists():
            path.unlink()

    bpy.context.scene.mgr_unity_export_path = str(export_path)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = mesh

    assert bpy.ops.mgr.export_unity_fbx() == {"FINISHED"}
    assert export_path.exists()
    assert export_path.stat().st_size > 0
    assert qa_path.exists()

    payload = json.loads(qa_path.read_text(encoding="utf-8"))
    assert payload["export_profile"] == "unity_fbx"
    assert payload["mesh_count"] >= 1
    assert payload["bone_count"] == len(armature.data.bones)
    assert "Unity FBX" in bpy.context.scene.mgr_export_message
    assert "add_leaf_bones=False" in bpy.context.scene.mgr_export_message


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_UNITY_FBX_EXPORT_OPERATOR_TEST_OK")
