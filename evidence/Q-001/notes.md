# Q-001 Evidence Notes

Category: quadruped
Target filename: `Q-001-quadruped-dog.glb`
Rig target: Quadruped template

## Expected Risks

- baseline four-leg deformation

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
  --slot Q-001 \
  --source-name "<source asset name>" \
  --source-url "<source url or ticket>" \
  --license "<license>" \
  --external-path "<source asset path>" \
  --qa-report evidence/Q-001/qa-report.json \
  --preview-neutral evidence/Q-001/preview-neutral.png \
  --export-unity-fbx evidence/Q-001/export-unity.fbx \
  --notes evidence/Q-001/notes.md \
  --deformation-score <1-5> \
  --unity-status <pass|fail|blocked|not tested> \
  --unreal-status <pass|fail|blocked|not tested> \
  --evidence-root . \
  --check-files
```
