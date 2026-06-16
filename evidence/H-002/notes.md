# H-002 Evidence Notes

Category: humanoid
Target filename: `H-002-humanoid-stylized-chibi.glb`
Rig target: Humanoid template

## Expected Risks

- large head
- short limbs
- template scaling

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
  --slot H-002 \
  --source-name "<source asset name>" \
  --source-url "<source url or ticket>" \
  --license "<license>" \
  --external-path "<source asset path>" \
  --qa-report evidence/H-002/qa-report.json \
  --preview-neutral evidence/H-002/preview-neutral.png \
  --export-unity-fbx evidence/H-002/export-unity.fbx \
  --notes evidence/H-002/notes.md \
  --deformation-score <1-5> \
  --unity-status <pass|fail|blocked|not tested> \
  --unreal-status <pass|fail|blocked|not tested> \
  --evidence-root . \
  --check-files
```
