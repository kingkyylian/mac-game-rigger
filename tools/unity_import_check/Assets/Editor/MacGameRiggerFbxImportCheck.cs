using System.IO;
using System.Linq;
using UnityEditor;
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
            File.WriteAllText(resultPath, "{\"status\":\"fail\",\"error\":\"No FBX file found\"}");
            EditorApplication.Exit(1);
            return;
        }

        AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceUpdate);
        GameObject asset = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
        if (asset == null)
        {
            File.WriteAllText(resultPath, "{\"status\":\"fail\",\"assetPath\":\"" + assetPath + "\",\"error\":\"AssetDatabase returned null\"}");
            EditorApplication.Exit(1);
            return;
        }

        File.WriteAllText(resultPath, "{\"status\":\"pass\",\"assetPath\":\"" + assetPath + "\"}");
        EditorApplication.Exit(0);
    }
}
