# H-006 Evidence Notes

Category: humanoid
Target filename: `H-006-humanoid-lowpoly.glb`
Rig target: Humanoid template

## Expected Risks

- low-poly deformation

## Required Artifacts

- [x] `asset-import-smoke.json`
- [x] `workflow-summary.json`
- [x] `qa-report.json`
- [x] `preview-neutral.png`
- [x] `preview-pose.png` when relevant
- [x] `export-unity.fbx` or `export.fbx`
- [x] `unity-import.json` when Unity import is run
- [x] `unreal-import.json` when Unreal import is run or blocked

## Review

Source asset: Quaternius Animated Woman Pack - `Animated Woman.fbx`
Source URL: `https://quaternius.com/packs/animatedwoman.html`
License: CC0
Local path: `local_assets/H-006/H-006-quaternius-animated-woman.fbx`
SHA-256: `587512588e1b80af84d899cc93b3597428cd775da24c802a91f5ea348e935619`

Blender import smoke: pass in Blender 4.5.10.
Import metrics: 1 mesh, 1 armature, 48 bones, 1 material, 954 vertices, 1908 faces, 10 actions.
Suggested category: humanoid.

Mac Game Rigger workflow: pass in Blender 4.5.10.
Workflow summary: `evidence/H-006/workflow-summary.json`
Generated armature: 17 bones.
Source rig stripping: 1 armature, 1 armature modifier, and 34 vertex groups removed before MGR weighting.
Capsule weighting: 954 vertices weighted.
QA result: 0 unweighted vertices, 0 over-limit vertices, no warnings, no errors.
Unity FBX export: `evidence/H-006/export-unity.fbx`
Pose preview operator: `pose_humanoid_stress`; 10 pose bones changed before
rendering `preview-pose.png`.

Preview framing fix: refreshed after dynamic camera reframe and dynamic camera
clip-end handling. Neutral and pose previews are now visually readable.
Deformation score: 2
Unity import status: blocked; Unity Editor is not installed/discoverable locally.
Unreal import status: blocked; Unreal Editor is not installed/discoverable locally.
Manual cleanup required: yes, shoulder/elbow/leg deformation quality is still
too weak for game-ready use.
Failure type: deformation quality issue

Registration status: H-006 is complete as low-quality evidence for the
low-poly humanoid slot. It should not be counted as quality success until pose
stress and deformation output are improved.

## Register Command

```bash
scripts/register_asset_evidence.py \
  --slot H-006 \
  --source-name "Quaternius Animated Woman Pack - Animated Woman.fbx" \
  --source-url "https://quaternius.com/packs/animatedwoman.html" \
  --license "CC0" \
  --external-path "local_assets/H-006/H-006-quaternius-animated-woman.fbx" \
  --qa-report evidence/H-006/qa-report.json \
  --preview-neutral evidence/H-006/preview-neutral.png \
  --preview-pose evidence/H-006/preview-pose.png \
  --export-unity-fbx evidence/H-006/export-unity.fbx \
  --notes evidence/H-006/notes.md \
  --deformation-score 2 \
  --unity-status blocked \
  --unreal-status blocked \
  --failure-type "deformation quality issue" \
  --evidence-root . \
  --check-files
```
