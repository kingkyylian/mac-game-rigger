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
| Blender compatibility matrix | partial | `scripts/run_blender_compat_matrix.py --blender /opt/homebrew/bin/blender --output build/blender-compat-4.5-full.json --quiet` passed 15 Blender headless tests on local Blender 4.5.10 LTS outside the sandbox. `scripts/run_blender_compat_matrix.py --discover --skip-tests --require-version-prefix "Blender 4.2" --output build/blender-compat-target-4.2.json --quiet` is blocked with `required_blender_version_not_found`; discovered versions are only Blender 4.5.10 LTS. |
| Real asset evidence gate | pass | `scripts/validate_asset_evidence.py --manifest samples/manifest.json --evidence-root . --check-evidence-files --require-production-trial --quiet` passes with 12 complete real asset evidence entries. `docs/asset-evidence-progress.md` keeps stricter game-ready gates separate so the production-trial pass does not hide product gaps. |
| CI smoke gate | blocked | `.github/workflows/ci.yml` runs `scripts/run_full_alpha_smoke.sh --skip-blender` and uploads `dist/MacGameRigger-0.1.0.zip`; remote GitHub run `28247801894` failed before starting because private-repo Actions billing/spending limit needs attention. |
| Performance smoke gate | pass | `scripts/run_full_alpha_smoke.sh --skip-blender` runs `scripts/run_performance_benchmark.py --vertex-count 1000 --max-seconds-per-case 10`; `docs/performance-benchmarks.md` records the 10k/50k/100k capsule weight-binding baseline. |
| Blender workflow benchmark | pass | `scripts/run_blender_workflow_benchmark.py --blender blender --asset local_assets/H-006/H-006-quaternius-animated-woman.fbx --template humanoid --evidence-root build/blender-workflow-benchmark --output build/blender-workflow-benchmark.json --timeout-seconds 300 --max-seconds-per-case 120` passed outside the sandbox in 3.142040s with QA pass, pose deformation pass, preview renders, and Unity FBX export. |
| Real asset family workflow benchmark | pass | `scripts/run_blender_workflow_benchmark.py --blender blender --manifest samples/manifest.json --slot H-003 --slot H-004 --slot H-005 --slot H-009 --slot H-010 --slot Q-001 --slot Q-002 --slot C-001 --slot P-001 --slot P-002 --evidence-root build/blender-workflow-real-asset-family-benchmark --output build/blender-workflow-real-asset-family-benchmark.json --timeout-seconds 300 --max-seconds-per-case 120` passed outside the sandbox; 10/10 real manifest slots passed structural QA, pose deformation, and Unity FBX export. |
| Synthetic workflow scaling | pass | `scripts/run_blender_workflow_benchmark.py --blender blender --synthetic-humanoid-vertices 10000 --synthetic-humanoid-vertices 50000 --synthetic-humanoid-vertices 100000 --evidence-root build/blender-workflow-synthetic-benchmark --output build/blender-workflow-synthetic-benchmark.json --timeout-seconds 600 --max-seconds-per-case 180` passed outside the sandbox; 10k in 3.195480s, 50k in 5.995934s, 100k in 10.817145s, with clean structural QA, pose deformation pass, and Unity FBX export. |
| Template-family workflow scaling | pass | `scripts/run_blender_workflow_benchmark.py --blender blender --synthetic-multimesh-humanoid-vertices 10000 --synthetic-quadruped-vertices 10000 --synthetic-tail-creature-vertices 10000 --synthetic-prop-hinge-vertices 10000 --evidence-root build/blender-workflow-template-family-benchmark --output build/blender-workflow-template-family-benchmark.json --timeout-seconds 600 --max-seconds-per-case 180` passed outside the sandbox; structural QA, pose deformation, and Unity FBX export pass for all four cases. |
| Strict humanoid Animator gate | blocked | `docs/asset-evidence-progress.md` shows `configuredAnimatorSmokeForHumanoidScore3` blocked for H-003, H-004, H-005, H-009, and H-010. `scripts/plan_unity_animator_smoke_migration.py --json` lists exactly those five migration commands. `scripts/check_unity_batchmode_health.py --output build/unity-batchmode-health.json --timeout-seconds 90` currently times out with Unity Licensing Client/bootstrap failure before asset import starts. |
| Strict separate-mesh humanoid gate | blocked | `docs/asset-evidence-progress.md` shows `realSeparateMeshHumanoidEvidence` blocked for H-003, H-004, H-005, H-006, H-009, and H-010. Current complete score >= 3 real humanoids report source import mesh count 1 and rig workflow mesh count 1, so no real separate-mesh hair/accessory/clothing humanoid evidence exists yet. |
| Split-mesh humanoid intake plan | pass | `scripts/plan_split_mesh_humanoid_intake.py --manifest samples/manifest.json --json` reports H-002, H-007, and H-008 as open humanoid slots and recommends H-002. When an asset path is provided, it emits source import smoke, Blender workflow, manifest registration, and report regeneration commands. |
| Split-mesh humanoid verifier | blocked | `scripts/verify_split_mesh_humanoid_evidence.py --manifest samples/manifest.json --evidence-root . --json` is wired and currently blocks because no score >= 3 real humanoid has both source import mesh count > 1 and rig workflow mesh count > 1. |

## Verification Commands

