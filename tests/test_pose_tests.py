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
    assert armature.pose.bones["UpperArm.L"].rotation_euler == (0.0, 0.0, 1.1)
    assert armature.pose.bones["LowerLeg.L"].rotation_euler == (0.75, 0.0, 0.0)
    assert armature.pose.bones["Neck"].rotation_euler == (0.0, 0.0, 0.45)
