# H-009 Evidence Notes

Category: humanoid
Target filename: `H-009-quaternius-soldier-male.fbx`
Rig target: Humanoid template

## Source

- Source: Quaternius Ultimate Animated Character Pack - `Soldier_Male.fbx`
- Source URL: `https://quaternius.com/packs/ultimatedanimatedcharacter.html`
- Drive pack folder id: `1sNi1AfenfPRrvRt5yfaj5QMMd6KKcUJ5`
- Drive FBX folder id: `1zn_PeKyQwPhgAggaoJZJFpLB2DQrr86U`
- Drive file id: `1a-hba4k6uJVtUDYzHsaNvx4r7rVMNICs`
- License: CC0
- Local-only source binary: `local_assets/H-009/H-009-quaternius-soldier-male.fbx`
- SHA256: `ff250924f45de0eb447d353c7d6f665f6864bc7e828075853d8193c1e9dbadfc`

## Import Smoke

- Status: pass
- Meshes: 1
- Source armatures: 1
- Source bones: 32
- Vertices: 1515
- Faces: 1510
- Actions: 17
- Suggested category: humanoid

## Workflow Result

- Template: humanoid
- Generated bones: 21
- Weighted vertices: 1515
- Unweighted vertices: 0
- Over-limit vertices: 0
- Pruned weights: 0
- Normalized vertices: 0
- Pose operators: humanoid stress and side review
- Pose deformation status: pass
- Max axis expansion: 1.0367
- Export: `evidence/H-009/export-unity.fbx`

## Review

Deformation score: 3
Visual review status: pass
Unity import status: pass
Unreal import status: blocked
Manual cleanup required: yes
Failure type: deformation quality issue

The soldier silhouette remains readable and is useful as the wide-shoulder /
bulky humanoid stress case. Pose deformation metrics pass and no unweighted or
over-limit vertices are reported. Shoulder/upper-arm weighting still needs
manual cleanup before production use.

Latest workflow rerun after distal coverage scaling: `poseDeformation.status`
is `pass` with max axis expansion 1.0118x. `humanoidDiagnostics` reports
`pass`; coverage ratios are core 0.8244, arm 0.1043, leg 0.0462, and foot
0.0251. Hands and feet now have dominant fallback coverage. This keeps the
score-3 claim valid as usable-with-cleanup evidence, while shoulder/upper-arm
weighting still needs manual cleanup before production use.

Unity batchmode import passed on Unity `6000.4.1f1` using
`evidence/H-009/export-unity.fbx`.

## Commands

```bash
blender --background --factory-startup --python tools/blender_asset_import_smoke.py -- --slot H-009 --asset local_assets/H-009/H-009-quaternius-soldier-male.fbx --output evidence/H-009/asset-import-smoke.json --source-name 'Quaternius Ultimate Animated Character Pack - Soldier_Male.fbx' --source-url 'https://quaternius.com/packs/ultimatedanimatedcharacter.html' --license CC0
```

```bash
blender --background --factory-startup --python tools/blender_asset_workflow.py -- --asset local_assets/H-009/H-009-quaternius-soldier-male.fbx --evidence-dir evidence/H-009 --summary evidence/H-009/workflow-summary.json --camera-axis y --template humanoid
```
