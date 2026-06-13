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
    bpy.context.scene.pop("mgr_last_analysis", None)


def run_test():
    reset_scene()

    no_selection_result = bpy.ops.mgr.analyze_asset()
    assert no_selection_result == {"CANCELLED"}
    assert "mgr_last_analysis" not in bpy.context.scene

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    mesh_obj = bpy.context.object
    mesh_obj.name = "MGR_Test_Mesh"

    selected_result = bpy.ops.mgr.analyze_asset()
    assert selected_result == {"FINISHED"}
    assert bpy.context.scene["mgr_last_analysis"] == "Selected mesh: MGR_Test_Mesh"


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_ANALYZE_OPERATOR_TEST_OK")
