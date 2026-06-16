# Asset Evaluation Protocol

This protocol defines how real assets are evaluated for Mac Game Rigger production trial readiness.

## Goal

Replace proxy-only confidence with repeatable evidence from real game assets.

Each evaluated asset must produce:

- asset manifest entry;
- QA JSON;
- preview PNG;
- exported FBX;
- Unity or Unreal import result when applicable;
- deformation score;
- notes on manual cleanup required.

## Asset Identity

Every asset must use a stable slot ID from `samples/README.md` and `samples/manifest.json`.

Filename format:

```text
<slot-id>-<short-description>.<ext>
```

Examples:

```text
H-001-humanoid-clean-neutral.glb
Q-001-quadruped-dog.glb
C-001-tail-creature-dragon.glb
```

Do not change the slot ID when swapping the underlying source asset.

## Required Metadata

For every real asset, record:

- slot ID;
- category;
- source name;
- source URL or internal storage reference;
- license;
- whether the binary can be committed to the repo;
- local filename or external path;
- vertex/mesh/material estimate;
- whether it already has an armature;
- expected deformation risks;
- evidence paths.

Use `samples/manifest.json` as the source of truth.

Example `realAsset` entry:

```json
{
  "sourceName": "Internal Hero Character",
  "sourceUrl": "https://example.invalid/source-or-ticket",
  "license": "internal-test",
  "canCommitBinary": false,
  "externalPath": "/external/assets/H-001-humanoid-clean-neutral.glb"
}
```

Example `evidence` entry:

```json
{
  "qaReport": "evidence/H-001/qa-report.json",
  "previewNeutral": "evidence/H-001/preview-neutral.png",
  "exportUnityFbx": "evidence/H-001/export-unity.fbx",
  "notes": "evidence/H-001/notes.md",
  "deformationScore": 4,
  "unityImport": { "status": "pass" },
  "unrealImport": { "status": "blocked" }
}
```

For large evidence that is stored outside the repository, use object form with a storage reference:

```json
{
  "exportUnityFbx": {
    "storageReference": "s3://studio-rig-evidence/H-001/export-unity.fbx"
  }
}
```

Validate the manifest and current evidence state:

```bash
scripts/validate_asset_evidence.py --manifest samples/manifest.json
scripts/validate_asset_evidence.py --manifest samples/manifest.json --check-evidence-files --evidence-root .
```

Enforce the production trial gate:

```bash
scripts/validate_asset_evidence.py --manifest samples/manifest.json --evidence-root . --require-production-trial
```

`--require-production-trial` also checks local evidence file existence. Relative paths are resolved from `--evidence-root`.

Register one completed slot without hand-editing JSON:

```bash
scripts/create_evidence_skeleton.py --evidence-root .

scripts/register_asset_evidence.py \
  --manifest samples/manifest.json \
  --slot H-001 \
  --source-name "Internal Hero Character" \
  --source-url "https://example.invalid/source-or-ticket" \
  --license internal-test \
  --external-path /external/assets/H-001-humanoid-clean-neutral.glb \
  --qa-report evidence/H-001/qa-report.json \
  --preview-neutral evidence/H-001/preview-neutral.png \
  --export-unity-fbx evidence/H-001/export-unity.fbx \
  --notes evidence/H-001/notes.md \
  --deformation-score 4 \
  --unity-status pass \
  --unreal-status blocked \
  --evidence-root . \
  --check-files
```

`create_evidence_skeleton.py` creates only evidence folders and `notes.md` checklists. It does not create fake QA reports, previews, FBX files, or engine import results.

The register script refuses to overwrite an existing slot unless `--force` is passed.

## Standard Workflow

For every asset:

1. Import/open the asset in Blender.
2. Run asset analysis.
3. Choose the closest template.
4. Place or load landmarks.
5. Validate landmarks.
6. Generate armature.
7. Bind weights.
8. Run weight cleanup.
9. Run pose tests.
10. Generate QA JSON.
11. Generate preview PNG.
12. Export FBX with Unity or Unreal profile.
13. Run engine import verifier when available.
14. Assign deformation score.

## Evidence Layout

Use this layout for local or committed evidence:

```text
evidence/
  <slot-id>/
    qa-report.json
    preview-neutral.png
    preview-pose.png
    export-unity.fbx
    export-unreal.fbx
    unity-import.json
    unreal-import.json
    notes.md
```

Large binaries may stay outside git, but their path or storage reference must be recorded in `samples/manifest.json`.

## Deformation Score

Use the rubric in `docs/deformation-scoring-rubric.md`.

Production trial acceptance:

- score 4-5: usable;
- score 3: usable with cleanup;
- score 1-2: not acceptable without manual rig work.

The production trial target is at least 70% of real assets scoring 3 or higher.

## Minimum Production Trial Set

The first real validation pack should include at least:

- 3 humanoids;
- 2 quadrupeds;
- 1 low-poly humanoid;
- 1 thin-limb humanoid;
- 1 wide-shoulder or bulky humanoid;
- 1 tail creature;
- 1 accessory or prop-heavy character.

The validator enforces this as:

- at least 10 complete real assets;
- at least 3 humanoids;
- at least 2 quadrupeds;
- `H-006` low-poly humanoid complete;
- `H-010` thin-limb humanoid complete;
- `H-003` or `H-009` wide/bulky stress case complete;
- at least 1 tail creature;
- at least 1 prop or accessory-heavy slot;
- at least 70% of complete assets scoring 3 or higher;
- at least 3 Unity import passes;
- at least 1 Unreal pass or explicit Unreal blocker.

Complete evidence means the slot has real asset metadata, deformation score, QA report, preview, exported FBX, notes, and local files or explicit storage references for those artifacts.

## Failure Classification

Classify every failed asset with one primary failure type:

- import failure;
- template mismatch;
- landmark ambiguity;
- armature generation issue;
- weight bind issue;
- deformation quality issue;
- export failure;
- engine import failure;
- performance issue;
- out of scope asset type.

## Review Rule

Engine import success is not deformation success. An asset is production-trial usable only when the Blender QA, preview review, deformation score, and engine import notes all support the result.
