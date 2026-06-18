# Production Trial Asset Source Plan

Date: 2026-06-17

This document locks the first public-source candidate pool for Mac Game Rigger
production-trial evidence. It does not claim that the real asset gate is passed.
The actual `samples/manifest.json` `realAsset` fields must stay empty until the
binary files are downloaded, inspected, and registered with real evidence paths.

## License Basis

Primary candidate source: Quaternius.

- Quaternius FAQ says the assets can be used for free without attribution in
  commercial, educational, and personal projects, and that all models are under
  CC0.
- Quaternius also states models can be modified and can be edited in Blender or
  imported as FBX files.

Fallback candidate source: Kenney.

- Kenney support says game assets on Kenney asset pages are public-domain/CC0
  and usable in commercial projects.

Source references:

- `https://quaternius.com/faq.html`
- `https://quaternius.com/`
- `https://kenney.nl/support`
- `https://kenney.nl/assets`

## Candidate Mapping

Machine-readable mapping lives in:

```text
samples/asset-source-candidates.json
```

The initial production-trial set is:

| Slot | Candidate source | Why |
|---|---|---|
| `H-001` | Quaternius Animated Man Pack - `Animated Human.fbx` | Baseline normal humanoid; downloaded locally and passed Blender import smoke. |
| `H-002` | Quaternius Ultimate Animated Character Pack | Stylized/short-limb candidate if available. |
| `H-003` | Quaternius Modular Character Outfits - Fantasy or RPG Character Pack | Armored humanoid stress case. |
| `H-006` | Quaternius Animated Woman Pack - `Animated Woman.fbx` | Low-poly humanoid; registered as complete low-quality evidence with deformation score 2. |
| `H-009` | Quaternius Ultimate Modular Men Pack or Ultimate Animated Character Pack | Wide-shoulder/bulky stress case. |
| `H-010` | Quaternius Ultimate Animated Character Pack | Thin-limb stress case if available. |
| `Q-001` | Quaternius Ultimate Animated Animal Pack or Farm Animal Pack | Baseline dog-like quadruped. |
| `Q-002` | Quaternius Cube World Kit or Ultimate Animated Animal Pack | Cat or small quadruped candidate. |
| `C-001` | Quaternius Animated Dinosaur Pack or Ultimate Monsters | Tail creature candidate. |
| `P-001` | Quaternius Steampunk Turret Pack or Fantasy Props MegaKit | Prop/hinge mechanical candidate. |

## Registration Rule

Do not put a candidate into `samples/manifest.json` as `realAsset` until all of
these are true:

- the exact asset binary has been downloaded or stored;
- the selected file path or storage reference is known;
- source URL and license basis are recorded;
- Blender import has been attempted;
- at least notes and initial QA/preview/export evidence are planned for that
  same slot.

This avoids inflating `realAssetCount` with assets we have not actually tested.

## Executed Slots

### H-001 Baseline Humanoid

1. Download one normal-proportion humanoid from Quaternius. Done for
   `Animated Human.fbx`.
2. Save it outside git or under a git-ignored local asset folder. Done under
   `local_assets/H-001/`.
3. Open/import in Blender. Done; see
   `evidence/H-001/asset-import-smoke.json`.
4. Run the Mac Game Rigger workflow.
5. Generate `evidence/H-001/qa-report.json`, preview PNG, and Unity FBX.
6. Register H-001 with `scripts/register_asset_evidence.py`.

H-001 is registered as real evidence, but not quality success. Preview
orientation is normalized and front-facing now. It still has deformation score
2 and engine import blockers.

### H-006 Low-Poly Humanoid

1. Download one low-poly humanoid from Quaternius. Done for
   `Animated Woman.fbx`.
2. Save it under ignored local asset storage. Done under
   `local_assets/H-006/`.
3. Open/import in Blender. Done; see
   `evidence/H-006/asset-import-smoke.json`.
4. Run the Mac Game Rigger workflow. Done; see
   `evidence/H-006/workflow-summary.json`.
5. Generate `evidence/H-006/qa-report.json`, preview PNGs, and Unity FBX.
6. Register H-006 with `scripts/register_asset_evidence.py`.

H-006 is registered as complete low-quality evidence. It proves the pipeline can
ingest and process a second real asset, and preview framing/orientation is now
readable after the dynamic camera clipping and normalization work. The workflow
now uses a stronger humanoid stress pose, but the result still confirms a
product gap: deformation quality is not game-ready. It must not be counted as
quality success until those issues are fixed.

## Next Execution Step

Do not simply add more humanoid evidence before fixing the evidence quality
loop. Preview rendering is no longer blank and current humanoids render
front/upright, and humanoid stress pose evidence now covers arms, legs, and
neck. The next productive step is to improve deformation quality, then continue
the remaining slots in batches:

1. Improve humanoid deformation enough to reach score 3+ on at least one
   already-registered source.
2. Add the next category-spread assets: Q-001, Q-002, C-001, and P-001.
3. Install/configure Unity if local engine import pass evidence is required.
