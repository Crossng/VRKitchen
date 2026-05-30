# VRKitchen Code-Only Repository

This repository intentionally contains only code, configuration, and small tooling for the VRKitchen Unreal Engine 5.5.4 project.

The full Unreal project assets are delivered separately through cloud storage/netdisk. Do not commit large binary project data here.

## How to use

1. Download the full VRKitchen project package from netdisk/cloud storage.
2. Overlay this repository's `VRKitchen/` folder onto the full project folder.
3. Open `VRKitchen/VRKitchen.uproject` with Unreal Engine 5.5.4.
4. Rebuild the `VRKitchen` C++ module if prompted.
5. Run `CompileAllBlueprints` and `DataValidation` before sharing a release.

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
