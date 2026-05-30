# VRKitchen Code-Only Repository

This repository intentionally contains only code, configuration, and small tooling for the VRKitchen Unreal Engine 5.5.4 project.

The full Unreal project assets are delivered separately through cloud storage/netdisk. Do not commit large binary project data here.

## Current demo scope

- Target: UE 5.5.4, Windows PCVR, SteamVR through OpenXR.
- Demo map: `/Game/_Project/Maps/VRKitchen_Demo`.
- Gameplay loop: Chinese order feedback, validated plate submission, pan/stove cooking, overcooked burnt food rejection, 3-minute session timer, 115-point score target, streak bonus, mission clear result, star rating, correct/wrong counters, progressive steak, garden salad with dressing, burger, and combo orders, dynamic stage hints, urgency text, and next-goal guidance.
- Not verified here: real SteamVR headset feel, controller hand feel, Quest/Android standalone runtime.

## How to use

1. Download the full VRKitchen project package from netdisk/cloud storage.
2. Overlay this repository's `VRKitchen/` folder onto the full project folder.
3. Open `VRKitchen/VRKitchen.uproject` with Unreal Engine 5.5.4.
4. Rebuild the `VRKitchen` C++ module if prompted.
5. Run `CompileAllBlueprints`, `DataValidation`, `tools/verify_demo_gameplay_loop_via_bridge.py`, and `tools/verify_demo_content_design_via_bridge.py` before sharing a release.

## Delivery self-check

Before pushing code or uploading the full project to netdisk, run the delivery boundary check:

```powershell
python tools/verify_delivery_readiness.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen --code-repo-root C:\Users\hp\Desktop\VRKitchen_CodeOnly
```

The script checks that the full project still contains the demo map, source, config, plugin, and delivery docs, and that the code-only GitHub repository does not track `Content`, `.uasset`, `.umap`, binaries, package outputs, or oversized files.

To verify that the nine-dish demo menu, including garden salad with `Salad_Dressing` and the salad combo orders, is still wired into the player-facing recipe card, order board, station guidance, checklist, and final three-star completion flow:

```powershell
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\verify_demo_content_design_via_bridge.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

To run the lightweight menu-health audit that checks unlock order, unique dish names, Chinese player-facing text, and salad/combo recipe rules:

```powershell
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\verify_demo_menu_quality_via_bridge.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

If the full project map is missing the salad dressing Blueprint or food spawner, run the idempotent repair script in the full project before map/content validation. It saves `.uasset/.umap`, so the resulting assets stay in the netdisk package, not GitHub:

```powershell
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\ensure_salad_dressing_assets_via_bridge.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

If the full project map is missing the raw beef spawner used by steak and steak-salad orders, run:

```powershell
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\ensure_demo_raw_meat_spawner_via_bridge.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

## Asset organization audit

Asset naming and folder rules are documented in `VRKitchen_ASSET_ORGANIZATION.md`, and the staged migration plan is documented in `VRKitchen_ASSET_MIGRATION_PLAN.md`. The current safe workflow is to audit first and only move assets later inside Unreal Editor:

```powershell
python tools/verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen
```

The default audit is advisory. Use `--strict` only after project assets have been migrated and redirectors have been fixed.

To create a Markdown migration report from the full project, including phase/risk/category summaries, the recommended next batch, and a matching dry-run command:

```powershell
python tools/verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_AUDIT.md
```

To dry-run a staged Unreal Editor migration:

```powershell
$env:VRKITCHEN_ASSET_MIGRATION_PHASES='phase-1,phase-2-dev-folders,phase-2-prototypes'
$env:VRKITCHEN_ASSET_MIGRATION_DRY_RUN='1'
$env:VRKITCHEN_ASSET_MIGRATION_REPORT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN.json'
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\migrate_asset_organization_via_editor.py' -unattended -nop4 -nosplash -NullRHI
```

The migration script defaults to dry-run and does not run Fix Up Redirectors in unattended commandlets. After real asset moves, open Unreal Editor and run Fix Up Redirectors from the Content Browser before validation.

Validate every migration dry-run report before moving real assets. The verifier can check a whole phase alias, such as `phase-3` or `phase-4`, or one concrete script phase:

```powershell
python tools/verify_asset_migration_report.py --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN_PHASE3.json --expected-phases phase-3
python tools/verify_asset_migration_report.py --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN_PHASE4.json --expected-phases phase-4
```

If a real migration partially succeeds, audit the current redirector/target state before trying another move. This is read-only and helps decide whether the next step is Content Browser `Fix Up Redirectors`, a smaller migration batch, or manual review:

```powershell
$env:VRKITCHEN_ASSET_MIGRATION_REPORT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_APPLY_PHASE3_CURRENT.json'
$env:VRKITCHEN_ASSET_MIGRATION_AUDIT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_AUDIT_PHASE3_CURRENT.json'
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\audit_asset_migration_state_via_editor.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

## What belongs in GitHub

- `VRKitchen/Source/`
- `VRKitchen/Config/`
- `VRKitchen/VRKitchen.uproject`
- Small helper scripts under `tools/`
- UnrealBridge source/python tooling if needed

## What stays out of GitHub

- `Content/`
- `Binaries/`
- `Intermediate/`
- `Saved/`
- `DerivedDataCache/`
- Large `.uasset`, `.umap`, `.fbx`, `.zip`, `.pdb`, `.exe`, and build artifacts
