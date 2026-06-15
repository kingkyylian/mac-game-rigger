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


def add_report_test_mesh():
    mesh_data = bpy.data.meshes.new("MGR_QA_Report_Test_Data")
    mesh_data.from_pydata(
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)],
        [],
        [],
    )
    mesh_data.update()
    mesh = bpy.data.objects.new("MGR_QA_Report_Test_Mesh", mesh_data)
    bpy.context.collection.objects.link(mesh)

    for name in ("A", "B", "C", "D", "E"):
        group = mesh.vertex_groups.new(name=name)
        group.add([1], 0.2, "REPLACE")
    return mesh


def add_report_test_armature():
    bpy.ops.object.armature_add(location=(0.0, 0.0, 0.0))
    armature = bpy.context.object
    armature.name = "MGR_Armature"
    return armature


def run_test():
    reset_scene()
    mesh = add_report_test_mesh()
    add_report_test_armature()
    output_path = Path(tempfile.gettempdir()) / "mac_game_rigger_qa_report_operator.json"
    if output_path.exists():
        output_path.unlink()

    bpy.context.scene.mgr_qa_report_path = str(output_path)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh

    assert bpy.ops.mgr.write_qa_report() == {"FINISHED"}
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["mesh_count"] == 1
    assert payload["vertex_count"] == 3
    assert payload["bone_count"] == 1
    assert payload["unweighted_vertices"] == 2
    assert payload["over_limit_vertices"] == 1
    assert payload["warnings"] == ["Unweighted vertices: 2", "Over-limit vertices: 1"]
    assert payload["errors"] == []
    assert bpy.context.scene.mgr_qa_report_message == f"Wrote QA report: {output_path}"


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_QA_REPORT_OPERATOR_TEST_OK")
