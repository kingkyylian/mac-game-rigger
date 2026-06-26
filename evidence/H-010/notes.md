# H-010 Evidence Notes

Category: humanoid
Target filename: `H-010-humanoid-thin-limbs.glb`
Rig target: Humanoid template
Source: Quaternius Ultimate Animated Character Pack - `Elf.fbx`
Source URL: https://quaternius.com/packs/ultimatedanimatedcharacter.html
Source file: `local_assets/H-010/H-010-quaternius-elf.fbx`
License: CC0
SHA256: `02948bf6ff8d441a348cc1cb3a7fb42bc3625cc9135c23770a484e732ce4646a`

## Expected Risks

- thin limbs
- capsule weighting stability

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

H-010 is a real thin-limb humanoid stress case. Blender import smoke passes with
one mesh, one source armature, 32 source bones, 1,314 vertices, and 17 actions.
The Mac Game Rigger workflow generated a fresh MGR armature, bound all vertices,
reported zero unweighted vertices, and exported `export-unity.fbx`.

Automatic pose deformation is solid: `poseDeformation.status` is `pass` and
`maxAxisExpansionRatio` is `1.0x`. QA reports zero over-limit vertices, with
only 2 pruned and normalized vertices during cleanup.

Latest workflow rerun after distal coverage scaling: `humanoidDiagnostics`
reports `pass`; coverage ratios are core 0.7489, arm 0.0259, leg 0.1971, and
foot 0.0259. Hands and feet now have dominant fallback coverage instead of zero
effective coverage. This makes H-010 valid score-3 thin-limb stress evidence,
but it still needs lower-leg/foot review before any stronger score claim.

Manual visual review is score 3. The silhouette stays coherent in stress and
side-review poses, but thin legs/feet still need targeted cleanup before the
asset should be treated as game-production ready. This result is useful
thin-limb coverage and supports the production-trial ratio, but it is not score
4 because lower-leg and foot behavior still needs direct Blender inspection.

Unity batchmode import passed on Unity `6000.4.1f1` using
`evidence/H-010/export-unity.fbx`.

Known cleanup/review items:

- inspect knees, ankles, and feet in Blender with shaded geometry, not only flat
  silhouettes;
- verify wrists and elbows after applying gameplay animation clips;
- review Unity scale/orientation and avatar/generic rig settings beyond import;
- keep this as thin-limb evidence, not as a final production-quality claim.

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
