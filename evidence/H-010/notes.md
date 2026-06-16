# H-010 Evidence Notes

Category: humanoid
Target filename: `H-010-humanoid-thin-limbs.glb`
Rig target: Humanoid template

## Expected Risks

- thin limbs
- capsule weighting stability

## Required Artifacts

- [ ] `qa-report.json`
- [ ] `preview-neutral.png`
- [ ] `preview-pose.png` when relevant
- [ ] `export-unity.fbx` or `export.fbx`
- [ ] `unity-import.json` when Unity import is run
- [ ] `unreal-import.json` when Unreal import is run or blocked

## Review

Deformation score:
Unity import status:
Unreal import status:
Manual cleanup required:
Failure type:

## Register Command

```bash
scripts/register_asset_evidence.py \
  --slot H-010 \
  --source-name "<source asset name>" \
  --source-url "<source url or ticket>" \
  --license "<license>" \
  --external-path "<source asset path>" \
  --qa-report evidence/H-010/qa-report.json \
  --preview-neutral evidence/H-010/preview-neutral.png \
  --export-unity-fbx evidence/H-010/export-unity.fbx \
  --notes evidence/H-010/notes.md \
  --deformation-score <1-5> \
  --unity-status <pass|fail|blocked|not tested> \
  --unreal-status <pass|fail|blocked|not tested> \
  --evidence-root . \
  --check-files
```
