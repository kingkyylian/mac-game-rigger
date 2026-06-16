# Unreal Import Verification

Unreal import validation is not yet complete. This document defines the missing gate and the first implementation target.

## Current Status

`UnrealEditor` is not currently available on `PATH`, so alpha smoke has not verified a real Unreal import.

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

Without `--dry-run`, the script currently returns a machine-readable blocked result because the real Unreal batch import commandlet is not implemented yet:

```json
{"status":"blocked","reason":"unreal_batch_import_not_implemented","unrealEditor":"<path-to-UnrealEditor>","fbx":"<exported.fbx>","timeoutSeconds":240}
```

## Minimum Checks

The first Unreal verifier should check:

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

There are two current blockers:

- `UnrealEditor` needs to be installed or its path supplied on the local machine.
- The Unreal batch import commandlet still needs to be implemented. Until then, `scripts/verify_unreal_fbx_import.sh` can verify inputs and report `blocked`, but cannot prove a real Unreal import pass.
