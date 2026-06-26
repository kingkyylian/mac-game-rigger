# P-002 Prop Hinge Evidence

## Source

- Slot: `P-002`
- Category: prop
- Target filename: `P-002-prop-treasure-chest-hinge.fbx`
- Rig target: `Prop hinge template`
- Source name: `Internal local asset pipeline - treasure_chest.fbx`
- Source reference: `file:///Users/kyylian/Developer/blender-egitim/mehmet-repo/asset-pipeline/assets/_done/F013_treasure_chest.json`
- License / usage label: `internal-local`
- Local source path: `local_assets/P-002/P-002-local-treasure-chest.fbx`
- Source SHA-256: `763eb6efa069aa5bed17d6273c21812d345336f4d112d15abb4984c664777259`

This is an internal local asset used to validate chunky prop and hinge-like workflow behavior. It should not be counted as a public-source CC0 asset.

## Import Smoke

- Status: pass
- Mesh count: 1
- Armatures before rigging: 0
- Materials: 3
- Vertices: 118
- Faces: 108
- Bounds: width `0.6`, depth `0.428`, height `0.4725`
- Suggested category: `prop`

This validates the broader prop classifier against a real chunky box-like prop, not only synthetic stats or a thin door slab.

## Workflow Result

- Workflow status: pass
- Template: `prop_hinge`
- Artist hinge controls: pivot `0.10`, base/origin `0.22`, layout axis `y`
- Generated bones: 3
- QA report: 118 vertices, 3 bones, 0 unweighted vertices, 0 over-limit vertices
- Prop weight diagnostics: `propBase` 64 dominant vertices, `propHinge` 2 dominant vertices, `propMovingPart` 52 dominant vertices
- Prop diagnostic thresholds: pass, coverage ratios `propBase` 0.5424, `propHinge` 0.0169, `propMovingPart` 0.4407, warnings none
- Pose preview operator: `pose_prop_hinge_open`
- Side review operator: `pose_prop_hinge_side_review`
- Pose deformation: pass
- Allowed expanded axis: `y`, because hinge opening intentionally expands the swing axis
- Unity export: `evidence/P-002/export-unity.fbx`
- Unity import: pass

## Visual Review

Score: 3

The preview produces a readable first-pass hinge-open treasure chest pose and validates the prop hinge workflow on a chunky prop shape. The result is usable as evidence for game-engine import and rough hinge behavior, not as final art-clean rig output.

Known cleanup work:

- Hinge layout axis is now artist-adjustable through a Blender enum/dropdown between X and Y; chest-like assets still need a polished rotation-plane/orientation UX beyond coarse axis selection.
- Hinge pose review now exposes artist-controlled open angle, rotation axis, and positive/negative swing direction in the Blender UI.
- Empty-based hinge visual guides can now be dragged and committed back to landmarks, but a polished custom pivot/orientation gizmo is still missing.
- `scripts/verify_prop_hinge_gizmo_workflow.py` now provides repeatable headless Blender smoke coverage for guide creation, guide move, commit back to landmarks, armature generation, and hinge-open pose.
- A prop_hinge-only Blender GizmoGroup now creates pivot and swing-tip X/Y/Z arrow handles bound to guide locations, but it still needs polished UX validation in an interactive viewport session.
- Prop QA now covers door and chunky chest-like evidence, but should be tuned against more shapes such as crate stacks, lamps, gates, and mechanical panels.
- This asset is internal-local evidence, not public CC0 coverage.
- Unreal import is still blocked until an Unreal verifier is added.
