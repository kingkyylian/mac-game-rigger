# Alpha Smoke Results

Date: 2026-06-15

This smoke pass combines generated Blender proxy scenes for full rig workflow timing with five real open sample assets from the Khronos glTF Sample Assets repository for import coverage. Real licensed production studio characters have not been added to the repository yet, so deformation quality still needs production art validation.

Engine import status is now verified for the generated Unity FBX export. Unity Editor was found at `/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity`; sandboxed batchmode still cannot run because Unity Package Manager cannot open its local socket, but sandbox-external batchmode imports `/var/folders/jg/ppc_rfwj63v8qprgfw63k3pr0000gn/T/mac_game_rigger_unity_export.fbx` successfully after restarting a stale Unity Licensing Client process.

## Summary

| Slot ID | Category | Proxy Asset | Template | Time To First Rig | Cleanup Minutes | Deformation Score | FBX Export | Engine Import | Accepted | Notes |
|---|---|---|---|---:|---:|---:|---|---|---|---|
| H-001 | humanoid | generated clean neutral biped proxy | Humanoid | 0.3 | 10 | 3 | pass | pass: Unity batchmode import verifier | accepted for alpha smoke | Full landmark -> armature -> capsule weights -> QA -> Unity FBX path passed in headless Blender and Unity import. |
| H-006 | humanoid | generated low-poly biped proxy | Humanoid | 0.3 | 15 | 3 | pass | not individually imported | needs review | Low-poly proxy validates deterministic bone generation and fallback weights; real low-poly silhouette still needs manual review. |
| H-010 | humanoid | generated thin-limb biped proxy | Humanoid | 0.4 | 20 | 3 | pass | not individually imported | needs review | Capsule weighting produced bounded influences; thin-limb production assets remain a cleanup risk. |
| Q-001 | quadruped | generated quadruped dog proxy | Quadruped | 0.4 | 30 | 2 | pass | not individually imported | needs review | Quadruped template loads and exports, but deformation quality needs real four-leg asset validation. |
| C-001 | tail/wing creature | generated creature proxy | Quadruped + Tail + Wing | 0.5 | 45 | 2 | pass | not individually imported | needs review | Current alpha has no dedicated wing helper yet; result is useful as a failure visibility baseline. |

## Real Sample Asset Import Baseline

Source: temporary checkout of `KhronosGroup/glTF-Sample-Assets` under `/private/tmp/gltf-sample-assets`.

| Asset ID | Asset | Category | Format | Meshes | Armatures | Actions | Blender Import | Notes |
|---|---|---|---|---:|---:|---:|---|---|
| R-001 | CesiumMan | humanoid character | GLB | 2 | 1 | 1 | pass | Rigged humanoid sample imported through Blender glTF importer. |
| R-002 | Fox | quadruped creature | GLB | 2 | 1 | 3 | pass | Rigged animated quadruped sample imported through Blender glTF importer. |
| R-003 | BrainStem | organic rigged asset | GLB | 2 | 1 | 1 | pass | Rigged organic sample imported through Blender glTF importer. |
| R-004 | CesiumMilkTruck | vehicle prop | GLB | 3 | 0 | 1 | pass | Non-character game asset import baseline. |
| R-005 | DamagedHelmet | hard-surface prop | GLB | 1 | 0 | 0 | pass | Static prop import baseline. |

## Verification Commands

```bash
python3 -m pytest tests -q
blender --background --factory-startup --python blender_tests/test_generate_armature_operator.py
blender --background --factory-startup --python blender_tests/test_capsule_weights_operator.py
blender --background --factory-startup --python blender_tests/test_weight_cleanup_operator.py
blender --background --factory-startup --python blender_tests/test_pose_tests_operator.py
blender --background --factory-startup --python blender_tests/test_qa_report_operator.py
blender --background --factory-startup --python blender_tests/test_unity_fbx_export_operator.py
blender --background --factory-startup --python blender_tests/test_unreal_fbx_export_operator.py
python3 -m pytest tests/test_unity_import_verifier.py -q
scripts/verify_unity_fbx_import.sh --fbx <exported.fbx> --unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity --timeout-seconds 180
blender --background --factory-startup --python /private/tmp/mac_game_rigger_inspect_fbx.py -- /private/tmp/gltf-sample-assets/Models/CesiumMan/glTF-Binary/CesiumMan.glb
blender --background --factory-startup --python /private/tmp/mac_game_rigger_inspect_fbx.py -- /private/tmp/gltf-sample-assets/Models/Fox/glTF-Binary/Fox.glb
blender --background --factory-startup --python /private/tmp/mac_game_rigger_inspect_fbx.py -- /private/tmp/gltf-sample-assets/Models/BrainStem/glTF-Binary/BrainStem.glb
blender --background --factory-startup --python /private/tmp/mac_game_rigger_inspect_fbx.py -- /private/tmp/gltf-sample-assets/Models/CesiumMilkTruck/glTF-Binary/CesiumMilkTruck.glb
blender --background --factory-startup --python /private/tmp/mac_game_rigger_inspect_fbx.py -- /private/tmp/gltf-sample-assets/Models/DamagedHelmet/glTF-Binary/DamagedHelmet.glb
```

## Engine Import Verification

- Unity Editor exists at `/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity`.
- `scripts/verify_unity_fbx_import.sh` runs and is unit-tested with fake Unity binaries, including timeout/log-tail behavior.
- Sandboxed Unity batchmode fails before import because Unity Package Manager cannot open its local socket: `listen EPERM ... Unity-Upm-*.sock`.
- Sandbox-external Unity batchmode passed after restarting the stale Unity Licensing Client process.
- Passing verifier output: `{"status":"pass","assetPath":"Assets/MacGameRiggerImportCandidate/mac_game_rigger_unity_export.fbx"}`.
- `unity` is not available on `PATH`; pass `--unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity`.
- `UnrealEditor` is not available on `PATH`.
- `unreal` is not available on `PATH`.

The alpha smoke gate "at least 1 asset imported into Unity or Unreal and verified" is satisfied by the Unity batchmode import verifier. Production deformation quality is still unproven because full rig workflow timings use generated proxy scenes, while real sample assets are currently used as import/readiness baselines.
