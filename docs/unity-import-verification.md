# Unity Import Verification

This document describes the repeatable Unity import check for exported Mac Game Rigger FBX files.

## Current Verified Editor

Local Unity Editor path used during alpha smoke:

```text
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity
```

`unity` is not assumed to be available on `PATH`; pass the editor path explicitly.

## Command

Use the recorder when the result should become production evidence:

```bash
scripts/record_unity_import_evidence.py \
  --fbx evidence/H-003/export-unity.fbx \
  --unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  --timeout-seconds 240
```

The recorder runs the verifier and writes the wrapped result to
`evidence/<slot>/unity-import.json`. If Unity or the verifier fails, it exits
non-zero without overwriting existing evidence.

List all score >= 3 humanoid Unity-pass assets still missing configured Animator
smoke before running or re-running a migration batch:

```bash
scripts/check_unity_batchmode_health.py \
  --unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  --timeout-seconds 90

scripts/plan_unity_animator_smoke_migration.py \
  --manifest samples/manifest.json \
  --evidence-root . \
  --unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  --timeout-seconds 240
```

After Unity licensing is confirmed healthy, run the whole migration batch with:

```bash
scripts/run_unity_animator_smoke_migration.py \
  --manifest samples/manifest.json \
  --evidence-root . \
  --unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  --timeout-seconds 240
```

Use `--dry-run` first to list commands without starting Unity. The batch runner
automatically runs the same Unity batchmode health check before recorder
commands, writes `build/unity-batchmode-health.json`, then stops on the first
recorder failure so later evidence files are not touched after a licensing or
import problem. Pass `--preflight-output <path>` to write that health report
somewhere else. Use `--skip-preflight` only when Unity batchmode health was
already checked in the same terminal session.

To audit the strict configured Animator gate, run:

```bash
python3 scripts/validate_asset_evidence.py \
  --manifest samples/manifest.json \
  --evidence-root . \
  --require-configured-animator-smoke \
  --quiet
```

This command is expected to pass for the current evidence set. The planner
currently reports no configured Animator smoke migration gaps.

Use the raw verifier when debugging Unity import output before recording it:

```bash
scripts/verify_unity_fbx_import.sh \
  --fbx <exported.fbx> \
  --unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  --timeout-seconds 180
```

Expected successful output:

```json
{
  "status": "pass",
  "assetPath": "Assets/MacGameRiggerImportCandidate/<file>.fbx",
  "assetName": "<file>",
  "instantiated": true,
  "childCount": 20,
  "rendererCount": 1,
  "skinnedMeshRendererCount": 1,
  "meshFilterCount": 0,
  "animatorCount": 1,
  "boundsSmoke": {
    "passed": true,
    "boundsCenter": {"x": 0, "y": 1.87617242, "z": -0.02561009},
    "boundsSize": {"x": 3.23966861, "y": 3.78952384, "z": 1.33727825},
    "boundsHeight": 3.78952384,
    "maxDimension": 3.78952384
  },
  "boneTransformSmoke": {
    "passed": true,
    "boneCandidateCount": 17,
    "testedBone": "Hips",
    "rotationDeltaDegrees": 4.99997
  },
  "animationClipSmoke": {
    "passed": true,
    "sampledBone": "Hips",
    "sampledBonePath": "MGR_Armature/Hips",
    "sampledRotationDeltaDegrees": 90.2450943
  },
  "configuredAnimatorSmoke": {
    "passed": true,
    "animatorCount": 1,
    "controllerAssigned": true,
    "stateCount": 1,
    "sampledBone": "Hips",
    "sampledBonePath": "MGR_Armature/Hips",
    "sampledRotationDeltaDegrees": 90.2450943
  },
  "humanoidAvatarSmoke": {
    "passed": true,
    "avatarIsValid": true,
    "avatarIsHuman": true,
    "retargetReady": true,
    "mappedHumanBoneCount": 17,
    "requiredHumanBoneCount": 17
  },
  "modelImporter": {
    "available": true,
    "animationType": "Generic",
    "importAnimation": true,
    "globalScale": 1
  }
}
```

## What The Verifier Checks

The verifier creates a temporary Unity project, copies the FBX into `Assets/MacGameRiggerImportCandidate/`, opens Unity in batch mode, and runs `MacGameRiggerFbxImportCheck`.

The editor script checks that:

- the asset imports through Unity's asset database;
- the imported object can be loaded;
- the imported model prefab can be instantiated in an editor scene;
- the instantiated object has at least one renderable mesh component;
- renderer, skinned mesh renderer, mesh filter, animator, and child transform counts are recorded;
- renderer bounds are finite and positive, with center, size, height, and max dimension recorded;
- skinned mesh renderer bone links are sampled and one bone local rotation can be changed in editor batchmode;
- a generated Unity `AnimationClip` can sample a curve onto a linked bone and produce a positive sampled rotation delta;
- a temporary `Animator` and `AnimatorController` can be configured on the imported instance, with one state bound to a generated clip that samples a linked bone;
- for MGR humanoid bone names, Unity `AvatarBuilder.BuildHumanAvatar` can attempt to build a Humanoid Avatar and record whether the result is valid, human, and retarget-ready;
- Unity `ModelImporter` metadata is available and records animation type, animation import setting, and global scale;
- the import process exits with a pass/fail status that the shell script can parse.

