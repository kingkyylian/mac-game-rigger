# H-003 Evidence Notes

Category: humanoid
Target filename: `H-003-humanoid-armored.fbx`
Rig target: Humanoid template
Source: Quaternius Ultimate Animated Character Pack - `Knight_Male.fbx`
Source URL: https://quaternius.com/packs/ultimatedanimatedcharacter.html
Source file: `local_assets/H-003/H-003-quaternius-knight-male.fbx`
License: CC0
SHA256: `fd323fbc4962a9b94ab58d303bbc92ead7228393b735a95d98a8509e33747e3f`

## Expected Risks

- rigid armor
- weight bleed

## Required Artifacts

- [x] `asset-import-smoke.json`
- [x] `qa-report.json`
- [x] `preview-neutral.png`
- [x] `preview-neutral-side.png`
- [x] `preview-pose.png`
- [x] `preview-pose-side.png`
- [x] `export-unity.fbx` or `export.fbx`
- [x] `unity-import.json` when Unity import is run
- [ ] `unreal-import.json` when Unreal import is run or blocked

## Review

Deformation score: 3
Unity import status: pass
Unreal import status: blocked
Manual cleanup required: yes
Failure type: deformation quality issue

H-003 is a real armored humanoid stress case. Blender import smoke passes with
one mesh, one source armature, 32 source bones, 1,484 vertices, and 17 actions.
The Mac Game Rigger workflow generated a fresh MGR armature, bound all vertices,
reported zero unweighted vertices, and exported `export-unity.fbx`.

Latest workflow rerun after distal coverage scaling: `poseDeformation.status`
is `pass`, `maxAxisExpansionRatio` is `1.0x`, and `humanoidDiagnostics.status`
is `pass`. Coverage ratios are core 0.8807, arm 0.0256, leg 0.0647, and foot
0.0256. Hands and feet now receive dominant fallback coverage instead of being
left at effectively zero coverage.

Manual visual review is still conservative. The armored silhouette is readable
and does not show the severe limb expansion seen on H-001, but the bulky shoulder
and shield/armor shape make arm and torso separation hard to judge from the
current flat silhouette previews. This is now valid score-3 evidence under the
numeric gate, but it is still not score-4 production-clean deformation.

Known cleanup/review items:

- verify the asset orientation before comparing front and side screenshots;
- inspect shoulders, wrists, hips, knees, and armor intersections in Blender;
- Unity import verification passed on Unity `6000.4.1f1`;
- keep H-003 as armored/bulky humanoid coverage, not as a final quality claim.

## Register Command

```bash
scripts/register_asset_evidence.py \
  --slot H-003 \
  --source-name "<source asset name>" \
  --source-url "<source url or ticket>" \
  --license "<license>" \
  --external-path "<source asset path>" \
  --qa-report evidence/H-003/qa-report.json \
  --preview-neutral evidence/H-003/preview-neutral.png \
  --export-unity-fbx evidence/H-003/export-unity.fbx \
  --notes evidence/H-003/notes.md \
  --deformation-score <1-5> \
  --unity-status <pass|fail|blocked|not tested> \
  --unreal-status <pass|fail|blocked|not tested> \
  --evidence-root . \
  --check-files
```