```bash
python3 -m pytest tests -q
scripts/validate_asset_evidence.py --manifest samples/manifest.json
scripts/validate_asset_evidence.py --manifest samples/manifest.json --evidence-root . --check-evidence-files --require-production-trial --quiet
scripts/generate_asset_evidence_report.py --manifest samples/manifest.json --evidence-root . --check-evidence-files --output docs/asset-evidence-progress.md
scripts/run_performance_benchmark.py --vertex-count 10000 --vertex-count 50000 --vertex-count 100000 --output build/performance-benchmark.json
scripts/run_blender_workflow_benchmark.py --blender blender --asset local_assets/H-006/H-006-quaternius-animated-woman.fbx --template humanoid --evidence-root build/blender-workflow-benchmark --output build/blender-workflow-benchmark.json --timeout-seconds 300 --max-seconds-per-case 120
scripts/run_blender_workflow_benchmark.py --blender blender --manifest samples/manifest.json --slot H-003 --slot H-004 --slot H-005 --slot H-009 --slot H-010 --slot Q-001 --slot Q-002 --slot C-001 --slot P-001 --slot P-002 --evidence-root build/blender-workflow-real-asset-family-benchmark --output build/blender-workflow-real-asset-family-benchmark.json --timeout-seconds 300 --max-seconds-per-case 120
scripts/run_blender_workflow_benchmark.py --blender blender --synthetic-humanoid-vertices 10000 --synthetic-humanoid-vertices 50000 --synthetic-humanoid-vertices 100000 --evidence-root build/blender-workflow-synthetic-benchmark --output build/blender-workflow-synthetic-benchmark.json --timeout-seconds 600 --max-seconds-per-case 180
scripts/run_blender_workflow_benchmark.py --blender blender --synthetic-multimesh-humanoid-vertices 10000 --synthetic-quadruped-vertices 10000 --synthetic-tail-creature-vertices 10000 --synthetic-prop-hinge-vertices 10000 --evidence-root build/blender-workflow-template-family-benchmark --output build/blender-workflow-template-family-benchmark.json --timeout-seconds 600 --max-seconds-per-case 180
scripts/plan_unity_animator_smoke_migration.py --manifest samples/manifest.json --evidence-root . --json
scripts/run_unity_animator_smoke_migration.py --manifest samples/manifest.json --evidence-root . --dry-run
scripts/check_unity_batchmode_health.py --output build/unity-batchmode-health.json --timeout-seconds 90
scripts/plan_split_mesh_humanoid_intake.py --manifest samples/manifest.json --json
scripts/verify_split_mesh_humanoid_evidence.py --manifest samples/manifest.json --evidence-root . --json
scripts/run_blender_compat_matrix.py --discover --skip-tests
scripts/run_blender_compat_matrix.py --discover --skip-tests --require-version-prefix "Blender 4.2" --output build/blender-compat-target-4.2.json --quiet
scripts/run_blender_compat_matrix.py --blender /opt/homebrew/bin/blender --output build/blender-compat-4.5-full.json --quiet
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

- Unity import validation has previous outside-sandbox passes, but the current configured Animator migration preflight times out before import because Unity Licensing Client/bootstrap fails. Latest health report path: `build/unity-batchmode-health.json`; the emitted hint says to open Unity Hub or the Unity Editor once to refresh licensing, then rerun outside the sandbox. Sandboxed Unity batchmode still fails with Package Manager `listen EPERM`, so engine import verification must run outside the sandbox.
- Blender full workflow benchmark passes outside the sandbox, but Blender 4.5.10 crashed inside the Codex sandbox with exit code 139 before producing a workflow summary.
- GitHub Actions CI is configured, but the first remote run did not start because the private repository hit an account billing/spending-limit restriction. Keep using `scripts/run_full_alpha_smoke.sh --skip-blender` locally until billing is fixed or the repo visibility is intentionally changed.
- Strict configured Animator smoke is still incomplete for five score >= 3 Unity-pass humanoids: H-003, H-004, H-005, H-009, and H-010. H-006 has passing configured Animator evidence.
- Strict separate-mesh humanoid evidence is missing: all complete score >= 3 real humanoids currently report source import mesh count 1 and rig workflow mesh count 1, so hair/accessory/clothing split-mesh behavior is still unproven on real assets.
- Split-mesh humanoid intake is now planned by script, but it still needs an actual licensed asset file before the strict gate can close.
- Unreal engine import validation is not complete: prepare-only workspace creation and unattended runner orchestration are implemented, but `UnrealEditor` is not on `PATH` and no real Unreal Editor import pass has been captured.
- Blender 4.2 target compatibility is not yet proven locally; the target gate now reports `required_blender_version_not_found` and current discovered Blender versions are only 4.5.10 LTS.
- Production trial evidence is present and passes, but the stricter game-ready configured Animator and real separate-mesh humanoid gates are not closed.
- Full Blender rig workflow timing now has one real H-006 baseline, a 10-slot real asset family benchmark, synthetic 10k / 50k / 100k scalability baselines, and synthetic template-family timing; real separate-mesh hair/accessory humanoids and Blender 4.2 timing still need evidence.
- Wing-specific rig helpers are still experimental; prop hinge and tail creature helpers are present but need more real asset evidence.
- Finger rigging, cloth/skirt deformation, and advanced tail/wing controls remain out of V1 scope.
- QA report has structural, weight, preview, and pose deformation evidence, but still does not replace artist visual approval.
