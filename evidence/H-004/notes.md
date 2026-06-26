# H-004 Evidence Notes

Category: humanoid
Target filename: `H-004-quaternius-wizard.fbx`
Rig target: Humanoid template

## Source

- Source: Quaternius Ultimate Animated Character Pack - `Wizard.fbx`
- Source URL: `https://quaternius.com/packs/ultimatedanimatedcharacter.html`
- Drive pack folder id: `1sNi1AfenfPRrvRt5yfaj5QMMd6KKcUJ5`
- Drive FBX folder id: `1zn_PeKyQwPhgAggaoJZJFpLB2DQrr86U`
- Drive file id: `1A2-WYmJ3lqpP3zVs-wWYz3ShpB-Vutm-`
- License: CC0
- Local-only source binary: `local_assets/H-004/H-004-quaternius-wizard.fbx`
- SHA256: `a0515645954945a9029bf2db4b4fa120f24e9516402987bdc29c7b570fb9f957`

## Import Smoke

- Status: pass
- Meshes: 1
- Source armatures: 1
- Source bones: 32
- Vertices: 3366
- Faces: 3319
- Actions: 17
- Suggested category: humanoid

## Workflow Result

- Template: humanoid
- Generated bones: 21
- Weighted vertices: 3366
- Unweighted vertices: 0
- Over-limit vertices: 0
- Pruned weights: 4
- Normalized vertices: 4
- Pose operators: humanoid stress and side review
- Pose deformation status: pass
- Max axis expansion: 1.0
- Export: `evidence/H-004/export-unity.fbx`

## Review

Deformation score: 3
Visual review status: pass
Unity import status: pass
Unreal import status: blocked
Manual cleanup required: yes
Failure type: deformation quality issue

The wizard silhouette remains readable in neutral, stress, and side-review
previews. The tall hat and robe volume are preserved well enough for
usable-with-cleanup evidence, but robe/leg intersections and direct shaded
Blender review remain open before production use.

Latest workflow rerun after distal coverage scaling: `humanoidDiagnostics`
reports `pass`; coverage ratios are core 0.8865, arm 0.0255, leg 0.0615, and
foot 0.0255. Hands and feet now have dominant fallback coverage instead of zero
effective coverage. Because this is still a robe/hidden-foot asset, shaded
Blender review remains important before any production-clean claim.

Unity batchmode import passed on Unity `6000.4.1f1` using
`evidence/H-004/export-unity.fbx`.

## Commands

```bash
blender --background --factory-startup --python tools/blender_asset_import_smoke.py -- --slot H-004 --asset local_assets/H-004/H-004-quaternius-wizard.fbx --output evidence/H-004/asset-import-smoke.json --source-name 'Quaternius Ultimate Animated Character Pack - Wizard.fbx' --source-url 'https://quaternius.com/packs/ultimatedanimatedcharacter.html' --license CC0
```

```bash
blender --background --factory-startup --python tools/blender_asset_workflow.py -- --asset local_assets/H-004/H-004-quaternius-wizard.fbx --evidence-dir evidence/H-004 --summary evidence/H-004/workflow-summary.json --camera-axis y --template humanoid
```
