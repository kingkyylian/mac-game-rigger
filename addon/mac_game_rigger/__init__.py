from .bl_info import bl_info as bl_info
from .ui.operators import classes as operator_classes
from .ui.operators import register_properties, unregister_properties
from .ui.panels import classes as panel_classes


classes = [*operator_classes, *panel_classes]


def register():
    import bpy

    register_properties()
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unregister_properties()
