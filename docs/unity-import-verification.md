# Unity Import Verification

This document describes the repeatable Unity import check for exported Mac Game Rigger FBX files.

## Current Verified Editor

Local Unity Editor path used during alpha smoke:

```text
/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity
```

`unity` is not assumed to be available on `PATH`; pass the editor path explicitly.

## Command

```bash
scripts/verify_unity_fbx_import.sh \
  --fbx <exported.fbx> \
  --unity /Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity \
  --timeout-seconds 180
```

Expected successful output:

```json
{"status":"pass","assetPath":"Assets/MacGameRiggerImportCandidate/<file>.fbx"}
```

## What The Verifier Checks

The verifier creates a temporary Unity project, copies the FBX into `Assets/MacGameRiggerImportCandidate/`, opens Unity in batch mode, and runs `MacGameRiggerFbxImportCheck`.

The editor script checks that:

- the asset imports through Unity's asset database;
- the imported object can be loaded;
- the import process exits with a pass/fail status that the shell script can parse.

## Known Environment Constraint

Unity batchmode fails inside the current sandbox because Unity Package Manager cannot open its local socket:

```text
listen EPERM ... Unity-Upm-*.sock
```

Run this verifier outside the sandbox. A stale Unity Licensing Client process may also block batchmode startup; restart that process or Unity Hub if the verifier stalls before import.

## Alpha Evidence

Alpha smoke has one successful Unity batchmode import verifier pass for a generated Unity FBX export. This satisfies the internal alpha import gate, but it is not enough for production trial.

## Production Trial Gate

Before production trial, collect:

- at least 3 real asset Unity import passes;
- at least 1 humanoid asset with avatar/generic rig notes;
- at least 1 non-humanoid/generic asset import pass;
- scale/orientation notes for each imported asset;
- QA JSON and preview PNG linked to the same exported FBX.

## Failure Triage

If the verifier fails, capture:

- Unity version and full editor path;
- FBX path;
- verifier JSON output;
- Unity editor log tail;
- whether failure happened before asset import or during asset validation.
