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

Candidate source planning lives in `samples/asset-source-candidates.json` and
`docs/production-trial-asset-source-plan.md`. A candidate source is not a real
asset record. Only populate `samples/manifest.json` `realAsset` after the exact
binary has been downloaded or stored and the local path or storage reference is
known.

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
  "previewNeutralSide": "evidence/H-001/preview-neutral-side.png",
  "previewPose": "evidence/H-001/preview-pose.png",
  "previewPoseSide": "evidence/H-001/preview-pose-side.png",
  "exportUnityFbx": "evidence/H-001/export-unity.fbx",
  "notes": "evidence/H-001/notes.md",
  "deformationScore": 4,
  "visualReview": {
    "status": "pass",
    "notes": "Front and side pose previews show acceptable shoulder, elbow, knee, and wrist deformation."
  },
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

When `--check-evidence-files` is enabled, the validator also reports preview
silhouette diagnostics for readable PNG previews. The current metrics are image
size, foreground pixel ratio, foreground bounding box, and bounding-box fill
ratio, plus vertical center-shift ratio between the top and bottom silhouette
bands. The progress report summarizes this as side-view width expansion
(`side neutral->pose px ratio`) and `lean` when side previews are present, or
neutral-view foreground/fill percentages otherwise. These numbers are not a
replacement for manual deformation review yet; they are a tracking signal for
pose artifacts, body lean, cropping, blank previews, and side-view expansion
regressions.

For humanoid workflow evidence, `preview-pose.png` uses the full front-facing
stress pose, while `preview-pose-side.png` may use the side-review pose. The
side-review pose intentionally avoids arm swing so the side silhouette can
catch body, leg, and lean regressions without arm projection hiding the torso.

Generate a Markdown progress report:

```bash
scripts/generate_asset_evidence_report.py \
  --manifest samples/manifest.json \
  --evidence-root . \
  --check-evidence-files \
  --output docs/asset-evidence-progress.local.md
```

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
  --preview-neutral-side evidence/H-001/preview-neutral-side.png \
  --preview-pose evidence/H-001/preview-pose.png \
  --preview-pose-side evidence/H-001/preview-pose-side.png \
  --export-unity-fbx evidence/H-001/export-unity.fbx \
  --notes evidence/H-001/notes.md \
  --deformation-score 4 \
  --visual-review-status pass \
  --visual-review-notes "Front and side pose previews show acceptable shoulder, elbow, knee, and wrist deformation." \
  --unity-status pass \
  --unreal-status blocked \
  --evidence-root . \
  --check-files
```

`create_evidence_skeleton.py` creates only evidence folders and `notes.md` checklists. It does not create fake QA reports, previews, FBX files, or engine import results.

The register script refuses to overwrite an existing slot unless `--force` is passed.

For score 3 or higher, the validator requires quality support beyond the numeric score:
either `visualReview.status=pass` with non-empty `visualReview.notes` plus both
side preview artifacts, or a passing Unity/Unreal import result. This keeps
metric-only `pass`/`warn` outputs or single-view screenshots from being counted
as production-quality deformation evidence.

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
    preview-neutral-side.png
    preview-pose.png
    preview-pose-side.png
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
