# Alpha Release Checklist

Date: 2026-06-15
Release: Mac Game Rigger Alpha 0.1.0

## P0 Checklist

| Area | Status | Evidence |
|---|---|---|
| Install | pass | `scripts/install_addon_dev.sh` creates the Blender 4.2 dev symlink. |
| Add-on enable | pass | `blender --background --factory-startup --python-expr "import mac_game_rigger; mac_game_rigger.register(); mac_game_rigger.unregister()"` passed in earlier foundation verification. |
| Landmark workflow | pass | `blender_tests/test_landmark_operators.py`, `test_landmark_validation_operator.py`, and `test_landmark_mirror_operator.py`. |
| Armature generation | pass | `blender_tests/test_generate_armature_operator.py` and `test_armature_generation.py`. |
| Weight bind | pass | `blender_tests/test_automatic_weights_operator.py`, `test_capsule_weights_operator.py`, and `test_weight_cleanup_operator.py`. |
| Pose tests | pass | `blender_tests/test_pose_tests_operator.py`. |
| QA report | pass | `tests/test_qa_report.py` and `blender_tests/test_qa_report_operator.py`. |
| Preview PNG | pass | `blender_tests/test_preview_operator.py`. |
| Export | pass | `blender_tests/test_unity_fbx_export_operator.py` and `test_unreal_fbx_export_operator.py` create FBX files and QA JSON. |
| Package | pass | `scripts/package_addon.sh` creates `dist/MacGameRigger-0.1.0.zip`. |
| Smoke benchmark | pass | `docs/alpha-smoke-results.md` has 5 generated full-workflow proxy rows, 5 real glTF sample asset import rows, and one Unity batchmode import verifier pass for `mac_game_rigger_unity_export.fbx`. |

## Verification Commands

```bash
python3 -m pytest tests -q
blender --background --factory-startup --python blender_tests/test_generate_armature_operator.py
blender --background --factory-startup --python blender_tests/test_capsule_weights_operator.py
blender --background --factory-startup --python blender_tests/test_weight_cleanup_operator.py
blender --background --factory-startup --python blender_tests/test_pose_tests_operator.py
blender --background --factory-startup --python blender_tests/test_qa_report_operator.py
blender --background --factory-startup --python blender_tests/test_preview_operator.py
blender --background --factory-startup --python blender_tests/test_unity_fbx_export_operator.py
blender --background --factory-startup --python blender_tests/test_unreal_fbx_export_operator.py
scripts/package_addon.sh
python3 -m pytest tests/test_unity_import_verifier.py -q
scripts/verify_unity_fbx_import.sh --fbx <exported.fbx> --unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity --timeout-seconds 180
```

## Known issues

- Unity import validation passes outside the sandbox after restarting a stale Unity Licensing Client process. Sandboxed Unity batchmode still fails with Package Manager `listen EPERM`, so engine import verification must run outside the sandbox.
- Unreal engine import validation is not available: `UnrealEditor` is not on `PATH`.
- Full rig workflow timings currently use generated proxy scenes; five real Khronos glTF sample assets are covered as Blender import/readiness baselines, not production deformation QA.
- Wing and prop-specific rig helpers are not implemented in alpha 0.1.0.
- Finger rigging, cloth/skirt deformation, and advanced tail/wing controls remain out of V1 scope.
- QA report is structural and count-based; it does not yet compute visual deformation quality automatically.
