# Mac Game Rigger Alpha

Mac Game Rigger Alpha is a Mac-first Blender 4.2 add-on for game teams that need faster first-pass rigging, cleanup, QA, and engine-ready export without CUDA, UniRig, or a remote GPU.

The product is **Blender add-on first**. Blender remains the artist-facing environment for mesh inspection, landmark placement, armature generation, weight binding, pose checks, and FBX/GLB export.

This is **not a full AI auto-rigger**. The goal is a practical human-in-the-loop rigging workbench: template rigs, guided landmarks, automatic weight baselines, cleanup diagnostics, pose tests, QA reports, and Unity/Unreal export profiles.

## Alpha Scope

V1 targets:

- Blender 4.2 add-on installable on macOS.
- Humanoid and quadruped rig templates.
- Landmark creation, mirroring, and validation.
- Armature generation from template + landmarks.
- Automatic Blender weight binding.
- Capsule-distance fallback weight math.
- Weight cleanup diagnostics.
- Pose tests for common deformation failures.
- Unity and Unreal FBX export profiles.
- QA report JSON and preview PNG generation.

V1 does not target:

- UniRig porting.
- CUDA or remote GPU inference.
- General arbitrary-character AI rigging.
- Training pipelines.
- Full standalone DCC replacement.

## Repository Status

This repository is at project foundation stage. The current source of truth for product scope is:

```text
docs/product-scope.md
```

## Planned Layout

```text
addon/mac_game_rigger/
  __init__.py
  bl_info.py
  ui/
  core/
  templates/
  presets/
scripts/
tests/
blender_tests/
docs/
samples/
```

## Development Assumptions

- macOS Apple Silicon.
- Blender 4.2 installed locally.
- Python 3.11 for pure-Python tests.
- Blender Python for add-on and integration behavior.

