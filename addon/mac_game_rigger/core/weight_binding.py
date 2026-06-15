from __future__ import annotations


def selected_meshes(context) -> list:
    return [obj for obj in context.selected_objects if obj.type == "MESH"]


def find_mgr_armature(bpy_module):
    armature = bpy_module.data.objects.get("MGR_Armature")
    if armature is None or armature.type != "ARMATURE":
        return None
    return armature
