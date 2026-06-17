# H-001 Evidence Notes

Category: humanoid
Target filename: `H-001-humanoid-clean-neutral.glb`
Rig target: Humanoid template

## Expected Risks

- baseline proportions

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

Source asset: Quaternius Animated Man Pack - `Animated Human.fbx`
Source URL: `https://quaternius.com/packs/animatedman.html`
License: CC0
Local path: `local_assets/H-001/H-001-quaternius-animated-human.fbx`
SHA-256: `edd4fde3a73afe2a22ddb5a10a215373a0880d9a4ee32a0815879a260b8e8445`

Blender import smoke: pass in Blender 4.5.10.
Import metrics: 1 mesh, 1 armature, 48 bones, 1 material, 791 vertices, 1578 faces, 9 actions.
Suggested category: humanoid.

Mac Game Rigger workflow: pass in Blender 4.5.10.
Workflow summary: `evidence/H-001/workflow-summary.json`
Generated armature: 17 bones.
Source rig stripping: 1 armature, 1 armature modifier, and 34 vertex groups removed before MGR weighting.
Capsule weighting: 791 vertices weighted.
QA result: 0 unweighted vertices, 0 over-limit vertices, no warnings, no errors.
Unity FBX export: `evidence/H-001/export-unity.fbx`
Pose preview operator: `pose_arm_raise`; 4 pose bones changed before rendering `preview-pose.png`.

Deformation score: 2
Unity import status: blocked; Unity Editor is not installed/discoverable locally.
Unreal import status: blocked; Unreal Editor is not installed/discoverable locally.
Manual cleanup required: yes, landmark/camera alignment and arm deformation need tuning before quality claim.
Failure type: deformation quality issue

Registration status: H-001 may be registered as complete evidence, but it should
be treated as a weak-quality baseline, not a production-quality success. The
source binary remains local-only under `local_assets/`.

## Register Command

```bash
scripts/register_asset_evidence.py \
  --slot H-001 \
  --source-name "Quaternius Animated Man Pack - Animated Human.fbx" \
  --source-url "https://quaternius.com/packs/animatedman.html" \
  --license "CC0" \
  --external-path "local_assets/H-001/H-001-quaternius-animated-human.fbx" \
  --qa-report evidence/H-001/qa-report.json \
  --preview-neutral evidence/H-001/preview-neutral.png \
  --preview-pose evidence/H-001/preview-pose.png \
  --export-unity-fbx evidence/H-001/export-unity.fbx \
  --notes evidence/H-001/notes.md \
  --deformation-score 2 \
  --unity-status blocked \
  --unreal-status blocked \
  --failure-type "deformation quality issue" \
  --evidence-root . \
  --check-files
```