## Known Environment Constraint

Unity batchmode fails inside the current sandbox because Unity Package Manager cannot open its local socket:

```text
listen EPERM ... Unity-Upm-*.sock
```

Run this verifier outside the sandbox. A stale Unity Licensing Client process may also block batchmode startup; restart that process or Unity Hub if the verifier stalls before import.

If sandbox-external batchmode reaches Unity but stalls before import, inspect the
log tail for licensing/bootstrap markers such as:

```text
[Licensing::Module] Timed-out after 60.00s, waiting for channel: "LicenseClient-<user>"
[Licensing::Module] Error: 'com.unity.editor.headless' was not found.
```

This means the FBX was not validated yet. Open Unity Hub or the Unity Editor
once to refresh licensing, then rerun `scripts/record_unity_import_evidence.py`
outside the sandbox. The recorder preserves existing evidence on this failure.

For repeatable preflight evidence, write a machine-readable health report before
running individual recorder commands:

```bash
scripts/check_unity_batchmode_health.py \
  --unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  --timeout-seconds 90 \
  --output evidence/unity-batchmode-health.json
```

The JSON report records `status`, `exitCode`, `timedOut`, `unity`,
`timeoutSeconds`, `hint`, `stderr`, and the Unity `logTail`. This keeps the
licensing/bootstrap blocker auditable without overwriting asset import evidence.
The migration batch writes the same report automatically at
`build/unity-batchmode-health.json`.

## Alpha Evidence

Alpha smoke has one successful Unity batchmode import verifier pass for a generated Unity FBX export. This satisfies the internal alpha import gate, but it is not enough for production trial.

## Production Trial Evidence

The production-trial gate now has at least three real asset Unity import passes:

- `H-002`: `evidence/H-002/export-unity.fbx`
- `H-003`: `evidence/H-003/export-unity.fbx`
- `H-004`: `evidence/H-004/export-unity.fbx`
- `H-005`: `evidence/H-005/export-unity.fbx`
- `H-006`: `evidence/H-006/export-unity.fbx`
- `H-009`: `evidence/H-009/export-unity.fbx`
- `H-010`: `evidence/H-010/export-unity.fbx`
- `Q-001`: `evidence/Q-001/export-unity.fbx`
- `Q-002`: `evidence/Q-002/export-unity.fbx`
- `C-001`: `evidence/C-001/export-unity.fbx`
- `P-001`: `evidence/P-001/export-unity.fbx`
- `P-002`: `evidence/P-002/export-unity.fbx`

Each pass was captured with Unity `6000.4.1f1` and recorded in the matching
`evidence/<slot>/unity-import.json` file. The current production evidence now
requires score >= 3 Unity-pass assets to pass bone transform smoke and
generated animation clip sampling smoke, with positive rotation deltas for both.
For score >= 3 humanoid Unity-pass assets, `configuredAnimatorSmoke` is now
validated as a blocking quality signal: the temporary configured Animator must
have a controller, at least one state, and a positive sampled bone rotation
delta. H-002, H-003, H-004, H-005, H-006, H-009, and H-010 currently record this
configured Animator smoke evidence. The gate also requires finite positive
renderer bounds with a positive max dimension and height.

The evidence validator also emits non-blocking Unity scale warnings from
recorded `boundsSmoke.maxDimension`. Current warning limits are 10 Unity units
for humanoids, 12 for quadrupeds, 30 for tail or wing creatures, and 5 for
props. These warnings do not fail the production-trial gate, but they are shown
in `docs/asset-evidence-progress.md`.

Severe scale limits are blocking for score >= 3 Unity-pass assets. Current
severe limits are 100 Unity units for humanoids, 120 for quadrupeds, 300 for
tail or wing creatures, and 50 for props. Assets above these limits are marked
incomplete until the export scale is normalized or the evidence is updated with
a corrected Unity import.

The verifier now emits `humanoidAvatarSmoke` for humanoid evidence. Current
score >= 3 Unity-pass humanoids record passing Humanoid Avatar smoke with valid
human Avatars and complete required human-bone mapping. Invalid
`humanoidAvatarSmoke` blocks score >= 3 humanoid evidence.

For stronger production confidence beyond the current gate, continue collecting:

- retarget-specific playback notes beyond Avatar construction;
- scale normalization evidence for severe Unity scale anomalies;
- prop pivot/origin notes for hinge-like assets;
- QA JSON and preview PNG linked to the same exported FBX.

## Failure Triage

If the verifier fails, capture:

- Unity version and full editor path;
- FBX path;
- verifier JSON output;
- Unity editor log tail;
- whether failure happened before asset import or during asset validation.
