from __future__ import annotations

from pathlib import Path


def render_preview_png(bpy_module, output_path: Path, resolution: int = 512) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy_module.context.scene
    scene.render.filepath = str(output_path)
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.film_transparent = False

    if not bpy_module.app.background and bpy_module.ops.render.opengl.poll():
        try:
            bpy_module.ops.render.opengl(write_still=True, view_context=False)
            return output_path
        except RuntimeError:
            pass

    _ensure_camera(bpy_module)
    bpy_module.ops.render.render(write_still=True)
    return output_path


def _ensure_camera(bpy_module) -> None:
    scene = bpy_module.context.scene
    if scene.camera is not None:
        return
    bpy_module.ops.object.camera_add(
        location=(0.0, -4.0, 1.5),
        rotation=(1.5708, 0.0, 0.0),
    )
    scene.camera = bpy_module.context.object
