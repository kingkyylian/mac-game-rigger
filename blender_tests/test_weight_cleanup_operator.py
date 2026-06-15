import sys
from pathlib import Path
import traceback

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "addon"))

import mac_game_rigger  # noqa: E402


def reset_scene():
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def add_cleanup_test_mesh():
    mesh_data = bpy.data.meshes.new("MGR_Cleanup_Test_Data")
    mesh_data.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)],
        [],
        [],
    )
    mesh_data.update()
    mesh = bpy.data.objects.new("MGR_Cleanup_Test_Mesh", mesh_data)
    bpy.context.collection.objects.link(mesh)

    groups = {name: mesh.vertex_groups.new(name=name) for name in ("A", "B", "C", "D", "E")}
    mesh.vertex_groups.new(name="Empty")

    for group in groups.values():
        group.add([1], 0.2, "REPLACE")
    groups["A"].add([2], 0.0001, "REPLACE")
    groups["B"].add([2], 0.9999, "REPLACE")
    return mesh


def group_names(mesh):
    return {vertex_group.name for vertex_group in mesh.vertex_groups}


def vertex_weight_total(vertex):
    return sum(group.weight for group in vertex.groups)


def run_test():
    reset_scene()
    mesh = add_cleanup_test_mesh()
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh

    result = bpy.ops.mgr.cleanup_weights()
    assert result == {"FINISHED"}

    assert "Empty" not in group_names(mesh)
    assert len(mesh.data.vertices[0].groups) == 0
    assert len(mesh.data.vertices[1].groups) == 5
    assert len(mesh.data.vertices[2].groups) == 1
    assert abs(vertex_weight_total(mesh.data.vertices[2]) - 1.0) < 0.001

    message = bpy.context.scene.mgr_weight_cleanup_message
    assert "unweighted=1" in message
    assert "over_limit=1" in message
    assert "removed_empty=1" in message
    assert "pruned=1" in message
    assert "normalized=1" in message


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_WEIGHT_CLEANUP_OPERATOR_TEST_OK")
