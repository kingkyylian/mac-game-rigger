import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon/mac_game_rigger/core/pose_tests.py"
spec = importlib.util.spec_from_file_location("pose_tests", MODULE_PATH)
pose_tests = importlib.util.module_from_spec(spec)
sys.modules["pose_tests"] = pose_tests
spec.loader.exec_module(pose_tests)


class FakePoseBone:
    def __init__(self):
        self.rotation_mode = "QUATERNION"
        self.rotation_euler = (0.0, 0.0, 0.0)


class FakePoseBones(dict):
    def __iter__(self):
        return iter(self.values())


class FakePose:
    def __init__(self, names):
        self.bones = FakePoseBones({name: FakePoseBone() for name in names})


class FakeArmature:
    def __init__(self, names):
        self.pose = FakePose(names)


def test_humanoid_stress_pose_combines_arm_leg_and_neck_stress():
    armature = FakeArmature(
        [
            "UpperArm.L",
            "UpperArm.R",
            "LowerArm.L",
            "LowerArm.R",
            "UpperLeg.L",
            "UpperLeg.R",
            "LowerLeg.L",
            "LowerLeg.R",
            "Neck",
            "Head",
        ]
    )

    result = pose_tests.apply_humanoid_stress_pose(armature)

    assert result.changed_bones == 10
    assert result.missing_bones == ()
    assert armature.pose.bones["UpperArm.L"].rotation_euler == (0.0, 0.0, 0.18)
    assert armature.pose.bones["LowerLeg.L"].rotation_euler == (0.75, 0.0, 0.0)
    assert armature.pose.bones["Neck"].rotation_euler == (0.0, 0.0, 0.45)


def test_humanoid_stress_pose_keeps_arm_spread_within_pose_qa_bounds():
    armature = FakeArmature(["UpperArm.L", "UpperArm.R", "LowerArm.L", "LowerArm.R"])

    pose_tests.apply_humanoid_stress_pose(armature)

    assert abs(armature.pose.bones["UpperArm.L"].rotation_euler[2]) <= 0.2
    assert abs(armature.pose.bones["UpperArm.R"].rotation_euler[2]) <= 0.2
    assert abs(armature.pose.bones["LowerArm.L"].rotation_euler[2]) <= 0.08
    assert abs(armature.pose.bones["LowerArm.R"].rotation_euler[2]) <= 0.08


def test_humanoid_stress_pose_keeps_upper_leg_motion_side_review_friendly():
    armature = FakeArmature(["UpperLeg.L", "UpperLeg.R", "LowerLeg.L", "LowerLeg.R"])

    pose_tests.apply_humanoid_stress_pose(armature)

    assert abs(armature.pose.bones["UpperLeg.L"].rotation_euler[0]) <= 0.12
    assert abs(armature.pose.bones["UpperLeg.R"].rotation_euler[0]) <= 0.12
    assert armature.pose.bones["LowerLeg.L"].rotation_euler[0] >= 0.6
    assert armature.pose.bones["LowerLeg.R"].rotation_euler[0] >= 0.6


def test_humanoid_side_review_pose_omits_arm_swing_for_side_silhouette():
    armature = FakeArmature(
        [
            "UpperArm.L",
            "UpperArm.R",
            "LowerArm.L",
            "LowerArm.R",
            "UpperLeg.L",
            "UpperLeg.R",
            "LowerLeg.L",
            "LowerLeg.R",
            "Neck",
            "Head",
        ]
    )

    result = pose_tests.apply_humanoid_side_review_pose(armature)

    assert result.changed_bones == 4
    assert armature.pose.bones["UpperArm.L"].rotation_euler == (0.0, 0.0, 0.0)
    assert armature.pose.bones["LowerArm.L"].rotation_euler == (0.0, 0.0, 0.0)
    assert armature.pose.bones["UpperLeg.L"].rotation_euler == (-0.1, 0.0, 0.0)
    assert armature.pose.bones["LowerLeg.L"].rotation_euler == (0.75, 0.0, 0.0)
    assert armature.pose.bones["Neck"].rotation_euler == (0.0, 0.0, 0.0)
    assert armature.pose.bones["Head"].rotation_euler == (0.0, 0.0, 0.0)


def test_quadruped_gait_pose_moves_diagonal_leg_pairs_and_tail():
    armature = FakeArmature(
        [
            "FrontUpperLeg.L",
            "FrontLowerLeg.L",
            "FrontPaw.L",
            "FrontUpperLeg.R",
            "FrontLowerLeg.R",
            "FrontPaw.R",
            "RearUpperLeg.L",
            "RearLowerLeg.L",
            "RearPaw.L",
            "RearUpperLeg.R",
            "RearLowerLeg.R",
            "RearPaw.R",
            "Tail.001",
            "Tail.002",
            "Neck",
            "Head",
        ]
    )

    result = pose_tests.apply_quadruped_gait_pose(armature)

    assert result.changed_bones == 16
    assert result.missing_bones == ()
    assert armature.pose.bones["FrontUpperLeg.L"].rotation_euler == (-0.32, 0.0, 0.0)
    assert armature.pose.bones["RearUpperLeg.R"].rotation_euler == (-0.28, 0.0, 0.0)
    assert armature.pose.bones["FrontUpperLeg.R"].rotation_euler == (0.28, 0.0, 0.0)
    assert armature.pose.bones["RearUpperLeg.L"].rotation_euler == (0.32, 0.0, 0.0)
    assert armature.pose.bones["Tail.001"].rotation_euler == (0.0, 0.0, 0.18)
    assert armature.pose.bones["Tail.002"].rotation_euler == (0.0, 0.0, -0.12)


