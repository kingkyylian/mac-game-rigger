# P-001 Prop Hinge Evidence

## Source

- Slot: `P-001`
- Category: prop
- Target filename: `P-001-local-wooden-door.fbx`
- Rig target: `Prop hinge template`
- Source name: `Internal local asset pipeline - wooden_door.fbx`
- Source reference: `file:///Users/kyylian/Developer/blender-egitim/asset-pipeline/assets/_done/E001_wooden_door.json`
- License / usage label: `internal-local`
- Local source path: `local_assets/P-001/P-001-local-wooden-door.fbx`
- Source SHA-256: `c1e682005643b78fb176c7c363596c572b657749848d266e6a9186deefd8a3c4`

This is an internal local asset used to validate prop-rig behavior. It should not be counted as a public-source CC0 asset.

## Import Smoke

- Status: pass
- Mesh count: 1
- Armatures before rigging: 0
- Materials: 1
- Vertices: 360
- Faces: 378
- Bounds: width `0.7025`, depth `0.0668`, height `1.1375`

The generic asset smoke classifier now suggests `prop` for this thin door-like mesh. The production workflow was still run explicitly with `--template prop_hinge` so the evidence remains tied to the intended hinge rig.

## Workflow Result

- Workflow status: pass
- Template: `prop_hinge`
- Artist hinge controls: pivot X `0.08`, base/origin X `0.18`
- Generated bones: 3
- QA report: 360 vertices, 3 bones, 0 unweighted vertices, 0 over-limit vertices
- Prop weight diagnostics: `propBase` 138 dominant vertices, `propHinge` 12 dominant vertices, `propMovingPart` 210 dominant vertices
- Prop diagnostic thresholds: pass, coverage ratios `propBase` 0.3833, `propHinge` 0.0333, `propMovingPart` 0.5833, warnings none
- Pose preview operator: `pose_prop_hinge_open`
- Side review operator: `pose_prop_hinge_side_review`
- Pose deformation: pass
- Allowed expanded axis: `y`, because hinge opening intentionally expands the swing axis
- Unity export: `evidence/P-001/export-unity.fbx`
- Unity import: pass

## Visual Review

Score: 3

The preview produces a readable hinge-open door pose and validates that the prop hinge template can generate a simple game-engine importable rig on macOS. This is usable as first-pass prop evidence, not a final production-clean rig.

Known cleanup work:

- Pivot/origin placement now has CLI-level controls, Blender UI sliders, selected-mesh landmark generation, and draggable Empty-based visual hinge guides that can be committed back to landmarks. It still needs a polished custom pivot/orientation gizmo.
- Hinge pose review now exposes artist-controlled open angle, rotation axis, and positive/negative swing direction in the Blender UI.
- `scripts/verify_prop_hinge_gizmo_workflow.py` now provides repeatable headless Blender smoke coverage for guide creation, guide move, commit back to landmarks, armature generation, and hinge-open pose.
- A prop_hinge-only Blender GizmoGroup now creates pivot and swing-tip X/Y/Z arrow handles bound to guide locations, but it still needs polished UX validation in an interactive viewport session.
- Weight diagnostics now label prop regions and enforce basic threshold warnings; thresholds still need tuning against more prop shapes.
- The generic import smoke classifier now handles this thin prop case and has synthetic chunky/low-long mechanical prop coverage, but it still needs confirmation against more real prop assets.
- Unreal import is still blocked until an Unreal verifier is added.
