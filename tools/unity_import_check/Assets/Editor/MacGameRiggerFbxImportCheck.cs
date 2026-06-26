using System.IO;
using System.Globalization;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

public static class MacGameRiggerFbxImportCheck
{
    public static void Run()
    {
        const string importFolder = "Assets/MacGameRiggerImportCandidate";
        string resultFolder = "Library/MacGameRiggerImportCheck";
        Directory.CreateDirectory(resultFolder);
        string resultPath = Path.Combine(resultFolder, "result.json");

        string assetPath = Directory.GetFiles(importFolder, "*.fbx", SearchOption.TopDirectoryOnly)
            .Select(path => path.Replace("\\", "/"))
            .FirstOrDefault();

        if (string.IsNullOrEmpty(assetPath))
        {
            WriteFailure(resultPath, "", "No FBX file found");
            EditorApplication.Exit(1);
            return;
        }

        AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceUpdate);
        GameObject asset = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
        if (asset == null)
        {
            WriteFailure(resultPath, assetPath, "AssetDatabase returned null");
            EditorApplication.Exit(1);
            return;
        }

        GameObject instance = PrefabUtility.InstantiatePrefab(asset) as GameObject;
        if (instance == null)
        {
            instance = Object.Instantiate(asset);
        }

        if (instance == null)
        {
            WriteFailure(resultPath, assetPath, "Imported asset could not be instantiated");
            EditorApplication.Exit(1);
            return;
        }

