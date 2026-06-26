import importlib
import sys
import types


class FakeSceneType:
    pass


class FakeProps:
    @staticmethod
    def StringProperty(**kwargs):
        return {"type": "StringProperty", **kwargs}

    @staticmethod
    def EnumProperty(**kwargs):
        return {"type": "EnumProperty", **kwargs}

    @staticmethod
    def FloatProperty(**kwargs):
        return {"type": "FloatProperty", **kwargs}


def install_fake_bpy(monkeypatch):
    fake_bpy = types.SimpleNamespace(
        types=types.SimpleNamespace(
            Operator=object,
            Panel=object,
            GizmoGroup=object,
            Scene=FakeSceneType,
        ),
        props=FakeProps(),
    )
    monkeypatch.setitem(sys.modules, "bpy", fake_bpy)
    monkeypatch.setitem(
        sys.modules,
        "mathutils",
        types.SimpleNamespace(Vector=lambda value: value),
    )
    return fake_bpy


def import_ui_modules(monkeypatch):
    install_fake_bpy(monkeypatch)
    for module_name in [
        "addon.mac_game_rigger",
        "addon.mac_game_rigger.ui.operators",
        "addon.mac_game_rigger.ui.panels",
    ]:
        sys.modules.pop(module_name, None)
    operators = importlib.import_module("addon.mac_game_rigger.ui.operators")
    panels = importlib.import_module("addon.mac_game_rigger.ui.panels")
    return operators, panels


def test_register_properties_adds_prop_hinge_pivot_and_base_scene_controls(monkeypatch):
    operators, _panels = import_ui_modules(monkeypatch)

    operators.register_properties()

    assert FakeSceneType.mgr_prop_hinge_pivot_x == {
        "type": "FloatProperty",
        "name": "Prop Hinge Pivot X",
        "default": 0.16,
        "min": 0.0,
        "max": 1.0,
    }
    assert FakeSceneType.mgr_prop_hinge_base_x == {
        "type": "FloatProperty",
        "name": "Prop Hinge Base X",
        "default": 0.28,
        "min": 0.0,
        "max": 1.0,
    }
    assert FakeSceneType.mgr_prop_hinge_axis == {
        "type": "EnumProperty",
        "name": "Prop Hinge Axis",
        "items": (
            ("x", "X Axis", "Lay out hinge chain along the asset X axis"),
            ("y", "Y Axis", "Lay out hinge chain along the asset Y axis"),
        ),
        "default": "x",
    }
    assert FakeSceneType.mgr_prop_hinge_open_angle == {
        "type": "FloatProperty",
        "name": "Prop Hinge Open Angle",
        "default": 0.65,
        "min": 0.0,
        "max": 1.5708,
    }
    assert FakeSceneType.mgr_prop_hinge_swing_direction == {
        "type": "EnumProperty",
        "name": "Prop Hinge Swing Direction",
        "items": (
            ("positive", "Positive Z", "Open the hinge along positive Z rotation"),
            ("negative", "Negative Z", "Open the hinge along negative Z rotation"),
        ),
        "default": "positive",
    }
    assert FakeSceneType.mgr_prop_hinge_rotation_axis == {
        "type": "EnumProperty",
        "name": "Prop Hinge Rotation Axis",
        "items": (
            ("x", "X Rotation", "Rotate the hinge pose around the local X axis"),
            ("y", "Y Rotation", "Rotate the hinge pose around the local Y axis"),
            ("z", "Z Rotation", "Rotate the hinge pose around the local Z axis"),
        ),
        "default": "z",
    }

    operators.unregister_properties()

    assert not hasattr(FakeSceneType, "mgr_prop_hinge_pivot_x")
    assert not hasattr(FakeSceneType, "mgr_prop_hinge_base_x")
    assert not hasattr(FakeSceneType, "mgr_prop_hinge_axis")
    assert not hasattr(FakeSceneType, "mgr_prop_hinge_open_angle")
    assert not hasattr(FakeSceneType, "mgr_prop_hinge_swing_direction")
    assert not hasattr(FakeSceneType, "mgr_prop_hinge_rotation_axis")


class FakeLayout:
    def __init__(self):
        self.props = []
        self.labels = []
        self.operators = []

    def label(self, *, text):
        self.labels.append(text)

    def prop(self, scene, name):
        self.props.append(name)

    def operator(self, operator_id, *, text):
        self.operators.append((operator_id, text))

    def separator(self):
        pass


class FakeGizmo:
    def __init__(self, gizmo_type):
        self.gizmo_type = gizmo_type
        self.target_bindings = []
        self.matrix_basis = None

    def target_set_prop(self, target, data, property_name, *, index=-1):
        self.target_bindings.append((target, data, property_name, index))


