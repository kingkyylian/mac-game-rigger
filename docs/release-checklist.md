# Alpha Release Checklist

Date: 2026-06-26
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
| Blender compatibility matrix | partial | `scripts/run_blender_compat_matrix.py` passed 15 Blender headless tests on local Blender 4.5.10 LTS outside the sandbox; Blender 4.2 target evidence is still required before beta. |
| Real asset evidence gate | pass | `scripts/validate_asset_evidence.py --manifest samples/manifest.json --evidence-root . --check-evidence-files --require-production-trial --quiet` passes with 12 complete real asset evidence entries. |
| CI smoke gate | blocked | `.github/workflows/ci.yml` runs `scripts/run_full_alpha_smoke.sh --skip-blender` and uploads `dist/MacGameRigger-0.1.0.zip`; remote GitHub run `28246102354` failed before starting because private-repo Actions billing/spending limit needs attention. |
| Performance smoke gate | pass | `scripts/run_full_alpha_smoke.sh --skip-blender` runs `scripts/run_performance_benchmark.py --vertex-count 1000 --max-seconds-per-case 10`; `docs/performance-benchmarks.md` records the 10k/50k/100k capsule weight-binding baseline. |
| Strict humanoid Animator gate | blocked | `docs/asset-evidence-progress.md` shows `configuredAnimatorSmokeForHumanoidScore3` blocked for H-003, H-004, H-005, H-009, and H-010. |

## Verification Commands

```bash
python3 -m pytest tests -q
scripts/validate_asset_evidence.py --manifest samples/manifest.json
scripts/validate_asset_evidence.py --manifest samples/manifest.json --evidence-root . --check-evidence-files --require-production-trial --quiet
scripts/run_performance_benchmark.py --vertex-count 10000 --vertex-count 50000 --vertex-count 100000 --output build/performance-benchmark.json
scripts/run_blender_compat_matrix.py --discover --skip-tests
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

## Production Trial Gate Command

This is expected to return zero for the current evidence set:

```bash
scripts/validate_asset_evidence.py --manifest samples/manifest.json --evidence-root . --require-production-trial
```

## Known issues

- Unity import validation passes outside the sandbox after restarting a stale Unity Licensing Client process. Sandboxed Unity batchmode still fails with Package Manager `listen EPERM`, so engine import verification must run outside the sandbox.
- GitHub Actions CI is configured, but the first remote run did not start because the private repository hit an account billing/spending-limit restriction. Keep using `scripts/run_full_alpha_smoke.sh --skip-blender` locally until billing is fixed or the repo visibility is intentionally changed.
- Strict configured Animator smoke is still incomplete for five score >= 3 Unity-pass humanoids: H-003, H-004, H-005, H-009, and H-010. H-006 has passing configured Animator evidence.
- Unreal engine import validation is not complete: prepare-only workspace creation and unattended runner orchestration are implemented, but `UnrealEditor` is not on `PATH` and no real Unreal Editor import pass has been captured.
- Blender 4.2 target compatibility is not yet proven locally; current discovered Blender is 4.5.10 LTS.
- Production trial evidence is present and passes, but the stricter game-ready configured Animator gate is not closed.
- Full Blender rig workflow timings still need a formal end-to-end benchmark across 10k / 50k / 100k vertex meshes; current performance benchmark covers deterministic capsule weight-binding math only.
- Wing-specific rig helpers are still experimental; prop hinge and tail creature helpers are present but need more real asset evidence.
- Finger rigging, cloth/skirt deformation, and advanced tail/wing controls remain out of V1 scope.
- QA report has structural, weight, preview, and pose deformation evidence, but still does not replace artist visual approval.
