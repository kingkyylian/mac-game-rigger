import json
import sys
from pathlib import Path
import tempfile
import traceback

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "addon"))

import mac_game_rigger  # noqa: E402


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


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


def seed_preview_scene():
    bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0.0, 0.0, 1.1))
    bpy.context.object.name = "MGR_Preview_Test_Mesh"
    bpy.ops.object.light_add(type="AREA", location=(0.0, -3.0, 4.0))
    bpy.context.object.name = "MGR_Preview_Light"
    bpy.ops.object.camera_add(location=(0.0, -4.0, 1.4), rotation=(1.5708, 0.0, 0.0))
    bpy.context.scene.camera = bpy.context.object


def assert_png(path):
    assert path.exists()
    assert path.read_bytes()[:8] == PNG_SIGNATURE


def run_test():
    reset_scene()
    seed_preview_scene()
    bpy.context.scene.mgr_current_template = "humanoid"
    seed_full_humanoid()
    assert bpy.ops.mgr.generate_armature() == {"FINISHED"}

    output_dir = Path(tempfile.gettempdir())
    front_path = output_dir / "mac_game_rigger_front_preview.png"
    pose_path = output_dir / "mac_game_rigger_pose_preview.png"
    for path in (front_path, pose_path):
        if path.exists():
            path.unlink()

    bpy.context.scene.mgr_preview_output_path = str(front_path)
    assert bpy.ops.mgr.render_front_preview() == {"FINISHED"}
    assert_png(front_path)

    bpy.context.scene.mgr_preview_output_path = str(pose_path)
    assert bpy.ops.mgr.render_pose_preview() == {"FINISHED"}
    assert_png(pose_path)
    assert bpy.context.scene.mgr_preview_message == f"Wrote preview PNG: {pose_path}"


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_PREVIEW_OPERATOR_TEST_OK")
