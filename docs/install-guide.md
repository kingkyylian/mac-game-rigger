# Install Guide

This guide covers local macOS installation paths for Mac Game Rigger Alpha.

## Requirements

- macOS on Apple Silicon.
- Blender 4.2 target version, or a newer Blender version for compatibility testing.
- Python 3.11 for local pure-Python tests.
- Repository checkout:

```bash
cd /Users/kyylian/mac-game-rigger
```

## Development Symlink Install

Use the development installer when actively editing the add-on:

```bash
scripts/install_addon_dev.sh
```

Expected result:

- Blender add-ons folder contains a symlink to `addon/mac_game_rigger`.
- Source edits are picked up without rebuilding the zip package.

Then open Blender and enable:

```text
Edit > Preferences > Add-ons > Mac Game Rigger
```

## Zip Package Install

Build the distributable package:

```bash
scripts/package_addon.sh
```

Expected output:

```text
dist/MacGameRigger-0.1.0.zip
```

Install in Blender:

```text
Edit > Preferences > Add-ons > Install... > dist/MacGameRigger-0.1.0.zip
```

After enabling the add-on, the panel should appear in the 3D View sidebar.

## Quick Functional Smoke

After install, run this manual smoke inside Blender:

1. Open or create a simple mesh scene.
2. Run asset analysis.
3. Create template landmarks.
4. Validate landmarks.
5. Generate armature.
6. Bind weights.
7. Run pose test.
8. Generate QA report.
9. Generate preview PNG.
10. Export Unity or Unreal FBX.

For automated local verification, use:

```bash
python3 -m pytest tests -q
```

For Blender-dependent verification, run the scripts under `blender_tests/` with Blender batch mode.

## macOS Notes

- If macOS blocks a downloaded zip, remove quarantine before installing:

```bash
xattr -dr com.apple.quarantine dist/MacGameRigger-0.1.0.zip
```

- If Blender does not show the add-on after a symlink install, restart Blender and re-check the add-ons folder for the expected symlink.
- If multiple Blender versions are installed, confirm which version owns the add-ons folder used by `scripts/install_addon_dev.sh`.

## Current Compatibility Status

The product target is Blender 4.2 on macOS. Recent local validation has also run on a newer Blender LTS build. Before beta, the same test matrix must be run on Blender 4.2 and documented in `docs/release-checklist.md`.
