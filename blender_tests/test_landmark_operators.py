import sys
from pathlib import Path
import traceback

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "addon"))

import mac_game_rigger  # noqa: E402


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)


def landmark_names():
    return {obj.name for obj in bpy.context.scene.objects if obj.name.startswith("MGR_Landmark_")}


def run_test():
    reset_scene()

    bpy.context.scene.cursor.location = (1.0, -2.0, 3.5)
    bpy.context.scene.mgr_landmark_name = "hips"

    create_result = bpy.ops.mgr.create_landmark()
    assert create_result == {"FINISHED"}

    landmark = bpy.data.objects["MGR_Landmark_hips"]
    assert landmark.type == "EMPTY"
    assert landmark.empty_display_type == "SPHERE"
    assert tuple(round(value, 4) for value in landmark.location) == (1.0, -2.0, 3.5)

    bpy.ops.object.empty_add(type="CUBE", location=(9.0, 9.0, 9.0))
    regular_empty = bpy.context.object
    regular_empty.name = "Regular_Empty"

    bpy.context.scene.mgr_landmark_name = "head"
    second_result = bpy.ops.mgr.create_landmark()
    assert second_result == {"FINISHED"}
    assert landmark_names() == {"MGR_Landmark_hips", "MGR_Landmark_head"}

    clear_result = bpy.ops.mgr.clear_landmarks()
    assert clear_result == {"FINISHED"}
    assert landmark_names() == set()
    assert "Regular_Empty" in bpy.data.objects


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_LANDMARK_OPERATORS_TEST_OK")
