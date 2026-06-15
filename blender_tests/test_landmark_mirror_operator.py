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


def add_landmark(name, location):
    bpy.ops.object.empty_add(type="SPHERE", location=location)
    landmark = bpy.context.object
    landmark.name = f"MGR_Landmark_{name}"
    return landmark


def rounded_location(obj):
    return tuple(round(value, 4) for value in obj.location)


def run_test():
    reset_scene()

    add_landmark("shoulder.L", (1.2, 0.5, 2.0))
    add_landmark("upper_arm.L", (1.6, 0.4, 1.7))
    existing_right = add_landmark("upper_arm.R", (9.0, 9.0, 9.0))

    result = bpy.ops.mgr.mirror_landmarks()
    assert result == {"FINISHED"}

    assert "MGR_Landmark_shoulder.R" in bpy.data.objects
    shoulder_right = bpy.data.objects["MGR_Landmark_shoulder.R"]
    assert shoulder_right.type == "EMPTY"
    assert shoulder_right.empty_display_type == "SPHERE"
    assert rounded_location(shoulder_right) == (-1.2, 0.5, 2.0)

    assert "MGR_Landmark_upper_arm.R" in bpy.data.objects
    assert bpy.data.objects["MGR_Landmark_upper_arm.R"] == existing_right
    assert rounded_location(existing_right) == (-1.6, 0.4, 1.7)


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_LANDMARK_MIRROR_TEST_OK")
