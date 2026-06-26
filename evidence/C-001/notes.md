# C-001 Evidence Notes

Category: tail creature
Target filename: `C-001-quaternius-apatosaurus.fbx`
Rig target: Tail creature template

## Source

- Source: Quaternius Animated Dinosaur Pack - `Apatosaurus.fbx`
- Source URL: `https://quaternius.com/packs/animateddinosaurs.html`
- Drive folder: `https://drive.google.com/drive/folders/1u5Fhu3ziuRlGonW6bUI7uClqBGoSNeF6?usp=sharing`
- Drive FBX folder id: `1xcRhyZq5TPVpjPveaAlX3JnpWo3n-SP1`
- Drive file id: `1v3ZGBrJjA_zGQN6s-9NyZ1eYqbPOYDC2`
- License: CC0
- Local-only source binary: `local_assets/C-001/C-001-quaternius-apatosaurus.fbx`
- SHA256: `e09a1c62f282cf5470d297c6a67f5acb51b09edd1a26af35d2f7fa30fedda2b4`

## Import Smoke

- Status: pass
- Meshes: 1
- Source armatures: 1
- Source bones: 39
- Vertices: 723
- Faces: 714
- Actions: 6
- Suggested category: quadruped

## Workflow Result

- Template: tail_creature
- Source rig stripped: yes
- Generated bones: 25
- Weighted vertices: 723
- Unweighted vertices: 0
- Over-limit vertices: 0
- Pruned weights: 0
- Normalized vertices: 0
- Pose operators: `pose_tail_creature_reach`, `pose_tail_creature_side_review`
- Pose deformation status: pass
- Max axis expansion: 1.3026
- Export: `evidence/C-001/export-unity.fbx`

## Review

Deformation score: 3
Visual review status: pass
Unity import status: pass
Unreal import status: blocked
Manual cleanup required: yes
Failure type: deformation quality issue

The Apatosaurus is useful as real tail-creature coverage because it has an
extreme long-tail/long-neck silhouette and stresses anatomy that a generic
quadruped template does not model well. The dedicated tail-creature template now
adds a longer neck chain and a three-bone tail chain, runs a quieter reach pose,
and keeps the silhouette readable enough for usable-with-cleanup evidence.

The result is improved but not production-clean. Pose deformation max expansion
dropped from the quadruped baseline `2.1013x` to `1.3026x`, tail-dominant
coverage increased to 252 vertices, and Unity batchmode import passes. Direct
shaded review is still needed for leg placement, upper-neck bending, and final
tail weighting before this becomes artist-quality game rig output.

## Commands

```bash
blender --background --factory-startup --python tools/blender_asset_import_smoke.py -- --slot C-001 --asset local_assets/C-001/C-001-quaternius-apatosaurus.fbx --output evidence/C-001/asset-import-smoke.json --source-name 'Quaternius Animated Dinosaur Pack - Apatosaurus.fbx' --source-url 'https://quaternius.com/packs/animateddinosaurs.html' --license CC0
```

```bash
blender --background --factory-startup --python tools/blender_asset_workflow.py -- --asset local_assets/C-001/C-001-quaternius-apatosaurus.fbx --evidence-dir evidence/C-001 --summary evidence/C-001/workflow-summary.json --camera-axis x --template tail_creature
```

```bash
scripts/verify_unity_fbx_import.sh --fbx evidence/C-001/export-unity.fbx --unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity --timeout-seconds 240
```
