# Q-001 Evidence Notes

Category: quadruped
Target filename: `Q-001-quaternius-husky.fbx`
Rig target: Quadruped template

## Source

- Source: Quaternius Ultimate Animated Animal Pack - `Husky.fbx`
- Source URL: `https://quaternius.com/packs/ultimateanimatedanimals.html`
- License: CC0
- Local source path: `local_assets/Q-001/Q-001-quaternius-husky.fbx`
- SHA256: `2fd68780ebd69e138303fd38a430f6b8a87f6aafd29770339c95ce15f52d7321`

## Evidence Summary

- Blender import smoke: pass
- Source import metrics: 1 mesh, 1 source armature, 65 source bones, 962 vertices, 12 actions
- MGR workflow: pass with `--template quadruped`
- Generated MGR bones: 23
- Weight QA: 0 unweighted vertices, 0 over-limit vertices
- Export: Unity-profile FBX generated
- Pose operator: `pose_quadruped_gait`
- Side pose operator: `pose_quadruped_side_review`
- Pose deformation: pass; max axis expansion ratio 1.2729

## Review

Deformation score: 3
Unity import status: pass
Unreal import status: blocked
Manual cleanup required: yes
Failure type: deformation quality issue

The asset proves that a real dog-like quadruped can be imported, stripped from
its source rig, bound to the current quadruped template, posed with a simple
gait review operator, rendered, QA-checked, and exported. It does not prove
production-quality quadruped rigging yet. Unity batchmode import passed on
Unity `6000.4.1f1` using `evidence/Q-001/export-unity.fbx`.

The primary preview is now rendered from the x axis, which gives a readable
dog-like side silhouette. The gait preview shows visible leg motion and the pose
deformation metric passes without extreme bbox expansion. This supports score 3:
usable with cleanup and additional inspection. It is not score 4 because the
end-on secondary view is still narrow and direct shaded Blender inspection is
still needed before production use.

## Artifacts

- `evidence/Q-001/asset-import-smoke.json`
- `evidence/Q-001/qa-report.json`
- `evidence/Q-001/workflow-summary.json`
- `evidence/Q-001/preview-neutral.png`
- `evidence/Q-001/preview-neutral-side.png`
- `evidence/Q-001/preview-pose.png`
- `evidence/Q-001/preview-pose-side.png`
- `evidence/Q-001/export-unity.fbx`
- `evidence/Q-001/export-unity.qa.json`
- `evidence/Q-001/unity-import.json`

## Commands

```bash
blender --background --factory-startup --python tools/blender_asset_import_smoke.py -- --slot Q-001 --asset local_assets/Q-001/Q-001-quaternius-husky.fbx --output evidence/Q-001/asset-import-smoke.json --source-name 'Quaternius Ultimate Animated Animal Pack - Husky.fbx' --source-url 'https://quaternius.com/packs/ultimateanimatedanimals.html' --license CC0
```

```bash
blender --background --factory-startup --python tools/blender_asset_workflow.py -- --asset local_assets/Q-001/Q-001-quaternius-husky.fbx --evidence-dir evidence/Q-001 --summary evidence/Q-001/workflow-summary.json --camera-axis y --template quadruped
```