class FakeGizmos:
    def __init__(self):
        self.created = []

    def new(self, gizmo_type):
        gizmo = FakeGizmo(gizmo_type)
        self.created.append(gizmo)
        return gizmo


class FakeGuide:
    def __init__(self, matrix_world):
        self.location = [0.0, 0.0, 0.0]
        self.matrix_world = matrix_world


class FakeScene:
    mgr_landmark_name = "hips"
    mgr_current_template = "prop_hinge"
    mgr_prop_hinge_pivot_x = 0.08
    mgr_prop_hinge_base_x = 0.18
    mgr_prop_hinge_axis = "y"
    mgr_prop_hinge_open_angle = 0.9
    mgr_prop_hinge_swing_direction = "negative"
    mgr_prop_hinge_rotation_axis = "x"
    mgr_qa_report_path = "qa.json"
    mgr_preview_output_path = "preview.png"
    mgr_unity_export_path = "unity.fbx"
    mgr_unreal_export_path = "unreal.fbx"
    mgr_landmark_validation_message = ""
    mgr_weight_cleanup_message = ""
    mgr_pose_test_message = ""
    mgr_qa_report_message = ""
    mgr_preview_message = ""
    mgr_export_message = ""


def test_main_panel_draws_prop_hinge_pivot_and_base_controls_for_prop_template(monkeypatch):
    _operators, panels = import_ui_modules(monkeypatch)
    panel = panels.MGR_PT_main_panel()
    layout = FakeLayout()
    panel.layout = layout
    context = types.SimpleNamespace(scene=FakeScene())

    panel.draw(context)

    assert "Prop Hinge Controls" in layout.labels
    assert "mgr_prop_hinge_pivot_x" in layout.props
    assert "mgr_prop_hinge_base_x" in layout.props
    assert "mgr_prop_hinge_axis" in layout.props
    assert "mgr_prop_hinge_open_angle" in layout.props
    assert "mgr_prop_hinge_swing_direction" in layout.props
    assert "mgr_prop_hinge_rotation_axis" in layout.props


def test_prop_hinge_landmark_helper_uses_ui_pivot_and_base_values(monkeypatch):
    operators, _panels = import_ui_modules(monkeypatch)
    bbox = {
        "min_x": 0.0,
        "max_x": 10.0,
        "min_y": -1.0,
        "max_y": 1.0,
        "min_z": 2.0,
        "max_z": 6.0,
    }

    landmarks = operators.prop_hinge_landmarks_from_bbox(
        bbox,
        hinge_pivot_x=0.08,
        base_origin_x=0.18,
    )

    assert landmarks == {
        "base": (1.8, 0.0, 2.64),
        "hinge": (0.8, 0.0, 4.0),
        "moving_part": (4.5, 0.0, 4.0),
        "moving_tip": (9.2, 0.0, 4.0),
    }


def test_prop_hinge_landmark_helper_can_use_y_axis_for_chest_like_props(monkeypatch):
    operators, _panels = import_ui_modules(monkeypatch)
    bbox = {
        "min_x": 0.0,
        "max_x": 10.0,
        "min_y": -2.0,
        "max_y": 8.0,
        "min_z": 2.0,
        "max_z": 6.0,
    }

    landmarks = operators.prop_hinge_landmarks_from_bbox(
        bbox,
        hinge_pivot_x=0.10,
        base_origin_x=0.22,
        layout_axis="y",
    )

    assert landmarks == {
        "base": (5.0, 0.2, 2.64),
        "hinge": (5.0, -1.0, 4.0),
        "moving_part": (5.0, 2.5, 4.0),
        "moving_tip": (5.0, 7.2, 4.0),
    }


def test_prop_hinge_visual_guide_helper_builds_axis_and_swing_markers(monkeypatch):
    operators, _panels = import_ui_modules(monkeypatch)
    bbox = {
        "min_x": 0.0,
        "max_x": 10.0,
        "min_y": -1.0,
        "max_y": 1.0,
        "min_z": 2.0,
        "max_z": 6.0,
    }
    landmarks = operators.prop_hinge_landmarks_from_bbox(
        bbox,
        hinge_pivot_x=0.08,
        base_origin_x=0.18,
    )

    guides = operators.prop_hinge_visual_guides_from_bbox(bbox, landmarks)

    assert guides == {
        "prop_hinge_axis_bottom": (0.8, 0.0, 2.0),
        "prop_hinge_axis_top": (0.8, 0.0, 6.0),
        "prop_hinge_pivot": (0.8, 0.0, 4.0),
        "prop_hinge_swing_tip": (9.2, 0.0, 4.0),
    }


