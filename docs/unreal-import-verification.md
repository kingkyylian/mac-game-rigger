# Unreal Import Verification

Unreal import validation is not yet complete. The verifier can now prepare a
repeatable Unreal import workspace and run an Unreal Editor executable with the
prepared Python import script, but the local alpha environment has not produced
a real Unreal Editor import pass yet.

## Current Status

`UnrealEditor` is not currently available on `PATH`, so alpha smoke has not verified a real Unreal import.

Implemented locally:

- FBX input validation;
- Unreal Editor path validation for dry-run/non-dry-run modes;
- prepare-only workspace creation without requiring Unreal Editor;
- Unreal Python import script template;
- unattended editor invocation with machine-readable config/result paths;
- machine-readable failure when Unreal exits without writing a result JSON.

Unity import verification has passed once, but Unity success does not prove Unreal success. Unreal can expose separate FBX problems:

- bone axis mismatch;
- root bone naming;
- scale mismatch;
- leaf bone behavior;
- material import differences;
- skeleton asset creation issues.

## Required Local Inputs

To run Unreal import verification, the machine needs:

- an installed Unreal Editor;
- the full path to `UnrealEditor`;
- an exported FBX from Mac Game Rigger;
- a temporary project or scripted throwaway project location.

Candidate editor path examples:

```text
/Applications/Epic Games/UE_5.4/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor
/Users/Shared/Epic Games/UE_5.4/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor
```

## Current Command

Current environment/path check:

```bash
scripts/verify_unreal_fbx_import.sh \
  --fbx <exported.fbx> \
  --unreal <path-to-UnrealEditor> \
  --timeout-seconds 240 \
  --dry-run
```

Expected dry-run output:

```json
{"status":"ready","unrealEditor":"<path-to-UnrealEditor>","fbx":"<exported.fbx>","timeoutSeconds":240}
```

Prepare a throwaway Unreal import workspace without requiring Unreal Editor:

```bash
scripts/verify_unreal_fbx_import.sh \
  --fbx <exported.fbx> \
  --project /tmp/MacGameRiggerImportCheck \
  --prepare-only
```

Expected prepare-only output:

```json
{
  "status": "prepared",
  "projectPath": "/tmp/MacGameRiggerImportCheck",
  "projectFile": "/tmp/MacGameRiggerImportCheck/MacGameRiggerImportCheck.uproject",
  "copiedFbx": "/tmp/MacGameRiggerImportCheck/Import/<exported.fbx>",
  "scriptPath": "/tmp/MacGameRiggerImportCheck/Content/Python/MacGameRiggerFbxImportCheck.py",
  "configPath": "/tmp/MacGameRiggerImportCheck/Saved/MacGameRiggerImportCheck/import-config.json",
  "resultPath": "/tmp/MacGameRiggerImportCheck/Saved/MacGameRiggerImportCheck/import-result.json"
}
```

Run the prepared Unreal import check:

```bash
scripts/verify_unreal_fbx_import.sh \
  --fbx <exported.fbx> \
  --unreal <path-to-UnrealEditor> \
  --project /tmp/MacGameRiggerImportCheck \
  --timeout-seconds 240
```

Expected successful output includes:

```json
{
  "status": "pass",
  "projectPath": "/tmp/MacGameRiggerImportCheck",
  "resultPath": "/tmp/MacGameRiggerImportCheck/Saved/MacGameRiggerImportCheck/import-result.json",
  "unrealExitCode": 0,
  "importedObjectPaths": ["/Game/MacGameRiggerImportCandidate/<asset>"]
}
```

If Unreal exits but the Python import script does not write the result JSON, the
verifier exits non-zero with `reason: "unreal_result_missing"` and stores stdout
and stderr logs under `Saved/MacGameRiggerImportCheck/`.

## Minimum Checks

The Unreal runner checks or records:

- Unreal starts in unattended/batch mode;
- the FBX can be imported;
- a skeletal mesh or static mesh asset is created as expected;
- skeleton/root bone information is available for skeletal imports;
- import logs do not contain fatal FBX errors;
- the script exits non-zero on failure.

## Production Trial Gate

Before production trial, collect:

- at least 1 humanoid Unreal import pass;
- at least 1 non-humanoid or quadruped Unreal import pass;
- scale/orientation notes;
- imported skeleton naming notes;
- FBX export profile used for each import.

## Current Blocker

Current blockers:

- `UnrealEditor` needs to be installed or its path supplied on the local machine.
- A real Unreal Editor run still needs to be captured for at least one humanoid and one non-humanoid exported FBX. Until that evidence exists, Unreal import is implemented as a verifier path but not proven as a production-trial pass.
