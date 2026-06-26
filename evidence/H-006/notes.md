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
Weighting policy: limb and distal bone capsules use narrower radius scales than torso capsules to reduce limb/body bleed.
Coverage fallback: capsule binding now enforces minimum per-bone vertex coverage on the nearest real mesh vertices while preserving max-influence normalization.
Landmark policy: generated arm landmarks stay near the chest/shoulder band so T-pose game assets do not receive a downward arm chain from bbox-only landmarks.
Axis policy: depth-dominant humanoid assets use depth as the arm lateral axis while hip/leg landmarks keep X-axis separation.
Side hip policy: upper-leg bones now start from generated `hip.L` and `hip.R` landmarks instead of the shared center `hips` landmark.
Cleanup metric: 0 empty deform groups removed after capsule weighting; `workflow-summary.json` records an empty `removedEmptyGroupNames` list.
Core capsule policy: core body capsules are wider and weighted with higher binding priority; bind-space normalization now keeps torso vertices core-dominant instead of neck-dominant.
Weight diagnostics: `core` is dominant on 720 vertices, `arm` on 48, `leg` on 115, and `foot` on 71 after the latest workflow rerun.
Pose deformation metric: pass; front stress-pose max bbox expansion is now 1.6538x. The side-review pose uses a leg-focused silhouette check and now reports side 54->51px with lean 0.01 in the progress report.
Humanoid diagnostic: `humanoidDiagnostics` reports `pass`; coverage ratios are core 0.7547, arm 0.0503, leg 0.1205, and foot 0.0744. H-006 is currently the strongest score-3 humanoid under the new diagnostic.
Visual review status: pass for score 3 support; front stress and side-review previews are readable after bind-space weighting and side-review pose separation. This is usable with manual cleanup review, not production-ready.
QA result: 0 unweighted vertices, 0 over-limit vertices, no warnings, no errors.
Unity FBX export: `evidence/H-006/export-unity.fbx`
Pose preview operator: `pose_humanoid_stress`; 10 pose bones changed before
rendering `preview-pose.png` and `preview-pose-side.png`.

Preview framing fix: refreshed after dynamic camera reframe and dynamic camera
clip-end handling. Neutral and pose previews are now visually readable.
Deformation score: 3
Unity import status: pass on Unity `6000.4.1f1` using `evidence/H-006/export-unity.fbx`.
Unreal import status: blocked; Unreal Editor is not installed/discoverable locally.
Manual cleanup required: yes, shoulder/elbow/leg deformation quality and engine
avatar/generic rig settings still need review before game-ready use.
Failure type: deformation quality issue

Registration status: H-006 is complete as score-3 evidence for the low-poly
humanoid slot. It counts as usable-with-cleanup evidence, but not as a
production-ready rig until engine import and broader asset coverage pass.

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
  --preview-neutral-side evidence/H-006/preview-neutral-side.png \
  --preview-pose-side evidence/H-006/preview-pose-side.png \
  --export-unity-fbx evidence/H-006/export-unity.fbx \
  --notes evidence/H-006/notes.md \
  --deformation-score 3 \
  --visual-review-status pass \
  --visual-review-notes "Front stress preview shows readable arm and knee deformation after bind-space weighting; side-review preview is clean with low silhouette drift. Usable with manual cleanup review before production." \
  --unity-status pass \
  --unreal-status blocked \
  --failure-type "deformation quality issue" \
  --evidence-root . \
  --check-files
```
