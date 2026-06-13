import bpy


LANDMARK_PREFIX = "MGR_Landmark_"


class MGR_OT_analyze_asset(bpy.types.Operator):
    bl_idname = "mgr.analyze_asset"
    bl_label = "Analyze Selected Mesh"
    bl_options = {"REGISTER"}

    def execute(self, context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not selected_meshes:
            self.report({"WARNING"}, "Select at least one mesh to analyze")
            context.scene.pop("mgr_last_analysis", None)
            return {"CANCELLED"}

        mesh = selected_meshes[0]
        message = f"Selected mesh: {mesh.name}"
        context.scene["mgr_last_analysis"] = message
        self.report({"INFO"}, message)
        return {"FINISHED"}


class MGR_OT_create_landmark(bpy.types.Operator):
    bl_idname = "mgr.create_landmark"
    bl_label = "Create Landmark"
    bl_options = {"REGISTER", "UNDO"}

    landmark_name: bpy.props.StringProperty(name="Landmark Name", default="")

    def execute(self, context):
        landmark_name = (self.landmark_name or context.scene.mgr_landmark_name).strip()
        if not landmark_name:
            self.report({"WARNING"}, "Enter a landmark name")
            return {"CANCELLED"}

        bpy.ops.object.empty_add(type="SPHERE", location=context.scene.cursor.location)
        landmark = context.object
        landmark.name = f"{LANDMARK_PREFIX}{landmark_name}"
        landmark.empty_display_size = 0.15
        self.report({"INFO"}, f"Created {landmark.name}")
        return {"FINISHED"}


class MGR_OT_clear_landmarks(bpy.types.Operator):
    bl_idname = "mgr.clear_landmarks"
    bl_label = "Clear Landmarks"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        landmarks = [obj for obj in context.scene.objects if obj.name.startswith(LANDMARK_PREFIX)]
        for landmark in landmarks:
            bpy.data.objects.remove(landmark, do_unlink=True)

        self.report({"INFO"}, f"Cleared {len(landmarks)} landmarks")
        return {"FINISHED"}


def register_properties():
    bpy.types.Scene.mgr_landmark_name = bpy.props.StringProperty(
        name="Landmark Name",
        default="hips",
    )


def unregister_properties():
    if hasattr(bpy.types.Scene, "mgr_landmark_name"):
        del bpy.types.Scene.mgr_landmark_name


classes = [MGR_OT_analyze_asset, MGR_OT_create_landmark, MGR_OT_clear_landmarks]
