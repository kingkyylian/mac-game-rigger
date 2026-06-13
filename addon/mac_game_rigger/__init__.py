from .bl_info import bl_info
from .ui.panels import classes as panel_classes


classes = [*panel_classes]


def register():
    import bpy

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

