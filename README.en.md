<div align="center">

# VRKitchen

### Unreal Engine 5.5.4 · Windows PCVR kitchen interaction demo

<p>
  <a href="https://github.com/Crossng/VRKitchen"><img src="https://img.shields.io/badge/project%20status-archived-2ea44f?style=flat-square" alt="Project status: archived"></a>
  <a href="https://www.unrealengine.com/"><img src="https://img.shields.io/badge/Unreal%20Engine-5.5.4-313131?style=flat-square&logo=unrealengine" alt="Unreal Engine 5.5.4"></a>
  <a href="https://github.com/Crossng/VRKitchen"><img src="https://img.shields.io/badge/platform-Windows%20PCVR-0078D4?style=flat-square" alt="Platform: Windows PCVR"></a>
  <a href="https://github.com/Crossng/VRKitchen/actions/workflows/maintenance.yml"><img src="https://github.com/Crossng/VRKitchen/actions/workflows/maintenance.yml/badge.svg" alt="Repository checks"></a>
</p>

<p>
  <strong>Receive orders → Prepare ingredients → Cook → Plate in order → Serve and score</strong>
</p>

<p>
  <a href="README.md">简体中文</a>
  ·
  <strong>English</strong>
</p>

</div>

---

## Overview

VRKitchen is a Windows PCVR kitchen interaction demo. Players follow orders, prepare ingredients, cook, plate, and serve as many correct orders as possible within a time limit.

The project has completed its planned goals and is officially archived. This repository is a code archive of the final version, containing source code, configuration, plugin source, verification tools, and project documentation. The complete project assets are distributed separately through Baidu Netdisk.

## Project at a glance

| Item | Details |
| --- | --- |
| Project status | Archived / final version |
| Development engine | Unreal Engine 5.5.4 |
| Runtime platform | Windows PCVR |
| VR runtime | SteamVR / OpenXR |
| Demo map | `/Game/_Project/Maps/VRKitchen_Demo` |
| Main technologies | C++, Blueprint, and Python tools |

## Download the complete project

> [!IMPORTANT]
> GitHub contains only source code and small tools. Download the complete Unreal project assets from Baidu Netdisk.

The complete project files, including `VRCrazyKitchen.zip` and one additional file, are available here:

<div align="center">

### [⬇️ Download the complete project](https://pan.baidu.com/s/1FlrQ5vl0GHLvo42fHb5gmA?pwd=rdnf)

**Extraction code: `rdnf`**

</div>

## Demo content

### Core gameplay

- Chinese-language order board, order feedback, and serving results
- Ingredient pickup, cutting, cooking, plating, and submission
- Cutting lettuce and tomatoes, plus pan-frying raw meat and raw patties
- Salad dressing and cold-dish preparation flow
- Strict validation of ingredient state, quantity, and plating order
- Failure feedback for raw, uncut, burned, and incorrectly ordered ingredients
- Plate clearing and ingredient recycling

### Menu progression

```text
Classic Burger
      ↓
Pan-Seared Steak
      ↓
Garden Salad
      ↓
Lettuce Burger · Tomato Burger
      ↓
Thick Patty Lettuce Burger · Deluxe Double-Meat Burger
      ↓
Steak Salad Combo · Classic Burger Salad Combo
```

### Rounds and scoring

- Three-minute demo round
- Correct orders add points; incorrect orders subtract points
- Consecutive completed orders earn combo bonuses
- One-, two-, and three-star results based on score
- The results screen shows completed orders, errors, accuracy, best combo, and practice suggestions

## Quick start

1. Download and extract the complete project from the Baidu Netdisk link above.
2. To use the latest code from GitHub, merge the repository's `VRKitchen/` folder into the root of the complete project.
3. Keep the complete project's `Content/` assets. Do not commit the asset directory or build products back to GitHub.
4. Open `VRKitchen/VRKitchen.uproject` with Unreal Engine 5.5.4.
5. When using SteamVR, set SteamVR as the OpenXR Runtime and connect a PCVR headset.
6. Run `/Game/_Project/Maps/VRKitchen_Demo`.

Without a headset, you can still compile code and Blueprints, validate data, and verify a Win64 package, but these checks cannot replace real VR interaction testing.

## Repository structure

```text
VRKitchen/
├── Config/                         Project configuration
├── Plugins/UnrealBridge/            Unreal Editor helper plugin
├── Source/VRKitchen/               VRKitchen C++ source
└── VRKitchen.uproject               Unreal project file

tools/
├── verify_demo_gameplay_loop_via_bridge.py      Gameplay-flow verification
├── verify_demo_content_design_via_bridge.py     Demo content verification
├── verify_demo_map_content_via_bridge.py        Demo map verification
├── verify_demo_menu_quality_via_bridge.py       Menu quality verification
├── verify_delivery_readiness.py                 Delivery-boundary checks
└── verify_asset_organization.py                 Asset organization audit
```

## Completion verification record

The final version completed the following checks:

- `VRKitchenEditor Win64 Development` C++ build
- `CompileAllBlueprints` Blueprint compilation
- `DataValidation` asset data validation
- Win64 Development packaging
- Core Actor and spatial relationship checks for the demo map
- Verification of the nine-dish menu, salads, combos, and three-star scoring flow
- Verification of cooking, burning, cutting, plating order, and error feedback

<details>
<summary>View lightweight repository checks</summary>

These checks do not require downloading `Content/`. They verify Python tool syntax, repository boundaries, and basic regressions:

```bash
python3 -m compileall -q tools
python3 -m unittest discover -s tools/tests -p 'test_*.py'
python3 tools/verify_delivery_readiness.py --skip-full-project --code-repo-root .
```

For complete-project verification, see [`VRKitchen_DELIVERY.md`](VRKitchen_DELIVERY.md).

</details>

## Asset submission boundary

The GitHub repository contains only code, configuration, plugin source, documentation, and small tools. The following remain in the complete project or the Netdisk archive:

- `Content/`
- `Binaries/`
- `Intermediate/`
- `Saved/`
- `DerivedDataCache/`
- Large assets and build products such as `.uasset`, `.umap`, `.fbx`, `.zip`, `.pdb`, and `.exe`

Asset directory conventions and migration notes:

- [`VRKitchen_ASSET_ORGANIZATION.md`](VRKitchen_ASSET_ORGANIZATION.md)
- [`VRKitchen_ASSET_MIGRATION_PLAN.md`](VRKitchen_ASSET_MIGRATION_PLAN.md)

## Related documentation

- [`VRKitchen_DELIVERY.md`](VRKitchen_DELIVERY.md): runtime environment, deliverables, and verification record
- [`VRKitchen_ASSET_ORGANIZATION.md`](VRKitchen_ASSET_ORGANIZATION.md): asset directory and naming conventions
- [`VRKitchen_ASSET_MIGRATION_PLAN.md`](VRKitchen_ASSET_MIGRATION_PLAN.md): asset migration plan and notes

The supporting documents linked above are currently available in Chinese.

## License

This repository does not include a standalone `LICENSE` file. Contact the repository owner to confirm the authorization scope before copying, modifying, or redistributing project content.
