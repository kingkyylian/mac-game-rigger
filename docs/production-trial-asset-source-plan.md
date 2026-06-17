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
| `H-001` | Quaternius Ultimate Animated Character Pack | Baseline normal humanoid. |
| `H-002` | Quaternius Ultimate Animated Character Pack | Stylized/short-limb candidate if available. |
| `H-003` | Quaternius Modular Character Outfits - Fantasy or RPG Character Pack | Armored humanoid stress case. |
| `H-006` | Quaternius Animated Man Pack or Animated Woman Pack | Low-poly humanoid candidate. |
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

## First Execution Step

Start with `H-001` only:

1. Download one normal-proportion humanoid from Quaternius.
2. Save it outside git or under a git-ignored local asset folder.
3. Open/import in Blender.
4. Run the Mac Game Rigger workflow.
5. Generate `evidence/H-001/qa-report.json`, preview PNG, and Unity FBX.
6. Register H-001 with `scripts/register_asset_evidence.py`.

Only after H-001 has real evidence should the remaining nine slots be filled in
batches.
