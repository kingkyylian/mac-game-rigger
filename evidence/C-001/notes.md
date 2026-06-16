# C-001 Evidence Notes

Category: tail creature
Target filename: `C-001-tail-creature-dragon.glb`
Rig target: Quadruped + tail + wing helpers

## Expected Risks

- tail chain
- wing deformation

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
  --slot C-001 \
  --source-name "<source asset name>" \
  --source-url "<source url or ticket>" \
  --license "<license>" \
  --external-path "<source asset path>" \
  --qa-report evidence/C-001/qa-report.json \
  --preview-neutral evidence/C-001/preview-neutral.png \
  --export-unity-fbx evidence/C-001/export-unity.fbx \
  --notes evidence/C-001/notes.md \
  --deformation-score <1-5> \
  --unity-status <pass|fail|blocked|not tested> \
  --unreal-status <pass|fail|blocked|not tested> \
  --evidence-root . \
  --check-files
```
