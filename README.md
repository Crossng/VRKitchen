# VRKitchen Code-Only Repository

This repository intentionally contains only code, configuration, and small tooling for the VRKitchen Unreal Engine 5.5.4 project.

The full Unreal project assets are delivered separately through cloud storage/netdisk. Do not commit large binary project data here.

## Current demo scope

- Target: UE 5.5.4, Windows PCVR, SteamVR through OpenXR.
- Demo map: `/Game/_Project/Maps/VRKitchen_Demo`.
- Gameplay loop: Chinese order feedback, validated plate submission, pan/stove cooking, overcooked burnt food rejection, 3-minute session timer, score target, streak bonus, mission clear result, star rating, correct/wrong counters, and progressive burger orders.
- Not verified here: real SteamVR headset feel, controller hand feel, Quest/Android standalone runtime.

## How to use

1. Download the full VRKitchen project package from netdisk/cloud storage.
2. Overlay this repository's `VRKitchen/` folder onto the full project folder.
3. Open `VRKitchen/VRKitchen.uproject` with Unreal Engine 5.5.4.
4. Rebuild the `VRKitchen` C++ module if prompted.
5. Run `CompileAllBlueprints`, `DataValidation`, and `tools/verify_demo_gameplay_loop_via_bridge.py` before sharing a release.

## Delivery self-check

Before pushing code or uploading the full project to netdisk, run the delivery boundary check:

```powershell
python tools/verify_delivery_readiness.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen --code-repo-root C:\Users\hp\Desktop\VRKitchen_CodeOnly
```

The script checks that the full project still contains the demo map, source, config, plugin, and delivery docs, and that the code-only GitHub repository does not track `Content`, `.uasset`, `.umap`, binaries, package outputs, or oversized files.

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
