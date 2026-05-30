"""Stage VRKitchen asset organization moves inside Unreal Editor.

This script deliberately uses Unreal Editor APIs instead of file-manager moves,
so asset references can be redirected and saved by the editor.

Environment variables:
  VRKITCHEN_ASSET_MIGRATION_PHASES   Comma-separated phases to run.
                                     Default: phase-1
  VRKITCHEN_ASSET_MIGRATION_DRY_RUN  1/true for report only, 0/false to apply.
                                     Default: 1
  VRKITCHEN_ASSET_MIGRATION_FIXUP    1/true to run redirector fix-up in this
                                     commandlet. Default: 0, because UE 5.5
                                     AssetTools can assert in unattended runs.
  VRKITCHEN_ASSET_MIGRATION_REPORT   Optional JSON report path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import unreal


PHASE_1_FOLDERS = (
    "/Game/_Project/Art",
    "/Game/_Project/Art/Audio",
    "/Game/_Project/Art/Environment",
    "/Game/_Project/Art/Food",
    "/Game/_Project/Art/FX",
    "/Game/_Project/Art/Lighting",
    "/Game/_Project/Art/Materials",
    "/Game/_Project/Art/Props",
    "/Game/_Project/Art/Textures",
    "/Game/_Project/Gameplay/Cooking",
    "/Game/_Project/Gameplay/Delivery",
    "/Game/_Project/Gameplay/Food",
    "/Game/_Project/Gameplay/Interaction",
    "/Game/_Project/Gameplay/Orders",
    "/Game/_Project/UI",
    "/Game/_Project/VR",
    "/Game/_External",
    "/Game/_External/Marketplace",
    "/Game/_External/TemplateSource",
    "/Game/_External/TemplateSource/PanStove",
    "/Game/_External/TemplateSource/PanStove/Textures",
    "/Game/_External/TemplateSource/WallMonitor",
    "/Game/_Legacy",
    "/Game/_Legacy/Characters",
    "/Game/_Legacy/FPWeapon",
    "/Game/_Legacy/LevelPrototyping",
    "/Game/_Legacy/Maps",
    "/Game/_Legacy/StarterContent",
    "/Game/_Legacy/VRSpectator",
    "/Game/_Legacy/VRTemplate",
    "/Game/_Dev",
    "/Game/_Dev/Prototypes",
    "/Game/_Dev/TestMaps",
)

DIRECTORY_MOVES = {
    # Empty/editor-only folders first; these are intentionally separate from the
    # large food_test prototype pack so we can migrate in very small batches.
    "phase-2-dev-folders": (
        ("/Game/Collections", "/Game/_Dev/Collections"),
        ("/Game/Developers", "/Game/_Dev/Developers"),
    ),
    "phase-2-prototypes": (
        ("/Game/food_test", "/Game/_Dev/Prototypes/food_test"),
    ),
    "phase-3-external": (
        ("/Game/Fast_Food_Restaurant", "/Game/_External/Marketplace/Fast_Food_Restaurant"),
        ("/Game/SM_PanStove_01.fbm", "/Game/_External/TemplateSource/PanStove/SM_PanStove_01.fbm"),
        ("/Game/SM_WallMonitor_01.fbm", "/Game/_External/TemplateSource/WallMonitor/SM_WallMonitor_01.fbm"),
        ("/Game/SM_WallMonitor_01_fbm", "/Game/_External/TemplateSource/WallMonitor/SM_WallMonitor_01_fbm"),
    ),
    "phase-3-legacy": (
        ("/Game/Characters", "/Game/_Legacy/Characters"),
        ("/Game/FPWeapon", "/Game/_Legacy/FPWeapon"),
        ("/Game/LevelPrototyping", "/Game/_Legacy/LevelPrototyping"),
        ("/Game/Maps", "/Game/_Legacy/Maps/ImportedMaps"),
        ("/Game/StarterContent", "/Game/_Legacy/StarterContent"),
        ("/Game/VRSpectator", "/Game/_Legacy/VRSpectator"),
    ),
    # Do not include /Game/VRTemplate here yet. DefaultInput.ini and the default
    # GameMode still point at VRTemplate assets, so it needs a dedicated pass.
}

ASSET_MOVES = {
    "phase-3-root-legacy": (
        ("/Game/Kitchen_Demo_Map", "/Game/_Legacy/Maps/Kitchen_Demo_Map"),
        ("/Game/Kitchen_Demo_Map_BuiltData", "/Game/_Legacy/Maps/Kitchen_Demo_Map_BuiltData"),
    ),
    "phase-3-root-external": (
        ("/Game/SM_PanStove_01", "/Game/_External/TemplateSource/PanStove/SM_PanStove_01"),
        ("/Game/texture_pbr_20250901", "/Game/_External/TemplateSource/PanStove/Textures/texture_pbr_20250901"),
        ("/Game/texture_pbr_20250901_metallic", "/Game/_External/TemplateSource/PanStove/Textures/texture_pbr_20250901_metallic"),
        ("/Game/texture_pbr_20250901_normal", "/Game/_External/TemplateSource/PanStove/Textures/texture_pbr_20250901_normal"),
        ("/Game/texture_pbr_20250901_roughness", "/Game/_External/TemplateSource/PanStove/Textures/texture_pbr_20250901_roughness"),
    ),
    "phase-4-root-gameplay": (
        ("/Game/BP_Pan", "/Game/_Project/Gameplay/Cooking/BP_Pan"),
        ("/Game/BP_Stove", "/Game/_Project/Gameplay/Cooking/BP_Stove"),
        ("/Game/BP_PickFood", "/Game/_Project/Gameplay/Food/BP_PickFood"),
        ("/Game/BP_Tomato", "/Game/_Project/Gameplay/Food/BP_Tomato"),
        ("/Game/BP_Plate", "/Game/_Project/Gameplay/Delivery/BP_Plate"),
    ),
    "phase-4-food-blueprints": (
        ("/Game/Blueprints/BP_BottomBun", "/Game/_Project/Gameplay/Food/BP_BottomBun"),
        ("/Game/Blueprints/BP_ChoppedLettuce", "/Game/_Project/Gameplay/Food/BP_ChoppedLettuce"),
        ("/Game/Blueprints/BP_ChoppedTomato", "/Game/_Project/Gameplay/Food/BP_ChoppedTomato"),
        ("/Game/Blueprints/BP_FoodSpawner", "/Game/_Project/Gameplay/Food/BP_FoodSpawner"),
        ("/Game/Blueprints/BP_Lettuce", "/Game/_Project/Gameplay/Food/BP_Lettuce"),
        ("/Game/Blueprints/BP_Meat", "/Game/_Project/Gameplay/Food/BP_Meat"),
        ("/Game/Blueprints/BP_Patty", "/Game/_Project/Gameplay/Food/BP_Patty"),
        ("/Game/Blueprints/BP_TopBun", "/Game/_Project/Gameplay/Food/BP_TopBun"),
        ("/Game/Blueprints/BP_row_meat", "/Game/_Project/Gameplay/Food/BP_RowMeat"),
    ),
    "phase-4-interaction-blueprints": (
        ("/Game/Blueprints/BP_Bin", "/Game/_Project/Gameplay/Interaction/BP_Bin"),
        ("/Game/Blueprints/BP_CuttingBoard", "/Game/_Project/Gameplay/Interaction/BP_CuttingBoard"),
        ("/Game/Blueprints/BP_Knife", "/Game/_Project/Gameplay/Interaction/BP_Knife"),
        ("/Game/Blueprints/BP_Sponge", "/Game/_Project/Gameplay/Interaction/BP_Sponge"),
    ),
    "phase-4-legacy-duplicates": (
        ("/Game/Blueprints/BP_OrderTablet", "/Game/_Legacy/Blueprints/BP_OrderTablet"),
        ("/Game/Blueprints/ST_Recipe", "/Game/_Legacy/Blueprints/ST_Recipe"),
        ("/Game/Blueprints/WBP_Orderscreen", "/Game/_Legacy/Blueprints/WBP_Orderscreen"),
    ),
}

VALID_PHASES = {"phase-1"} | set(DIRECTORY_MOVES) | set(ASSET_MOVES)
FIXUP_PATHS = ("/Game",)


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def selected_phases() -> list[str]:
    raw = os.environ.get("VRKITCHEN_ASSET_MIGRATION_PHASES", "phase-1")
    phases = [phase.strip() for phase in raw.split(",") if phase.strip()]
    unknown = [phase for phase in phases if phase not in VALID_PHASES]
    if unknown:
        raise RuntimeError(f"Unknown migration phase(s): {', '.join(unknown)}")
    return phases


class Runner:
    def __init__(self, dry_run: bool, fixup_redirectors: bool):
        self.dry_run = dry_run
        self.fixup_redirectors = fixup_redirectors
        self.results: list[dict[str, str]] = []
        self.errors: list[str] = []

    def record(self, status: str, action: str, source: str, target: str = "", detail: str = "") -> None:
        entry = {
            "status": status,
            "action": action,
            "source": source,
            "target": target,
            "detail": detail,
        }
        self.results.append(entry)
        message = f"[{status}] {action}: {source}"
        if target:
            message += f" -> {target}"
        if detail:
            message += f" ({detail})"
        unreal.log(message)

    def ensure_directory(self, path: str) -> None:
        if unreal.EditorAssetLibrary.does_directory_exist(path):
            self.record("skip", "ensure-directory", path, detail="already exists")
            return
        if self.dry_run:
            self.record("plan", "ensure-directory", path)
            return
        if not unreal.EditorAssetLibrary.make_directory(path):
            self.fail(f"Failed to create directory: {path}")
            return
        self.record("ok", "ensure-directory", path)

    def ensure_parent_directory(self, asset_path: str) -> None:
        parent = asset_path.rsplit("/", 1)[0]
        self.ensure_directory(parent)

    def cleanup_empty_directory(self, path: str) -> None:
        if not unreal.EditorAssetLibrary.does_directory_exist(path):
            self.record("skip", "cleanup-empty-directory", path, detail="source missing")
            return

        assets = unreal.EditorAssetLibrary.list_assets(path, recursive=True, include_folder=False)
        if assets:
            self.record("skip", "cleanup-empty-directory", path, detail=f"{len(assets)} assets remain")
            return

        if self.dry_run:
            self.record("plan", "cleanup-empty-directory", path)
            return

        if not unreal.EditorAssetLibrary.delete_directory(path):
            self.fail(f"Failed to delete empty directory: {path}")
            return
        self.record("ok", "cleanup-empty-directory", path)

    def move_asset(self, source: str, target: str) -> None:
        if not unreal.EditorAssetLibrary.does_asset_exist(source):
            self.record("skip", "move-asset", source, target, "source missing")
            return
        if unreal.EditorAssetLibrary.does_asset_exist(target):
            self.record("skip", "move-asset", source, target, "target already exists")
            return
        if self.dry_run:
            self.record("plan", "move-asset", source, target)
            return
        self.ensure_parent_directory(target)
        if not unreal.EditorAssetLibrary.rename_asset(source, target):
            self.fail(f"Failed to move asset: {source} -> {target}")
            return
        self.record("ok", "move-asset", source, target)

    def move_directory(self, source: str, target: str) -> None:
        if not unreal.EditorAssetLibrary.does_directory_exist(source):
            self.record("skip", "move-directory", source, target, "source missing")
            return
        if unreal.EditorAssetLibrary.does_directory_exist(target):
            self.record("skip", "move-directory", source, target, "target already exists")
            return
        if self.dry_run:
            self.record("plan", "move-directory", source, target)
            return
        parent = target.rsplit("/", 1)[0]
        self.ensure_directory(parent)
        if not unreal.EditorAssetLibrary.rename_directory(source, target):
            self.fail(f"Failed to move directory: {source} -> {target}")
            return
        self.record("ok", "move-directory", source, target)
        self.cleanup_empty_directory(source)

    def fixup_and_save(self) -> None:
        if self.dry_run:
            self.record("plan", "fixup-redirectors", ", ".join(FIXUP_PATHS))
            self.record("plan", "save-directory", "/Game")
            return

        if self.fixup_redirectors and hasattr(unreal, "UnrealBridgeEditorLibrary"):
            count = unreal.UnrealBridgeEditorLibrary.fixup_redirectors(list(FIXUP_PATHS))
            self.record("ok", "fixup-redirectors", ", ".join(FIXUP_PATHS), detail=f"{count} redirectors")
        else:
            self.record(
                "skip",
                "fixup-redirectors",
                ", ".join(FIXUP_PATHS),
                detail="run Fix Up Redirectors manually in the Unreal Editor after asset moves",
            )

        saved = unreal.EditorAssetLibrary.save_directory("/Game", only_if_is_dirty=True, recursive=True)
        self.record("ok" if saved else "warn", "save-directory", "/Game", detail=str(saved))

    def fail(self, message: str) -> None:
        self.errors.append(message)
        self.record("fail", "error", message)


def write_report(path: str, payload: dict) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    dry_run = env_bool("VRKITCHEN_ASSET_MIGRATION_DRY_RUN", True)
    fixup_redirectors = env_bool("VRKITCHEN_ASSET_MIGRATION_FIXUP", False)
    phases = selected_phases()
    runner = Runner(dry_run=dry_run, fixup_redirectors=fixup_redirectors)

    unreal.log(f"VRKitchen asset migration phases: {', '.join(phases)}")
    unreal.log(f"VRKitchen asset migration dry run: {dry_run}")
    unreal.log(f"VRKitchen asset migration fixup redirectors: {fixup_redirectors}")

    if "phase-1" in phases:
        for folder in PHASE_1_FOLDERS:
            runner.ensure_directory(folder)

    for phase in phases:
        for source, target in DIRECTORY_MOVES.get(phase, ()):
            runner.move_directory(source, target)
        for source, target in ASSET_MOVES.get(phase, ()):
            runner.move_asset(source, target)

    for phase in phases:
        for source, _target in DIRECTORY_MOVES.get(phase, ()):
            runner.cleanup_empty_directory(source)

    runner.fixup_and_save()

    payload = {
        "dry_run": dry_run,
        "phases": phases,
        "errors": runner.errors,
        "results": runner.results,
    }
    report_path = os.environ.get("VRKITCHEN_ASSET_MIGRATION_REPORT")
    if report_path:
        write_report(report_path, payload)
        unreal.log(f"Wrote migration report: {report_path}")

    if runner.errors:
        raise RuntimeError("; ".join(runner.errors))


main()