def test_quadruped_side_review_pose_keeps_tail_and_head_neutral():
    armature = FakeArmature(
        [
            "FrontUpperLeg.L",
            "FrontLowerLeg.L",
            "FrontPaw.L",
            "FrontUpperLeg.R",
            "FrontLowerLeg.R",
            "FrontPaw.R",
            "RearUpperLeg.L",
            "RearLowerLeg.L",
            "RearPaw.L",
            "RearUpperLeg.R",
            "RearLowerLeg.R",
            "RearPaw.R",
            "Tail.001",
            "Tail.002",
            "Neck",
            "Head",
        ]
    )

    result = pose_tests.apply_quadruped_side_review_pose(armature)

    assert result.changed_bones == 12
    assert armature.pose.bones["FrontUpperLeg.L"].rotation_euler == (-0.24, 0.0, 0.0)
    assert armature.pose.bones["RearUpperLeg.R"].rotation_euler == (-0.2, 0.0, 0.0)
    assert armature.pose.bones["Tail.001"].rotation_euler == (0.0, 0.0, 0.0)
    assert armature.pose.bones["Head"].rotation_euler == (0.0, 0.0, 0.0)


def test_tail_creature_reach_pose_moves_long_neck_and_tail_without_leg_collapse():
    armature = FakeArmature(
        [
            "FrontUpperLeg.L",
            "FrontUpperLeg.R",
            "RearUpperLeg.L",
            "RearUpperLeg.R",
            "Neck.001",
            "Neck.002",
            "Head",
            "Tail.001",
            "Tail.002",
            "Tail.003",
        ]
    )

    result = pose_tests.apply_tail_creature_reach_pose(armature)

    assert result.changed_bones == 10
    assert result.missing_bones == ()
    assert armature.pose.bones["Neck.001"].rotation_euler == (-0.16, 0.0, 0.0)
    assert armature.pose.bones["Neck.002"].rotation_euler == (0.12, 0.0, 0.0)
    assert armature.pose.bones["Tail.001"].rotation_euler == (0.0, 0.0, 0.12)
    assert armature.pose.bones["Tail.003"].rotation_euler == (0.0, 0.0, -0.06)
    assert abs(armature.pose.bones["FrontUpperLeg.L"].rotation_euler[0]) <= 0.08


def test_tail_creature_side_review_pose_keeps_tail_visible_and_limbs_quiet():
    armature = FakeArmature(
        [
            "FrontUpperLeg.L",
            "FrontUpperLeg.R",
            "RearUpperLeg.L",
            "RearUpperLeg.R",
            "Neck.001",
            "Neck.002",
            "Head",
            "Tail.001",
            "Tail.002",
            "Tail.003",
        ]
    )

    result = pose_tests.apply_tail_creature_side_review_pose(armature)

    assert result.changed_bones == 6
    assert armature.pose.bones["FrontUpperLeg.L"].rotation_euler == (0.0, 0.0, 0.0)
    assert armature.pose.bones["Tail.001"].rotation_euler == (0.0, 0.0, 0.08)
    assert armature.pose.bones["Tail.002"].rotation_euler == (0.0, 0.0, -0.04)
    assert armature.pose.bones["Head"].rotation_euler == (0.02, 0.0, 0.0)


def test_prop_hinge_open_pose_rotates_only_hinge_chain():
    armature = FakeArmature(["PropBase", "Hinge", "MovingPart"])

    result = pose_tests.apply_prop_hinge_open_pose(armature)

    assert result.changed_bones == 2
    assert result.missing_bones == ()
    assert armature.pose.bones["PropBase"].rotation_euler == (0.0, 0.0, 0.0)
    assert armature.pose.bones["Hinge"].rotation_euler == (0.0, 0.0, 0.65)
    assert armature.pose.bones["MovingPart"].rotation_euler == (0.0, 0.0, 0.18)


def test_prop_hinge_open_pose_accepts_artist_angle_and_negative_direction():
    armature = FakeArmature(["PropBase", "Hinge", "MovingPart"])

    result = pose_tests.apply_prop_hinge_open_pose(
        armature,
        open_angle=0.9,
        moving_part_angle=0.25,
        swing_direction="negative",
    )

    assert result.changed_bones == 2
    assert result.missing_bones == ()
    assert armature.pose.bones["PropBase"].rotation_euler == (0.0, 0.0, 0.0)
    assert armature.pose.bones["Hinge"].rotation_euler == (0.0, 0.0, -0.9)
    assert armature.pose.bones["MovingPart"].rotation_euler == (0.0, 0.0, -0.25)


def test_prop_hinge_open_pose_can_rotate_on_artist_selected_axis():
    armature = FakeArmature(["PropBase", "Hinge", "MovingPart"])

    result = pose_tests.apply_prop_hinge_open_pose(
        armature,
        open_angle=0.8,
        moving_part_angle=0.2,
        swing_direction="negative",
        rotation_axis="x",
    )

    assert result.changed_bones == 2
    assert result.missing_bones == ()
    assert armature.pose.bones["PropBase"].rotation_euler == (0.0, 0.0, 0.0)
    assert armature.pose.bones["Hinge"].rotation_euler == (-0.8, 0.0, 0.0)
    assert armature.pose.bones["MovingPart"].rotation_euler == (-0.2, 0.0, 0.0)


def test_prop_hinge_side_review_pose_uses_smaller_hinge_rotation():
    armature = FakeArmature(["PropBase", "Hinge", "MovingPart"])

    result = pose_tests.apply_prop_hinge_side_review_pose(armature)

    assert result.changed_bones == 1
    assert armature.pose.bones["Hinge"].rotation_euler == (0.0, 0.0, 0.35)
    assert armature.pose.bones["MovingPart"].rotation_euler == (0.0, 0.0, 0.0)
