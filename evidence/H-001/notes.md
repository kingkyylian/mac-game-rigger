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
Weighting policy: limb and distal bone capsules use narrower radius scales than torso capsules to reduce limb/body bleed.
Coverage fallback: capsule binding now enforces minimum per-bone vertex coverage on the nearest real mesh vertices while preserving max-influence normalization.
Landmark policy: generated arm landmarks stay near the chest/shoulder band so T-pose game assets do not receive a downward arm chain from bbox-only landmarks.
Axis policy: depth-dominant humanoid assets use depth as the arm lateral axis while hip/leg landmarks keep X-axis separation.
Foot forward policy: depth-dominant T-pose assets no longer use full arm-span depth for foot/toe forward offsets; foot capsules now stay near the pelvis forward line instead of stretching deep into the arm-span axis.
Side hip policy: upper-leg bones now start from generated `hip.L` and `hip.R` landmarks instead of the shared center `hips` landmark.
Cleanup metric: 0 empty deform groups removed after capsule weighting; `workflow-summary.json` records an empty `removedEmptyGroupNames` list.
Core capsule policy: core body capsules are wider and weighted with higher binding priority; minimum coverage fallback now keeps all generated deform groups active on this asset.
Fallback policy: nearest fallback now selects the bone with the lowest distance/radius ratio instead of the lowest absolute distance. This prevents tiny distal capsules from winning far-out vertices only because they are physically slightly closer.
Pose deformation metric: pass; stress-pose bbox max expansion is now 1.207x with no warning axes. This is a meaningful numeric improvement over the previous 2.591x X-axis expansion, but the stress preview still needs manual deformation review before a quality score increase.
Bone weight diagnostic: `workflow-summary.json` includes per-bone bounds and top weighted vertex samples under `boneWeightDiagnostics`. After the fallback-ratio change, `Foot.L` dominates 3 vertices with 1.0 average weight, while `LowerLeg.L` influences 33 vertices and dominates 29.
Capsule-bind diagnostic: `workflow-summary.json` includes `capsuleBindWeightDiagnostics`, which maps weighted vertices into the same capsule-bind space used by the actual binding algorithm. The latest H-001 data shows the previous left-foot over-capture redistributed away from `Foot.L`, while cleanup remains clean with 0 unweighted vertices and 0 over-limit vertices.
Capsule assignment diagnostic: `workflow-summary.json` includes `capsuleAssignmentDiagnostics`, which separates direct capsule assignments from nearest-bone fallback assignments. H-001 still has 440 capsule-assigned vertices and 351 nearest-fallback vertices, but fallback is now concentrated in core and limb bones: `Chest` 114, `Spine` 92, `LowerLeg.R` 30, `LowerArm.L` 28, `LowerArm.R` 28, `LowerLeg.L` 25, and `Foot.L` no longer appears in the top fallback list.
Humanoid diagnostic: `workflow-summary.json` now includes `humanoidDiagnostics`. H-001 reports `warn` with `weakHumanoidFootCoverage`; current dominant coverage ratios are core 0.7775, arm 0.0936, leg 0.11, and foot 0.019. This keeps the weak lower-leg/foot result visible even though the bbox-based pose deformation metric now passes.
Visual review status: fail; the front and side pose previews are readable, but the leg/foot deformation shows visible quality artifacts and does not justify a score 3 production-quality claim.
QA result: 0 unweighted vertices, 0 over-limit vertices, no warnings, no errors.
Unity FBX export: `evidence/H-001/export-unity.fbx`
Pose preview operator: `pose_humanoid_stress`; 10 pose bones changed before
rendering `preview-pose.png` and `preview-pose-side.png`.

Orientation normalization: applied Y-up to Z-up mesh rotation before source rig
stripping. Neutral and pose previews are now upright/front-facing.
Deformation score: 2
Unity import status: blocked; Unity Editor is not installed/discoverable locally.
Unreal import status: blocked; Unreal Editor is not installed/discoverable locally.
Manual cleanup required: yes, shoulder/elbow deformation artifacts and engine
import still need review before quality claim.
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
  --preview-neutral-side evidence/H-001/preview-neutral-side.png \
  --preview-pose-side evidence/H-001/preview-pose-side.png \
  --export-unity-fbx evidence/H-001/export-unity.fbx \
  --notes evidence/H-001/notes.md \
  --deformation-score 2 \
  --visual-review-status fail \
  --unity-status blocked \
  --unreal-status blocked \
  --failure-type "deformation quality issue" \
  --evidence-root . \
  --check-files
```