def test_prop_hinge_landmarks_can_be_committed_from_dragged_visual_guides(monkeypatch):
    operators, _panels = import_ui_modules(monkeypatch)

    landmarks = operators.prop_hinge_landmarks_from_guides(
        base_position=(1.0, 0.0, 2.64),
        pivot_position=(0.5, -0.5, 4.0),
        swing_tip_position=(5.5, 3.5, 4.8),
    )

    assert landmarks == {
        "base": (1.0, 0.0, 2.64),
        "hinge": (0.5, -0.5, 4.0),
        "moving_part": (2.75, 1.3, 4.36),
        "moving_tip": (5.5, 3.5, 4.8),
    }


def test_prop_hinge_visual_guide_operators_are_registered_and_drawn(monkeypatch):
    operators, panels = import_ui_modules(monkeypatch)
    operator_ids = {operator.bl_idname for operator in operators.classes}

    assert "mgr.generate_prop_hinge_landmarks" in operator_ids
    assert "mgr.refresh_prop_hinge_visual_guides" in operator_ids
    assert "mgr.commit_prop_hinge_guides" in operator_ids

    panel = panels.MGR_PT_main_panel()
    layout = FakeLayout()
    panel.layout = layout
    context = types.SimpleNamespace(scene=FakeScene())

    panel.draw(context)

    assert (
        "mgr.generate_prop_hinge_landmarks",
        "Generate Prop Hinge Landmarks",
    ) in layout.operators
    assert (
        "mgr.refresh_prop_hinge_visual_guides",
        "Refresh Hinge Visual Guides",
    ) in layout.operators
    assert (
        "mgr.commit_prop_hinge_guides",
        "Commit Hinge Guides",
    ) in layout.operators


def test_prop_hinge_custom_gizmo_group_is_registered_for_prop_template(monkeypatch):
    operators, _panels = import_ui_modules(monkeypatch)
    gizmo_group = next(
        cls
        for cls in operators.classes
        if getattr(cls, "bl_idname", "") == "MGR_GGT_prop_hinge_orientation"
    )

    assert gizmo_group.bl_label == "Prop Hinge Orientation Gizmo"
    assert gizmo_group.bl_space_type == "VIEW_3D"
    assert gizmo_group.bl_region_type == "WINDOW"
    assert {"3D", "PERSISTENT"}.issubset(gizmo_group.bl_options)
    assert gizmo_group.poll(types.SimpleNamespace(scene=FakeScene()))
    assert not gizmo_group.poll(
        types.SimpleNamespace(scene=types.SimpleNamespace(mgr_current_template="humanoid"))
    )


def test_prop_hinge_gizmo_group_binds_pivot_and_swing_tip_axis_handles(monkeypatch):
    operators, _panels = import_ui_modules(monkeypatch)
    gizmo_group_cls = next(
        cls
        for cls in operators.classes
        if getattr(cls, "bl_idname", "") == "MGR_GGT_prop_hinge_orientation"
    )
    pivot = FakeGuide(matrix_world="pivot-matrix")
    swing_tip = FakeGuide(matrix_world="swing-tip-matrix")
    operators.bpy.data = types.SimpleNamespace(
        objects={
            "MGR_Gizmo_prop_hinge_pivot": pivot,
            "MGR_Gizmo_prop_hinge_swing_tip": swing_tip,
        }
    )
    group = gizmo_group_cls()
    group.gizmos = FakeGizmos()

    group.setup(types.SimpleNamespace(scene=FakeScene()))
    group.draw_prepare(types.SimpleNamespace(scene=FakeScene()))

    assert len(group.gizmos.created) == 6
    assert {gizmo.gizmo_type for gizmo in group.gizmos.created} == {"GIZMO_GT_arrow_3d"}
    assert set(group._guide_handles) == {"pivot", "swing_tip"}
    assert set(group._guide_handles["pivot"]) == {"x", "y", "z"}
    assert set(group._guide_handles["swing_tip"]) == {"x", "y", "z"}
    assert group._guide_handles["pivot"]["x"].target_bindings == [
        ("offset", pivot, "location", 0)
    ]
    assert group._guide_handles["pivot"]["y"].target_bindings == [
        ("offset", pivot, "location", 1)
    ]
    assert group._guide_handles["pivot"]["z"].target_bindings == [
        ("offset", pivot, "location", 2)
    ]
    assert group._guide_handles["swing_tip"]["x"].target_bindings == [
        ("offset", swing_tip, "location", 0)
    ]
    assert group._guide_handles["swing_tip"]["y"].target_bindings == [
        ("offset", swing_tip, "location", 1)
    ]
    assert group._guide_handles["swing_tip"]["z"].target_bindings == [
        ("offset", swing_tip, "location", 2)
    ]
    assert group._guide_handles["pivot"]["x"].matrix_basis == "pivot-matrix"
    assert group._guide_handles["swing_tip"]["x"].matrix_basis == "swing-tip-matrix"
