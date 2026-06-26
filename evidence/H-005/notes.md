# H-005 Evidence Notes

Category: humanoid
Target filename: `H-005-quaternius-pirate-male.fbx`
Rig target: Humanoid template

## Source

- Source: Quaternius Ultimate Animated Character Pack - `Pirate_Male.fbx`
- Source URL: `https://quaternius.com/packs/ultimatedanimatedcharacter.html`
- Drive pack folder id: `1sNi1AfenfPRrvRt5yfaj5QMMd6KKcUJ5`
- Drive FBX folder id: `1zn_PeKyQwPhgAggaoJZJFpLB2DQrr86U`
- Drive file id: `1VkfDPMCRuAgJ9LLP9yTllWHDCQ9wwKpn`
- License: CC0
- Local-only source binary: `local_assets/H-005/H-005-quaternius-pirate-male.fbx`
- SHA256: `4a46790aeaa86a919245007932b4cfa7ce744590e538ad0cffe6895fdc48f98c`

## Import Smoke

- Status: pass
- Meshes: 1
- Source armatures: 1
- Source bones: 32
- Vertices: 1383
- Faces: 1384
- Actions: 17
- Suggested category: humanoid

## Workflow Result

- Template: humanoid
- Generated bones: 21
- Weighted vertices: 1383
- Unweighted vertices: 0
- Over-limit vertices: 0
- Pruned weights: 0
- Normalized vertices: 0
- Pose operators: humanoid stress and side review
- Pose deformation status: pass
- Max axis expansion: 1.0018
- Export: `evidence/H-005/export-unity.fbx`

## Review

Deformation score: 3
Visual review status: pass
Unity import status: pass
Unreal import status: blocked
Manual cleanup required: yes
Failure type: deformation quality issue

The pirate silhouette remains readable in stress and side-review previews, with
hat/head shape and arm pose staying coherent. The result is useful for fast
game-prototype rigging, but arm/shoulder weighting and accessory intersections
still need cleanup before production use.

Latest workflow rerun after distal coverage scaling: `humanoidDiagnostics`
reports `pass`; coverage ratios are core 0.8496, arm 0.026, leg 0.0976, and
foot 0.026. Hands and feet now have dominant fallback coverage instead of zero
effective coverage. This keeps the score-3 result valid as usable-with-cleanup
evidence, not production-clean deformation.

Unity batchmode import passed on Unity `6000.4.1f1` using
`evidence/H-005/export-unity.fbx`.

## Commands

```bash
blender --background --factory-startup --python tools/blender_asset_import_smoke.py -- --slot H-005 --asset local_assets/H-005/H-005-quaternius-pirate-male.fbx --output evidence/H-005/asset-import-smoke.json --source-name 'Quaternius Ultimate Animated Character Pack - Pirate_Male.fbx' --source-url 'https://quaternius.com/packs/ultimatedanimatedcharacter.html' --license CC0
```

```bash
blender --background --factory-startup --python tools/blender_asset_workflow.py -- --asset local_assets/H-005/H-005-quaternius-pirate-male.fbx --evidence-dir evidence/H-005 --summary evidence/H-005/workflow-summary.json --camera-axis y --template humanoid
```
