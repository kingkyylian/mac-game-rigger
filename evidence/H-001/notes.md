# H-001 Evidence Notes

Category: humanoid
Target filename: `H-001-humanoid-clean-neutral.glb`
Rig target: Humanoid template

## Expected Risks

- baseline proportions

## Required Artifacts

- [x] `asset-import-smoke.json`
- [ ] `qa-report.json`
- [ ] `preview-neutral.png`
- [ ] `preview-pose.png` when relevant
- [ ] `export-unity.fbx` or `export.fbx`
- [ ] `unity-import.json` when Unity import is run
- [ ] `unreal-import.json` when Unreal import is run or blocked

## Review

Source asset: Quaternius Animated Man Pack - `Animated Human.fbx`
Source URL: `https://quaternius.com/packs/animatedman.html`
License: CC0
Local path: `local_assets/H-001/H-001-quaternius-animated-human.fbx`
SHA-256: `edd4fde3a73afe2a22ddb5a10a215373a0880d9a4ee32a0815879a260b8e8445`

Blender import smoke: pass in Blender 4.5.10.
Import metrics: 1 mesh, 1 armature, 48 bones, 1 material, 791 vertices, 1578 faces, 9 actions.
Suggested category: humanoid.

Deformation score: not tested
Unity import status: not tested
Unreal import status: not tested
Manual cleanup required: not assessed
Failure type: not assessed

Do not register this slot in `samples/manifest.json` yet. The source binary is
downloaded and importable, but required QA, preview, and exported FBX evidence is
still missing.

## Register Command

```bash
scripts/register_asset_evidence.py \
  --slot H-001 \
  --source-name "<source asset name>" \
  --source-url "<source url or ticket>" \
  --license "<license>" \
  --external-path "<source asset path>" \
  --qa-report evidence/H-001/qa-report.json \
  --preview-neutral evidence/H-001/preview-neutral.png \
  --export-unity-fbx evidence/H-001/export-unity.fbx \
  --notes evidence/H-001/notes.md \
  --deformation-score <1-5> \
  --unity-status <pass|fail|blocked|not tested> \
  --unreal-status <pass|fail|blocked|not tested> \
  --evidence-root . \
  --check-files
```
