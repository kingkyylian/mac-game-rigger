# H-006 Evidence Notes

Category: humanoid
Target filename: `H-006-humanoid-lowpoly.glb`
Rig target: Humanoid template

## Expected Risks

- low-poly deformation

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
  --slot H-006 \
  --source-name "<source asset name>" \
  --source-url "<source url or ticket>" \
  --license "<license>" \
  --external-path "<source asset path>" \
  --qa-report evidence/H-006/qa-report.json \
  --preview-neutral evidence/H-006/preview-neutral.png \
  --export-unity-fbx evidence/H-006/export-unity.fbx \
  --notes evidence/H-006/notes.md \
  --deformation-score <1-5> \
  --unity-status <pass|fail|blocked|not tested> \
  --unreal-status <pass|fail|blocked|not tested> \
  --evidence-root . \
  --check-files
```
