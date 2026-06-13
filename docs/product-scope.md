# Mac Game Rigger Alpha Product Scope

## Execution Goal

Build **Mac Game Rigger Alpha**: a Mac-first Blender 4.2 add-on that helps a game team rig, test, clean up, and export character assets faster without CUDA, UniRig, or a remote GPU.

The product direction is **Blender add-on first**. Blender already gives us the mesh, armature, skinning, weight paint, FBX/GLB export, and artist review environment. The alpha should extend that workflow instead of trying to replace Blender or build a full DCC app.

## Product Promise

Mac Game Rigger Alpha is an assisted rigging workbench for game production. It should reduce repetitive rigging setup work, standardize export behavior, surface deformation problems earlier, and make artist cleanup more measurable.

This is **not a full AI auto-rigger**. It should not promise perfect one-click rigging for arbitrary meshes, generated creatures, bad topology, cloth-heavy characters, or hero assets that need expert weight painting.

## Target User

- Small game teams working mainly on Macs.
- Technical artists who use Blender as the rigging/review environment.
- Developers who need predictable Unity, Unreal, or Godot import outputs.
- Artists who want faster first-pass rigs and clearer cleanup guidance.

## V1 Scope

V1 should ship as a Blender add-on with deterministic, human-in-the-loop rigging tools.

### V1 Must Have

- Blender 4.2 add-on installable on macOS.
- `Mac Game Rigger` sidebar panel.
- Humanoid template rig.
- Quadruped template rig.
- Landmark creation and deletion.
- Landmark mirror support for `.L` / `.R` pairs.
- Landmark validation for required template points.
- Armature generation from template + landmarks.
- Automatic Blender weight binding.
- Capsule-distance fallback weight math.
- Weight cleanup tools:
  - normalize weights
  - prune tiny weights
  - remove empty vertex groups
  - detect unweighted vertices
  - detect vertices above max influence count
- Pose tests:
  - reset pose
  - arm raise
  - knee bend
  - neck turn
- Unity FBX export profile.
- Unreal FBX export profile.
- QA report JSON.
- Preview PNG generation.
- Alpha package zip.

### V1 Should Have

- Tail helper template.
- Basic wing helper template.
- Save/load landmark sets.
- Simple scorecard for sample assets.
- Manual smoke test instructions for Blender.

### V1 Can Defer

- Finger rigging.
- Face rigging.
- IK/FK control rig generation.
- Cloth/skirt helper bones.
- Advanced creature auto-detection.
- ML-based landmark suggestions.
- Standalone macOS app wrapper.
- Marketplace packaging.
- Plugin updater.

## Explicit Non-Goals

- No UniRig full port.
- No CUDA dependency.
- No remote GPU dependency.
- No training pipeline.
- No full automatic arbitrary-character rigging.
- No claim that the system replaces expert weight painting.
- No cloud backend.
- No generated-mesh repair system.
- No animation authoring suite.

## Supported Asset Classes

### V1 Primary

- Clean humanoid game characters.
- Stylized humanoids with normal limb layout.
- Simple quadrupeds.
- Simple props with hinge-like articulation.

### V1 Experimental

- Characters with tails.
- Winged creatures.
- Low-poly generated characters.

### V1 Not Reliable

- Dense bad-topology generated meshes.
- Long coats, skirts, robes, or heavy cloth.
- Characters with many extra limbs.
- Complex facial rigs.
- Production hero characters requiring polished deformation.

## Core Workflow

```text
1. User opens a mesh in Blender.
2. User opens View3D > Sidebar > Mac Game Rigger.
3. User analyzes selected mesh.
4. User selects a template.
5. User creates or adjusts landmarks.
6. User validates required landmarks.
7. User generates armature.
8. User binds weights.
9. User runs cleanup tools.
10. User applies pose tests.
11. User generates QA report and preview.
12. User exports FBX with Unity or Unreal profile.
```

## Alpha Definition of Done

Alpha is complete only when all of these are true:

- The add-on can be installed into Blender 4.2 on macOS.
- The `Mac Game Rigger` panel appears in the 3D View sidebar.
- The user can create and clear landmarks.
- The user can validate humanoid template landmarks.
- The user can generate a humanoid armature from a full landmark set.
- The user can bind at least one selected mesh to the generated armature.
- The user can run at least one weight cleanup diagnostic.
- The user can apply and reset at least one pose test.
- The user can export an FBX using the Unity profile.
- The user can export an FBX using the Unreal profile.
- The tool can save a QA report JSON.
- The tool can save a preview PNG.
- At least 5 sample assets have smoke test notes.
- At least 1 exported asset has been imported into Unity or Unreal for validation.
- Known issues are documented.
- The add-on can be packaged as `MacGameRigger-0.1.0.zip`.

## Quality Bar

V1 should be judged by production usefulness, not by research-model novelty.

Minimum acceptable quality:

- Clean humanoid first-pass rig can be generated in minutes.
- Tool reports missing landmarks instead of failing silently.
- Tool reports unweighted vertices and excessive influence counts.
- Export profiles avoid common game-engine FBX mistakes such as unwanted leaf bones.
- Artist can understand what needs manual cleanup.

Benchmark target:

```text
Humanoid: 8 of 10 clean humanoid assets usable with cleanup <= 20 minutes.
Quadruped: 3 of 5 simple quadruped assets usable with cleanup <= 35 minutes.
Tail/wing experiments: useful first-pass result or clear failure report.
```

## Technical Direction

Use deterministic code first:

- JSON rig templates.
- Blender empties as landmarks.
- Blender edit bones for armature generation.
- Blender automatic weights as baseline.
- Capsule-distance weights as fallback.
- Pure Python tests for template, landmark, category, export profile, and QA report logic.
- Blender headless tests for armature generation, binding, preview, and export.

ML can be considered later only for landmark suggestions. It should not be required for V1.

## Serious Execution Rules

- P0 scope must be completed before P1 polish.
- Every core function needs a unit test where Blender is not required.
- Every Blender-dependent feature needs either a headless Blender smoke script or a documented manual smoke test.
- A rigging task is not complete until the result can be visually inspected or exported.
- Alpha is not complete until at least one output is validated in a game engine.

## First Build Slice

The first build slice is intentionally narrow:

```text
Installable Blender add-on -> sidebar panel -> mesh analysis operator -> humanoid template loader -> landmark creation -> armature generation.
```

This slice proves whether the Blender add-on path is solid before we invest in weight cleanup, pose testing, and export polish.
