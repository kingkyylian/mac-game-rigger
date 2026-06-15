from __future__ import annotations

from pathlib import Path

from .export_profiles import ExportProfile


def export_fbx_with_profile(bpy_module, output_path: Path, profile: ExportProfile) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy_module.ops.export_scene.fbx(
        filepath=str(output_path),
        use_selection=profile.use_selection,
        global_scale=profile.global_scale,
        apply_unit_scale=profile.apply_unit_scale,
        add_leaf_bones=profile.add_leaf_bones,
        axis_forward=profile.forward_axis,
        axis_up=profile.up_axis,
    )
    return output_path
