# Q-002 Evidence Notes

Category: quadruped
Target filename: `Q-002-quaternius-fox.fbx`
Rig target: Quadruped template

## Source

- Source: Quaternius Ultimate Animated Animal Pack - `Fox.fbx`
- Source URL: `https://quaternius.com/packs/ultimateanimatedanimals.html`
- License: CC0
- Local source path: `local_assets/Q-002/Q-002-quaternius-fox.fbx`
- SHA256: `24da24dbd2800be0b268ade50429fb7d815423a92a9a39178a4fc460d7b832de`

## Evidence Summary

- Blender import smoke: pass
- Source import metrics: 1 mesh, 1 source armature, 67 source bones, 926 vertices, 12 actions
- Suggested category: quadruped
- MGR workflow: pass with `--template quadruped`
- Generated MGR bones: 23
- Weight QA: 0 unweighted vertices, 0 over-limit vertices
- Cleanup: 2 pruned weights, 2 normalized vertices
- Pose operator: `pose_quadruped_gait`
- Side pose operator: `pose_quadruped_side_review`
- Pose deformation: pass; max axis expansion ratio 1.3166
- Export: Unity-profile FBX generated

## Review

Deformation score: 3
Unity import status: pass
Unreal import status: blocked
Manual cleanup required: yes
Failure type: deformation quality issue

The asset proves a second real quadruped body shape can pass the current Mac
Game Rigger workflow. The primary x-axis preview gives a readable fox-like side
silhouette with a long tail, and the gait pose shows visible limb/body motion
without extreme bbox expansion. This satisfies the Q-002 small quadruped/tail
base evidence goal at score 3: usable with cleanup.

Unity batchmode import passed on Unity `6000.4.1f1` using
`evidence/Q-002/export-unity.fbx`.

It is not score 4 because the tail is still very upright in the source pose, and
direct shaded Blender inspection is still needed before production use.

## Artifacts

- `evidence/Q-002/asset-import-smoke.json`
- `evidence/Q-002/qa-report.json`
- `evidence/Q-002/workflow-summary.json`
- `evidence/Q-002/preview-neutral.png`
- `evidence/Q-002/preview-neutral-side.png`
- `evidence/Q-002/preview-pose.png`
- `evidence/Q-002/preview-pose-side.png`
- `evidence/Q-002/export-unity.fbx`
- `evidence/Q-002/export-unity.qa.json`
- `evidence/Q-002/unity-import.json`

## Commands

```bash
blender --background --factory-startup --python tools/blender_asset_import_smoke.py -- --slot Q-002 --asset local_assets/Q-002/Q-002-quaternius-fox.fbx --output evidence/Q-002/asset-import-smoke.json --source-name 'Quaternius Ultimate Animated Animal Pack - Fox.fbx' --source-url 'https://quaternius.com/packs/ultimateanimatedanimals.html' --license CC0
```

```bash
blender --background --factory-startup --python tools/blender_asset_workflow.py -- --asset local_assets/Q-002/Q-002-quaternius-fox.fbx --evidence-dir evidence/Q-002 --summary evidence/Q-002/workflow-summary.json --camera-axis x --template quadruped
```
