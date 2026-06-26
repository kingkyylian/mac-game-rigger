import importlib.util
from pathlib import Path
import sys

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon/mac_game_rigger/core/weight_binding.py"
spec = importlib.util.spec_from_file_location("weight_binding", MODULE_PATH)
weight_binding = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = weight_binding
spec.loader.exec_module(weight_binding)


def test_distance_point_to_segment_returns_perpendicular_distance_inside_segment():
    distance = weight_binding.distance_point_to_segment(
        point=(1.0, 1.0, 0.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(2.0, 0.0, 0.0),
    )

    assert distance == pytest.approx(1.0)


def test_distance_point_to_segment_clamps_before_segment_start():
    distance = weight_binding.distance_point_to_segment(
        point=(-1.0, 0.0, 0.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(2.0, 0.0, 0.0),
    )

    assert distance == pytest.approx(1.0)


def test_distance_point_to_segment_handles_zero_length_segment():
    distance = weight_binding.distance_point_to_segment(
        point=(0.0, 3.0, 4.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(0.0, 0.0, 0.0),
    )

    assert distance == pytest.approx(5.0)


def test_capsule_weight_falls_off_linearly_until_radius():
    assert weight_binding.capsule_weight(
        point=(0.0, 0.0, 0.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(2.0, 0.0, 0.0),
        radius=1.0,
    ) == pytest.approx(1.0)
    assert weight_binding.capsule_weight(
        point=(0.0, 0.5, 0.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(2.0, 0.0, 0.0),
        radius=1.0,
    ) == pytest.approx(0.5)
    assert weight_binding.capsule_weight(
        point=(0.0, 2.0, 0.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(2.0, 0.0, 0.0),
        radius=1.0,
    ) == pytest.approx(0.0)


def test_capsule_weight_rejects_non_positive_radius():
    with pytest.raises(ValueError, match="radius must be positive"):
        weight_binding.capsule_weight(
            point=(0.0, 0.0, 0.0),
            segment_start=(0.0, 0.0, 0.0),
            segment_end=(1.0, 0.0, 0.0),
            radius=0.0,
        )


def test_normalize_weights_keeps_positive_weights_and_sums_to_one():
    normalized = weight_binding.normalize_weights(
        {"UpperArm.L": 2.0, "Spine": 1.0, "Head": 0.0}
    )

    assert normalized == {
        "UpperArm.L": pytest.approx(2.0 / 3.0),
        "Spine": pytest.approx(1.0 / 3.0),
    }
    assert sum(normalized.values()) == pytest.approx(1.0)


def test_normalize_weights_returns_empty_when_no_positive_weights_exist():
    assert weight_binding.normalize_weights({"Spine": 0.0, "Head": -0.25}) == {}


def test_bone_radius_scale_keeps_limb_capsules_narrower_than_torso():
    torso_scale = weight_binding.bone_radius_scale("Chest", 0.6)
    upper_arm_scale = weight_binding.bone_radius_scale("UpperArm.L", 0.6)
    lower_leg_scale = weight_binding.bone_radius_scale("LowerLeg.R", 0.6)
    hand_scale = weight_binding.bone_radius_scale("Hand.L", 0.6)

    assert torso_scale > 0.6
    assert upper_arm_scale < torso_scale
    assert lower_leg_scale < torso_scale
    assert hand_scale < upper_arm_scale


def test_bone_radius_scale_keeps_torso_core_capsules_wider_than_default():
    hips_scale = weight_binding.bone_radius_scale("Hips", 0.6)
    spine_scale = weight_binding.bone_radius_scale("Spine", 0.6)
    chest_scale = weight_binding.bone_radius_scale("Chest", 0.6)
    upper_arm_scale = weight_binding.bone_radius_scale("UpperArm.L", 0.6)

    assert hips_scale > 0.6
    assert spine_scale > 0.6
    assert chest_scale > 0.6
    assert upper_arm_scale < chest_scale


def test_core_body_capsule_radius_covers_broad_torso_offset():
    radius = weight_binding.bone_radius_scale("Chest", 0.6)

    weight = weight_binding.capsule_weight(
        point=(1.2, 0.0, 0.5),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(0.0, 0.0, 1.0),
        radius=radius,
    )

    assert weight > 0.0


def test_bone_weight_bias_prioritizes_core_body_over_limb_candidates():
    core_bias = weight_binding.bone_weight_bias("Chest")
    limb_bias = weight_binding.bone_weight_bias("UpperArm.L")

    assert core_bias > limb_bias


def test_neck_and_head_do_not_use_torso_capsule_bias():
    assert weight_binding.bone_radius_scale("Neck", 0.6) == pytest.approx(0.6)
    assert weight_binding.bone_radius_scale("Head", 0.6) == pytest.approx(0.6)
    assert weight_binding.bone_weight_bias("Neck") == pytest.approx(1.0)
    assert weight_binding.bone_weight_bias("Head") == pytest.approx(1.0)


def test_top_capsule_weights_preserves_core_body_candidates_for_torso_point():
    bones = [
        {
            "name": "Hips",
            "head": (0.0, 0.0, 0.0),
            "tail": (0.0, 0.0, 1.0),
            "radius": 2.0,
        },
        {
            "name": "Spine",
            "head": (0.0, 0.0, 1.0),
            "tail": (0.0, 0.0, 2.0),
            "radius": 2.0,
        },
        {
            "name": "Chest",
            "head": (0.0, 0.0, 2.0),
            "tail": (0.0, 0.0, 3.0),
            "radius": 2.0,
        },
        {
            "name": "UpperArm.L",
            "head": (0.12, 0.0, 2.0),
            "tail": (0.12, 0.0, 3.0),
            "radius": 1.0,
        },
        {
            "name": "LowerArm.L",
            "head": (0.14, 0.0, 2.0),
            "tail": (0.14, 0.0, 3.0),
            "radius": 1.0,
        },
        {
            "name": "Hand.L",
            "head": (0.16, 0.0, 2.0),
            "tail": (0.16, 0.0, 3.0),
            "radius": 1.0,
        },
    ]

    weights = weight_binding._top_capsule_weights(
        point=(0.0, 0.0, 2.2),
        bones=bones,
        max_influences=4,
    )

    assert {"Hips", "Spine", "Chest"}.issubset(weights)
    assert len(weights) <= 4
    assert sum(weights.values()) == pytest.approx(1.0)


def test_top_capsule_weights_does_not_let_neck_dominate_below_neck_start():
    bones = [
        {
            "name": "Hips",
            "head": (0.0, 0.0, 0.0),
            "tail": (0.0, 0.0, 1.0),
            "radius": 0.25,
        },
        {
            "name": "Spine",
            "head": (0.0, 0.0, 1.0),
            "tail": (0.0, 0.0, 2.0),
            "radius": 0.25,
        },
        {
            "name": "Chest",
            "head": (0.0, 0.0, 2.0),
            "tail": (0.0, 0.0, 3.0),
            "radius": 0.25,
        },
        {
            "name": "Neck",
            "head": (0.0, 0.0, 3.3),
            "tail": (0.0, 0.0, 3.8),
            "radius": 3.0,
        },
    ]

    weights = weight_binding._top_capsule_weights(
        point=(0.4, 0.0, 3.05),
        bones=bones,
        max_influences=4,
    )

    assert weights["Chest"] > weights.get("Neck", 0.0)


def test_capsule_assignment_details_prefers_lower_ratio_limb_over_distal_fallback():
    bones = [
        {
            "name": "LowerLeg.L",
            "head": (0.0, 0.0, 1.0),
            "tail": (0.0, 0.0, 0.0),
            "radius": 0.4,
        },
        {
            "name": "Foot.L",
            "head": (0.0, 0.0, 0.0),
            "tail": (0.0, -0.2, -0.5),
            "radius": 0.2,
        },
    ]

    details = weight_binding.capsule_assignment_details(
        point=(0.9, -0.2, -0.5),
        bones=bones,
        max_influences=4,
    )

    assert details["mode"] == "nearestFallback"
    assert details["weights"] == {"LowerLeg.L": 1.0}
    assert details["nearestBone"] == "LowerLeg.L"
    assert details["nearestDistance"] == pytest.approx(1.0488, abs=0.0001)
    assert details["nearestRadius"] == pytest.approx(0.4)
    assert details["nearestDistanceRatio"] == pytest.approx(2.622, abs=0.0001)
    assert details["nearestBoneRegion"] == "limb"


def test_minimum_bone_coverage_adds_nearest_vertices_for_empty_bone():
    bones = [
        {
            "name": "Hips",
            "head": (0.0, 0.0, 0.0),
            "tail": (0.0, 0.0, 1.0),
            "radius": 1.0,
        },
        {
            "name": "UpperArm.L",
            "head": (5.0, 0.0, 0.0),
            "tail": (5.0, 0.0, 1.0),
            "radius": 1.0,
        },
    ]
    vertex_points = {
        0: (0.0, 0.0, 0.2),
        1: (0.1, 0.0, 0.4),
        2: (5.0, 0.0, 0.5),
    }
    vertex_weights = {
        0: {"UpperArm.L": 1.0},
        1: {"UpperArm.L": 1.0},
        2: {"UpperArm.L": 1.0},
    }

    covered = weight_binding.ensure_minimum_bone_coverage(
        vertex_weights=vertex_weights,
        vertex_points=vertex_points,
        bones=bones,
        min_vertices_per_bone=2,
        max_influences=4,
    )

    assert "Hips" in covered[0]
    assert "Hips" in covered[1]
    assert "Hips" not in covered[2]
    assert sum("Hips" in weights for weights in covered.values()) == 2
    assert all(sum(weights.values()) == pytest.approx(1.0) for weights in covered.values())


def test_minimum_bone_coverage_spreads_crowded_empty_bones_across_vertices():
    bones = [
        {
            "name": "Hips",
            "head": (0.0, 0.0, 0.0),
            "tail": (0.0, 0.0, 1.0),
            "radius": 1.0,
        },
        {
            "name": "Spine",
            "head": (0.0, 0.0, 0.0),
            "tail": (0.0, 0.0, 1.0),
            "radius": 1.0,
        },
        {
            "name": "Chest",
            "head": (0.0, 0.0, 0.0),
            "tail": (0.0, 0.0, 1.0),
            "radius": 1.0,
        },
    ]
    vertex_points = {
        0: (0.0, 0.0, 0.1),
        1: (0.0, 0.0, 0.2),
        2: (0.0, 0.0, 0.3),
    }
    vertex_weights = {
        0: {"UpperArm.L": 0.5, "LowerArm.L": 0.5},
        1: {"UpperArm.L": 0.5, "LowerArm.L": 0.5},
        2: {"UpperArm.L": 0.5, "LowerArm.L": 0.5},
    }

    covered = weight_binding.ensure_minimum_bone_coverage(
        vertex_weights=vertex_weights,
        vertex_points=vertex_points,
        bones=bones,
        min_vertices_per_bone=1,
        max_influences=2,
    )

    assert any("Hips" in weights for weights in covered.values())
    assert any("Spine" in weights for weights in covered.values())
    assert any("Chest" in weights for weights in covered.values())
    assert all(len(weights) <= 2 for weights in covered.values())
    assert all(sum(weights.values()) == pytest.approx(1.0) for weights in covered.values())


def test_minimum_bone_coverage_uses_smaller_target_for_distal_bones():
    bones = [
        {
            "name": "Hand.L",
            "head": (0.0, 0.0, 0.0),
            "tail": (0.0, 0.0, 1.0),
            "radius": 1.0,
        }
    ]
    vertex_points = {
        index: (0.0, 0.0, index * 0.1)
        for index in range(8)
    }
    vertex_weights = {
        index: {"Chest": 1.0}
        for index in vertex_points
    }

    covered = weight_binding.ensure_minimum_bone_coverage(
        vertex_weights=vertex_weights,
        vertex_points=vertex_points,
        bones=bones,
        min_vertices_per_bone=8,
        max_influences=4,
    )

    assert sum("Hand.L" in weights for weights in covered.values()) == 2


def test_minimum_bone_coverage_scales_distal_targets_and_makes_them_dominant_on_large_meshes():
    bones = [
        {
            "name": "Foot.L",
            "head": (0.0, 0.0, 0.0),
            "tail": (0.0, 0.0, 1.0),
            "radius": 1.0,
        }
    ]
    vertex_points = {
        index: (0.0, 0.0, index / 1000.0)
        for index in range(1000)
    }
    vertex_weights = {
        index: {"Chest": 1.0}
        for index in vertex_points
    }

    covered = weight_binding.ensure_minimum_bone_coverage(
        vertex_weights=vertex_weights,
        vertex_points=vertex_points,
        bones=bones,
        min_vertices_per_bone=8,
        max_influences=4,
    )

    foot_dominant_vertices = [
        weights for weights in covered.values()
        if weights.get("Foot.L", 0.0) > weights.get("Chest", 0.0)
    ]
    assert len(foot_dominant_vertices) >= 13


def test_capsule_diagnostics_report_world_space_vertical_bounds():
    class FakeMatrix:
        def __matmul__(self, value):
            return value

    class FakeBone:
        def __init__(self, name, head, tail):
            self.name = name
            self.head_local = head
            self.tail_local = tail
            self.use_deform = True

    class FakeArmatureData:
        bones = [
            FakeBone("Chest", (0.0, 0.0, 1.0), (0.0, 0.0, 2.0)),
            FakeBone("Neck", (0.0, 0.0, 2.0), (0.0, 0.0, 2.4)),
        ]

    class FakeArmature:
        matrix_world = FakeMatrix()
        data = FakeArmatureData()

    diagnostics = weight_binding.capsule_diagnostics(FakeArmature())

    assert diagnostics[0]["name"] == "Chest"
    assert diagnostics[0]["verticalMin"] == pytest.approx(1.0)
    assert diagnostics[0]["verticalMax"] == pytest.approx(2.0)
    assert diagnostics[0]["radius"] > diagnostics[1]["radius"]


def test_mesh_bind_vertex_points_normalizes_raw_vertices_to_world_bbox_space():
    class FakeMatrix:
        def __matmul__(self, value):
            return value

    class FakeVertex:
        def __init__(self, index, co):
            self.index = index
            self.co = co

    class FakeMeshData:
        vertices = [
            FakeVertex(0, (0.0, 0.0, 0.0)),
            FakeVertex(1, (0.0, 0.0, 100.0)),
        ]

    class FakeMesh:
        matrix_world = FakeMatrix()
        bound_box = [
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
        ]
        data = FakeMeshData()

    points = weight_binding.mesh_bind_vertex_points(FakeMesh())

    assert points[0] == pytest.approx((0.0, 0.0, 0.0))
    assert points[1] == pytest.approx((0.0, 0.0, 1.0))


def test_mesh_bind_vertex_points_accepts_explicit_target_bounds():
    class FakeMatrix:
        def __matmul__(self, value):
            return value

    class FakeVertex:
        def __init__(self, index, co):
            self.index = index
            self.co = co

    class FakeMeshData:
        vertices = [
            FakeVertex(0, (0.0, 0.0, 0.0)),
            FakeVertex(1, (10.0, 10.0, 100.0)),
        ]

    class FakeMesh:
        matrix_world = FakeMatrix()
        bound_box = []
        data = FakeMeshData()

    points = weight_binding.mesh_bind_vertex_points(
        FakeMesh(),
        target_bounds={
            "min": (-1.0, -2.0, -3.0),
            "max": (1.0, 2.0, 3.0),
        },
    )

    assert points[0] == pytest.approx((-1.0, -2.0, -3.0))
    assert points[1] == pytest.approx((1.0, 2.0, 3.0))