        int childCount = instance.GetComponentsInChildren<Transform>(true).Length;
        Renderer[] renderers = instance.GetComponentsInChildren<Renderer>(true);
        int rendererCount = renderers.Length;
        SkinnedMeshRenderer[] skinnedMeshRenderers = instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);
        int skinnedMeshRendererCount = skinnedMeshRenderers.Length;
        int meshFilterCount = instance.GetComponentsInChildren<MeshFilter>(true).Length;
        int animatorCount = instance.GetComponentsInChildren<Animator>(true).Length;
        BoundsSmokeResult boundsSmoke = RunBoundsSmoke(renderers);
        BoneTransformSmokeResult boneTransformSmoke = RunBoneTransformSmoke(skinnedMeshRenderers);
        AnimationClipSmokeResult animationClipSmoke = RunAnimationClipSmoke(instance, skinnedMeshRenderers);
        ConfiguredAnimatorSmokeResult configuredAnimatorSmoke = RunConfiguredAnimatorSmoke(instance, skinnedMeshRenderers);
        animatorCount = instance.GetComponentsInChildren<Animator>(true).Length;
        ModelImporter modelImporter = AssetImporter.GetAtPath(assetPath) as ModelImporter;

        if (rendererCount == 0 && meshFilterCount == 0 && skinnedMeshRendererCount == 0)
        {
            Object.DestroyImmediate(instance);
            WriteFailure(resultPath, assetPath, "Imported asset instance has no renderable mesh components");
            EditorApplication.Exit(1);
            return;
        }

        if (rendererCount > 0 && !boundsSmoke.passed)
        {
            Object.DestroyImmediate(instance);
            WriteFailure(resultPath, assetPath, "Imported asset instance has invalid renderer bounds");
            EditorApplication.Exit(1);
            return;
        }

        if (skinnedMeshRendererCount > 0 && !boneTransformSmoke.passed)
        {
            Object.DestroyImmediate(instance);
            WriteFailure(resultPath, assetPath, "Skinned mesh renderer has no mutable bone transform smoke pass");
            EditorApplication.Exit(1);
            return;
        }

        if (skinnedMeshRendererCount > 0 && !animationClipSmoke.passed)
        {
            Object.DestroyImmediate(instance);
            WriteFailure(resultPath, assetPath, "Skinned mesh renderer has no animation clip sampling smoke pass");
            EditorApplication.Exit(1);
            return;
        }

        if (skinnedMeshRendererCount > 0 && !configuredAnimatorSmoke.passed)
        {
            Object.DestroyImmediate(instance);
            WriteFailure(resultPath, assetPath, "Skinned mesh renderer has no configured Animator smoke pass");
            EditorApplication.Exit(1);
            return;
        }

        File.WriteAllText(
            resultPath,
            BuildPassJson(
                assetPath,
                asset.name,
                childCount,
                rendererCount,
                skinnedMeshRendererCount,
                meshFilterCount,
                animatorCount,
                boundsSmoke,
                boneTransformSmoke,
                animationClipSmoke,
                configuredAnimatorSmoke,
                modelImporter
            )
        );
        Object.DestroyImmediate(instance);
        EditorApplication.Exit(0);
    }

    private static void WriteFailure(string resultPath, string assetPath, string error)
    {
        var json = new StringBuilder();
        json.Append("{\"status\":\"fail\"");
        if (!string.IsNullOrEmpty(assetPath))
        {
            json.Append(",\"assetPath\":").Append(JsonString(assetPath));
        }
        json.Append(",\"error\":").Append(JsonString(error)).Append("}");
        File.WriteAllText(resultPath, json.ToString());
    }

    private static string BuildPassJson(
        string assetPath,
        string assetName,
        int childCount,
        int rendererCount,
        int skinnedMeshRendererCount,
        int meshFilterCount,
        int animatorCount,
        BoundsSmokeResult boundsSmoke,
        BoneTransformSmokeResult boneTransformSmoke,
        AnimationClipSmokeResult animationClipSmoke,
        ConfiguredAnimatorSmokeResult configuredAnimatorSmoke,
        ModelImporter modelImporter
    )
    {
        var json = new StringBuilder();
        json.Append("{");
        json.Append("\"status\":\"pass\"");
        json.Append(",\"assetPath\":").Append(JsonString(assetPath));
        json.Append(",\"assetName\":").Append(JsonString(assetName));
        json.Append(",\"instantiated\":true");
        json.Append(",\"childCount\":").Append(childCount);
        json.Append(",\"rendererCount\":").Append(rendererCount);
        json.Append(",\"skinnedMeshRendererCount\":").Append(skinnedMeshRendererCount);
        json.Append(",\"meshFilterCount\":").Append(meshFilterCount);
        json.Append(",\"animatorCount\":").Append(animatorCount);
        json.Append(",\"boundsSmoke\":{");
        json.Append("\"passed\":").Append(boundsSmoke.passed ? "true" : "false");
        json.Append(",\"boundsCenter\":").Append(JsonVector3(boundsSmoke.bounds.center));
        json.Append(",\"boundsSize\":").Append(JsonVector3(boundsSmoke.bounds.size));
        json.Append(",\"boundsHeight\":").Append(boundsSmoke.bounds.size.y.ToString("R", CultureInfo.InvariantCulture));
        json.Append(",\"maxDimension\":").Append(boundsSmoke.maxDimension.ToString("R", CultureInfo.InvariantCulture));
        if (!string.IsNullOrEmpty(boundsSmoke.error))
        {
            json.Append(",\"error\":").Append(JsonString(boundsSmoke.error));
        }
        json.Append("}");
        json.Append(",\"boneTransformSmoke\":{");
        json.Append("\"passed\":").Append(boneTransformSmoke.passed ? "true" : "false");
        json.Append(",\"boneCandidateCount\":").Append(boneTransformSmoke.boneCandidateCount);
        json.Append(",\"testedBone\":").Append(JsonString(boneTransformSmoke.testedBone));
        json.Append(",\"rotationDeltaDegrees\":").Append(boneTransformSmoke.rotationDeltaDegrees.ToString("R", CultureInfo.InvariantCulture));
        if (!string.IsNullOrEmpty(boneTransformSmoke.error))
        {
            json.Append(",\"error\":").Append(JsonString(boneTransformSmoke.error));
        }
        json.Append("}");
        json.Append(",\"animationClipSmoke\":{");
        json.Append("\"passed\":").Append(animationClipSmoke.passed ? "true" : "false");
        json.Append(",\"sampledBone\":").Append(JsonString(animationClipSmoke.sampledBone));
        json.Append(",\"sampledBonePath\":").Append(JsonString(animationClipSmoke.sampledBonePath));
        json.Append(",\"sampledRotationDeltaDegrees\":").Append(animationClipSmoke.sampledRotationDeltaDegrees.ToString("R", CultureInfo.InvariantCulture));
        if (!string.IsNullOrEmpty(animationClipSmoke.error))
        {
            json.Append(",\"error\":").Append(JsonString(animationClipSmoke.error));
        }
        json.Append("}");
        json.Append(",\"configuredAnimatorSmoke\":{");
        json.Append("\"passed\":").Append(configuredAnimatorSmoke.passed ? "true" : "false");
        json.Append(",\"animatorCount\":").Append(configuredAnimatorSmoke.animatorCount);
        json.Append(",\"controllerAssigned\":").Append(configuredAnimatorSmoke.controllerAssigned ? "true" : "false");
        json.Append(",\"stateCount\":").Append(configuredAnimatorSmoke.stateCount);
        json.Append(",\"sampledBone\":").Append(JsonString(configuredAnimatorSmoke.sampledBone));
        json.Append(",\"sampledBonePath\":").Append(JsonString(configuredAnimatorSmoke.sampledBonePath));
        json.Append(",\"sampledRotationDeltaDegrees\":").Append(configuredAnimatorSmoke.sampledRotationDeltaDegrees.ToString("R", CultureInfo.InvariantCulture));
        if (!string.IsNullOrEmpty(configuredAnimatorSmoke.error))
        {
            json.Append(",\"error\":").Append(JsonString(configuredAnimatorSmoke.error));
        }
        json.Append("}");
        json.Append(",\"modelImporter\":{");
        if (modelImporter == null)
        {
            json.Append("\"available\":false");
        }
        else
        {
            json.Append("\"available\":true");
            json.Append(",\"animationType\":").Append(JsonString(modelImporter.animationType.ToString()));
            json.Append(",\"importAnimation\":").Append(modelImporter.importAnimation ? "true" : "false");
            json.Append(",\"globalScale\":").Append(modelImporter.globalScale.ToString("R", CultureInfo.InvariantCulture));
        }
        json.Append("}}");
        return json.ToString();
    }

    private static BoundsSmokeResult RunBoundsSmoke(Renderer[] renderers)
    {
        Renderer firstRenderer = renderers.FirstOrDefault(renderer => renderer != null);
        if (firstRenderer == null)
        {
            return new BoundsSmokeResult(false, new Bounds(Vector3.zero, Vector3.zero), 0f, "No renderers found");
        }

        Bounds bounds = firstRenderer.bounds;
        foreach (Renderer renderer in renderers)
        {
            if (renderer != null)
            {
                bounds.Encapsulate(renderer.bounds);
            }
        }

        Vector3 center = bounds.center;
        Vector3 size = bounds.size;
        float maxDimension = Mathf.Max(size.x, Mathf.Max(size.y, size.z));
        bool finite = IsFinite(center.x)
            && IsFinite(center.y)
            && IsFinite(center.z)
            && IsFinite(size.x)
            && IsFinite(size.y)
            && IsFinite(size.z);
        bool positive = maxDimension > 0.001f && size.y > 0.001f;

        return new BoundsSmokeResult(
            finite && positive,
            bounds,
            maxDimension,
            finite && positive ? "" : "Renderer bounds are not finite or positive"
        );
    }

    private static BoneTransformSmokeResult RunBoneTransformSmoke(SkinnedMeshRenderer[] skinnedMeshRenderers)
    {
        Transform[] boneCandidates = BoneCandidates(skinnedMeshRenderers);

        if (boneCandidates.Length == 0)
        {
            return new BoneTransformSmokeResult(false, 0, "", 0f, "No SkinnedMeshRenderer bone links found");
        }

        Transform testedBone = boneCandidates[0];
        Quaternion originalRotation = testedBone.localRotation;
        testedBone.localRotation = Quaternion.Euler(0f, 5f, 0f) * originalRotation;
        float rotationDeltaDegrees = Quaternion.Angle(originalRotation, testedBone.localRotation);
        testedBone.localRotation = originalRotation;

        return new BoneTransformSmokeResult(
            rotationDeltaDegrees > 0.001f,
            boneCandidates.Length,
            testedBone.name,
            rotationDeltaDegrees,
            rotationDeltaDegrees > 0.001f ? "" : "Bone rotation did not change"
        );
    }

    private static AnimationClipSmokeResult RunAnimationClipSmoke(
        GameObject instance,
        SkinnedMeshRenderer[] skinnedMeshRenderers
    )
    {
        Transform[] boneCandidates = BoneCandidates(skinnedMeshRenderers);
        if (boneCandidates.Length == 0)
        {
            return new AnimationClipSmokeResult(false, "", "", 0f, "No SkinnedMeshRenderer bone links found");
        }

        Transform sampledBone = boneCandidates[0];
        string sampledBonePath = TransformPath(instance.transform, sampledBone);
        if (string.IsNullOrEmpty(sampledBonePath))
        {
            return new AnimationClipSmokeResult(false, sampledBone.name, "", 0f, "Could not resolve sampled bone path");
        }

        Quaternion originalRotation = sampledBone.localRotation;
        Vector3 originalEuler = sampledBone.localEulerAngles;

        var clip = new AnimationClip();
        clip.legacy = true;
        clip.SetCurve(
            sampledBonePath,
            typeof(Transform),
            "localEulerAnglesRaw.y",
            AnimationCurve.Linear(0f, originalEuler.y, 1f, originalEuler.y + 7.5f)
        );
        clip.SampleAnimation(instance, 1f);
        float sampledRotationDeltaDegrees = Quaternion.Angle(originalRotation, sampledBone.localRotation);
        sampledBone.localRotation = originalRotation;

        return new AnimationClipSmokeResult(
            sampledRotationDeltaDegrees > 0.001f,
            sampledBone.name,
            sampledBonePath,
            sampledRotationDeltaDegrees,
            sampledRotationDeltaDegrees > 0.001f ? "" : "AnimationClip sampling did not change bone rotation"
        );
    }

    private static ConfiguredAnimatorSmokeResult RunConfiguredAnimatorSmoke(
        GameObject instance,
        SkinnedMeshRenderer[] skinnedMeshRenderers
    )
    {
        Transform[] boneCandidates = BoneCandidates(skinnedMeshRenderers);
        if (boneCandidates.Length == 0)
        {
            return new ConfiguredAnimatorSmokeResult(false, 0, false, 0, "", "", 0f, "No SkinnedMeshRenderer bone links found");
        }

        Transform sampledBone = boneCandidates[0];
        string sampledBonePath = TransformPath(instance.transform, sampledBone);
        if (string.IsNullOrEmpty(sampledBonePath))
        {
            return new ConfiguredAnimatorSmokeResult(false, 0, false, 0, sampledBone.name, "", 0f, "Could not resolve sampled bone path");
        }

        Animator animator = instance.GetComponent<Animator>();
        if (animator == null)
        {
            animator = instance.AddComponent<Animator>();
        }

        var clip = new AnimationClip();
        clip.name = "MacGameRiggerConfiguredAnimatorSmokeClip";
        clip.legacy = false;
        Vector3 originalEuler = sampledBone.localEulerAngles;
        Quaternion originalRotation = sampledBone.localRotation;
        clip.SetCurve(
            sampledBonePath,
            typeof(Transform),
            "localEulerAnglesRaw.y",
            AnimationCurve.Linear(0f, originalEuler.y, 1f, originalEuler.y + 7.5f)
        );

        const string controllerPath = "Assets/MacGameRiggerImportCandidate/MacGameRiggerConfiguredAnimatorSmoke.controller";
        AssetDatabase.DeleteAsset(controllerPath);
        AnimatorController controller = AnimatorController.CreateAnimatorControllerAtPath(controllerPath);
        AnimatorState state = controller.layers[0].stateMachine.AddState("Smoke");
        state.motion = clip;
        animator.runtimeAnimatorController = controller;
        animator.applyRootMotion = false;
        animator.enabled = true;

        clip.SampleAnimation(instance, 1f);
        float sampledRotationDeltaDegrees = Quaternion.Angle(originalRotation, sampledBone.localRotation);
        sampledBone.localRotation = originalRotation;

        int animatorCount = instance.GetComponentsInChildren<Animator>(true).Length;
        bool controllerAssigned = animator.runtimeAnimatorController != null;
        int stateCount = controller.layers[0].stateMachine.states.Length;
        bool passed = animatorCount > 0
            && controllerAssigned
            && stateCount > 0
            && sampledRotationDeltaDegrees > 0.001f;

        return new ConfiguredAnimatorSmokeResult(
            passed,
            animatorCount,
            controllerAssigned,
            stateCount,
            sampledBone.name,
            sampledBonePath,
            sampledRotationDeltaDegrees,
            passed ? "" : "Configured Animator smoke did not create a controller state that samples bone rotation"
        );
    }

    private static Transform[] BoneCandidates(SkinnedMeshRenderer[] skinnedMeshRenderers)
    {
        return skinnedMeshRenderers
            .SelectMany(renderer => renderer.bones ?? new Transform[0])
            .Where(bone => bone != null)
            .Distinct()
            .ToArray();
    }

    private static string TransformPath(Transform root, Transform target)
    {
        if (root == target)
        {
            return "";
        }

        string path = target.name;
        Transform current = target.parent;
        while (current != null && current != root)
        {
            path = current.name + "/" + path;
            current = current.parent;
        }

        return current == root ? path : "";
    }

    private struct BoneTransformSmokeResult
    {
        public readonly bool passed;
        public readonly int boneCandidateCount;
        public readonly string testedBone;
        public readonly float rotationDeltaDegrees;
        public readonly string error;

        public BoneTransformSmokeResult(
            bool passed,
            int boneCandidateCount,
            string testedBone,
            float rotationDeltaDegrees,
            string error
        )
        {
            this.passed = passed;
            this.boneCandidateCount = boneCandidateCount;
            this.testedBone = testedBone;
            this.rotationDeltaDegrees = rotationDeltaDegrees;
            this.error = error;
        }
    }

    private struct BoundsSmokeResult
    {
        public readonly bool passed;
        public readonly Bounds bounds;
        public readonly float maxDimension;
        public readonly string error;

        public BoundsSmokeResult(bool passed, Bounds bounds, float maxDimension, string error)
        {
            this.passed = passed;
            this.bounds = bounds;
            this.maxDimension = maxDimension;
            this.error = error;
        }
    }

    private struct AnimationClipSmokeResult
    {
        public readonly bool passed;
        public readonly string sampledBone;
        public readonly string sampledBonePath;
        public readonly float sampledRotationDeltaDegrees;
        public readonly string error;

        public AnimationClipSmokeResult(
            bool passed,
            string sampledBone,
            string sampledBonePath,
            float sampledRotationDeltaDegrees,
            string error
        )
        {
            this.passed = passed;
            this.sampledBone = sampledBone;
            this.sampledBonePath = sampledBonePath;
            this.sampledRotationDeltaDegrees = sampledRotationDeltaDegrees;
            this.error = error;
        }
    }

    private struct ConfiguredAnimatorSmokeResult
    {
        public readonly bool passed;
        public readonly int animatorCount;
        public readonly bool controllerAssigned;
        public readonly int stateCount;
        public readonly string sampledBone;
        public readonly string sampledBonePath;
        public readonly float sampledRotationDeltaDegrees;
        public readonly string error;

        public ConfiguredAnimatorSmokeResult(
            bool passed,
            int animatorCount,
            bool controllerAssigned,
            int stateCount,
            string sampledBone,
            string sampledBonePath,
            float sampledRotationDeltaDegrees,
            string error
        )
        {
            this.passed = passed;
            this.animatorCount = animatorCount;
            this.controllerAssigned = controllerAssigned;
            this.stateCount = stateCount;
            this.sampledBone = sampledBone;
            this.sampledBonePath = sampledBonePath;
            this.sampledRotationDeltaDegrees = sampledRotationDeltaDegrees;
            this.error = error;
        }
    }

    private static string JsonString(string value)
    {
        return "\"" + value
            .Replace("\\", "\\\\")
            .Replace("\"", "\\\"")
            .Replace("\n", "\\n")
            .Replace("\r", "\\r") + "\"";
    }

    private static string JsonVector3(Vector3 value)
    {
        return "{\"x\":"
            + value.x.ToString("R", CultureInfo.InvariantCulture)
            + ",\"y\":"
            + value.y.ToString("R", CultureInfo.InvariantCulture)
            + ",\"z\":"
            + value.z.ToString("R", CultureInfo.InvariantCulture)
            + "}";
    }

    private static bool IsFinite(float value)
    {
        return !float.IsNaN(value) && !float.IsInfinity(value);
    }
}
