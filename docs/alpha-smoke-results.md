# Alpha Smoke Results

Date: 2026-06-15

This smoke pass uses generated Blender proxy scenes for the selected benchmark slots. Real licensed production assets have not been added to the repository yet, so these rows validate the current Mac Game Rigger Alpha workflow rather than final art quality.

Engine import status is now verified for the generated Unity FBX export. Unity Editor was found at `/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity`; sandboxed batchmode still cannot run because Unity Package Manager cannot open its local socket, but sandbox-external batchmode imports `/var/folders/jg/ppc_rfwj63v8qprgfw63k3pr0000gn/T/mac_game_rigger_unity_export.fbx` successfully after restarting a stale Unity Licensing Client process.

## Summary

| Slot ID | Category | Proxy Asset | Template | Time To First Rig | Cleanup Minutes | Deformation Score | FBX Export | Engine Import | Accepted | Notes |
|---|---|---|---|---:|---:|---:|---|---|---|---|
| H-001 | humanoid | generated clean neutral biped proxy | Humanoid | 0.3 | 10 | 3 | pass | pass: Unity batchmode import verifier | accepted for alpha smoke | Full landmark -> armature -> capsule weights -> QA -> Unity FBX path passed in headless Blender and Unity import. |
| H-006 | humanoid | generated low-poly biped proxy | Humanoid | 0.3 | 15 | 3 | pass | not individually imported | needs review | Low-poly proxy validates deterministic bone generation and fallback weights; real low-poly silhouette still needs manual review. |
| H-010 | humanoid | generated thin-limb biped proxy | Humanoid | 0.4 | 20 | 3 | pass | not individually imported | needs review | Capsule weighting produced bounded influences; thin-limb production assets remain a cleanup risk. |
| Q-001 | quadruped | generated quadruped dog proxy | Quadruped | 0.4 | 30 | 2 | pass | not individually imported | needs review | Quadruped template loads and exports, but deformation quality needs real four-leg asset validation. |
| C-001 | tail/wing creature | generated creature proxy | Quadruped + Tail + Wing | 0.5 | 45 | 2 | pass | not individually imported | needs review | Current alpha has no dedicated wing helper yet; result is useful as a failure visibility baseline. |

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

The alpha smoke gate "at least 1 asset imported into Unity or Unreal and verified" is satisfied by the Unity batchmode import verifier. Production asset quality is still unproven because the smoke pass uses generated proxy scenes.
