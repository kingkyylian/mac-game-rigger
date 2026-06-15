import json
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


def add_landmark(name, location):
    bpy.ops.object.empty_add(type="SPHERE", location=location)
    bpy.context.object.name = f"MGR_Landmark_{name}"


def seed_full_humanoid():
    template_path = REPO_ROOT / "addon/mac_game_rigger/templates/humanoid.json"
    required = tuple(json.loads(template_path.read_text(encoding="utf-8"))["required_landmarks"])
    for index, name in enumerate(required):
        x = -0.4 if name.endswith(".R") else 0.4 if name.endswith(".L") else 0.0
        add_landmark(name, (x, index * 0.01, 0.5 + index * 0.08))


def vertex_influence_total(mesh, vertex):
    return sum(
        group.weight
        for group in vertex.groups
        if mesh.vertex_groups[group.group].name in {vg.name for vg in mesh.vertex_groups}
    )


def run_test():
    reset_scene()
    bpy.context.scene.mgr_current_template = "humanoid"
    seed_full_humanoid()
    assert bpy.ops.mgr.generate_armature() == {"FINISHED"}
    armature = bpy.data.objects["MGR_Armature"]

    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, radius=0.45, location=(0.0, 0.0, 1.0))
    mesh = bpy.context.object
    mesh.name = "MGR_Capsule_Bind_Test_Mesh"

    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = mesh

    result = bpy.ops.mgr.apply_capsule_weights()
    assert result == {"FINISHED"}

    assert any(modifier.type == "ARMATURE" for modifier in mesh.modifiers)
    assert len(mesh.vertex_groups) > 0
    assert all(vertex.groups for vertex in mesh.data.vertices)
    assert all(len(vertex.groups) <= 4 for vertex in mesh.data.vertices)
    for vertex in mesh.data.vertices:
        assert abs(vertex_influence_total(mesh, vertex) - 1.0) < 0.001
    assert bpy.context.scene["mgr_last_capsule_weighted_vertices"] == len(mesh.data.vertices)


mac_game_rigger.register()
try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    mac_game_rigger.unregister()

print("MGR_CAPSULE_WEIGHTS_OPERATOR_TEST_OK")
