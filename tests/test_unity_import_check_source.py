from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER_SOURCE = REPO_ROOT / "tools/unity_import_check/Assets/Editor/MacGameRiggerFbxImportCheck.cs"


def test_unity_import_checker_records_instantiation_and_import_metadata():
    source = CHECKER_SOURCE.read_text(encoding="utf-8")

    assert "PrefabUtility.InstantiatePrefab" in source
    assert "ModelImporter" in source
    assert "instantiated" in source
    assert "skinnedMeshRendererCount" in source
    assert "meshFilterCount" in source
    assert "animationType" in source


def test_unity_import_checker_records_bone_transform_smoke_metadata():
    source = CHECKER_SOURCE.read_text(encoding="utf-8")

    assert ".bones" in source
    assert "Quaternion.Angle" in source
    assert "skinnedMeshRendererCount > 0 && !boneTransformSmoke.passed" in source
    assert "boneTransformSmoke" in source
    assert "boneCandidateCount" in source
    assert "testedBone" in source
    assert "rotationDeltaDegrees" in source


def test_unity_import_checker_records_animation_clip_sampling_smoke_metadata():
    source = CHECKER_SOURCE.read_text(encoding="utf-8")

    assert "AnimationClip" in source
    assert "AnimationCurve.Linear" in source
    assert "SampleAnimation" in source
    assert "animationClipSmoke" in source
    assert "sampledBone" in source
    assert "sampledRotationDeltaDegrees" in source
    assert "skinnedMeshRendererCount > 0 && !animationClipSmoke.passed" in source


def test_unity_import_checker_records_configured_animator_smoke_metadata():
    source = CHECKER_SOURCE.read_text(encoding="utf-8")

    assert "UnityEditor.Animations" in source
    assert "AnimatorController" in source
    assert "RunConfiguredAnimatorSmoke" in source
    assert "configuredAnimatorSmoke" in source
    assert "controllerAssigned" in source
    assert "stateCount" in source
    assert "skinnedMeshRendererCount > 0 && !configuredAnimatorSmoke.passed" in source


def test_unity_import_checker_records_humanoid_avatar_smoke_metadata():
    source = CHECKER_SOURCE.read_text(encoding="utf-8")

    assert "AvatarBuilder.BuildHumanAvatar" in source
    assert "HumanDescription" in source
    assert "HumanTrait.BoneName" in source
    assert "RunHumanoidAvatarSmoke" in source
    assert "humanoidAvatarSmoke" in source
    assert "avatarIsValid" in source
    assert "avatarIsHuman" in source
    assert "mappedHumanBoneCount" in source


def test_unity_import_checker_records_bounds_smoke_metadata():
    source = CHECKER_SOURCE.read_text(encoding="utf-8")

    assert "Renderer[] renderers" in source
    assert ".bounds" in source
    assert "boundsSmoke" in source
    assert "boundsCenter" in source
    assert "boundsSize" in source
    assert "boundsHeight" in source
    assert "maxDimension" in source
    assert "rendererCount > 0 && !boundsSmoke.passed" in source
