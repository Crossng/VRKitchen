#!/usr/bin/env python3
"""Audit VRKitchen Content organization without moving assets.

The default mode is advisory: it reports legacy/root-level assets and naming
issues as warnings. Use --strict when the project is ready to enforce the final
layout after assets have been migrated inside Unreal Editor.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


ALLOWED_TOP_LEVEL_DIRS = {
    "_Project",
    "_External",
    "_Legacy",
    "_Dev",
}

EXPECTED_PROJECT_DIRS = (
    "_Project/Maps",
    "_Project/Core",
    "_Project/Gameplay",
    "_Project/UI",
    "_Project/Art",
)

LEGACY_CANDIDATE_DIRS = {
    "StarterContent",
    "VRTemplate",
    "LevelPrototyping",
    "FPWeapon",
    "VRSpectator",
}

EXTERNAL_CANDIDATE_DIRS = {
    "Fast_Food_Restaurant",
    "SM_PanStove_01.fbm",
    "SM_WallMonitor_01.fbm",
    "SM_WallMonitor_01_fbm",
}

DEV_CANDIDATE_DIRS = {
    "Developers",
    "food_test",
}

ASSET_SUFFIXES = {
    ".uasset",
    ".umap",
    ".ubulk",
    ".uexp",
    ".fbx",
    ".wav",
    ".mp3",
    ".png",
    ".jpg",
    ".jpeg",
    ".tga",
}

ALLOWED_ASSET_PREFIXES = (
    "BP_",
    "WBP_",
    "M_",
    "MI_",
    "T_",
    "SM_",
    "SK_",
    "ABP_",
    "A_",
    "DA_",
    "DT_",
    "E_",
    "SFX_",
    "BGM_",
    "NS_",
    "MF_",
)

MAP_NAME_EXCEPTIONS = {
    "VRKitchen_Demo",
    "VRTemplateMap",
    "Kitchen_Demo_Map",
}


@dataclass
class Check:
    level: str
    message: str


def add(results: list[Check], level: str, message: str) -> None:
    results.append(Check(level, message))


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def first_items(items: list[str], limit: int = 20) -> str:
    visible = items[:limit]
    suffix = "" if len(items) <= limit else f" ... (+{len(items) - limit} more)"
    return ", ".join(visible) + suffix


def classify_legacy_dir(name: str) -> str:
    if name in LEGACY_CANDIDATE_DIRS:
        return "_Legacy"
    if name in EXTERNAL_CANDIDATE_DIRS:
        return "_External"
    if name in DEV_CANDIDATE_DIRS:
        return "_Dev"
    return "_Project or _External after reference review"


def has_good_asset_name(path: Path) -> bool:
    stem = path.stem
    suffix = path.suffix.lower()
    if suffix == ".umap":
        return stem in MAP_NAME_EXCEPTIONS or stem.startswith(("MAP_", "L_"))
    if suffix in {".ubulk", ".uexp"}:
        return True
    return stem.startswith(ALLOWED_ASSET_PREFIXES)


def audit_content(full_project_root: Path, strict: bool) -> list[Check]:
    results: list[Check] = []
    content_root = full_project_root / "Content"
    add(results, "INFO", f"Full project root: {full_project_root}")

    if not content_root.exists():
        add(results, "FAIL", "Missing Content directory")
        return results

    add(results, "PASS", "Content directory exists")

    for relative_dir in EXPECTED_PROJECT_DIRS:
        target = content_root / relative_dir
        if target.exists():
            add(results, "PASS", f"Expected project folder exists: Content/{relative_dir}")
        else:
            add(results, "WARN", f"Expected future folder is missing: Content/{relative_dir}")

    demo_map = content_root / "_Project" / "Maps" / "VRKitchen_Demo.umap"
    if demo_map.exists():
        add(results, "PASS", "Demo map is already isolated under Content/_Project/Maps")
    else:
        add(results, "FAIL", "Demo map is not under Content/_Project/Maps/VRKitchen_Demo.umap")

    top_level_dirs = [item for item in content_root.iterdir() if item.is_dir()]
    unclassified_dirs = sorted(
        item.name for item in top_level_dirs if item.name not in ALLOWED_TOP_LEVEL_DIRS
    )
    if unclassified_dirs:
        for name in unclassified_dirs:
            add(results, "WARN", f"Top-level folder needs classification: Content/{name} -> Content/{classify_legacy_dir(name)}")
    else:
        add(results, "PASS", "Only approved top-level Content folders are present")

    root_asset_files = sorted(
        relpath(item, content_root)
        for item in content_root.iterdir()
        if item.is_file() and item.suffix.lower() in ASSET_SUFFIXES
    )
    if root_asset_files:
        add(results, "WARN", "Root-level Content assets should be moved in Unreal Editor: " + first_items(root_asset_files))
    else:
        add(results, "PASS", "No root-level asset files in Content")

    bad_names = sorted(
        relpath(item, content_root)
        for item in content_root.rglob("*")
        if item.is_file()
        and item.suffix.lower() in ASSET_SUFFIXES
        and not has_good_asset_name(item)
    )
    if bad_names:
        add(results, "WARN", "Assets that do not follow the naming prefix guide: " + first_items(bad_names))
    else:
        add(results, "PASS", "Scanned asset filenames follow the naming prefix guide")

    if strict:
        for result in results:
            if result.level == "WARN":
                result.level = "FAIL"

    return results


def print_results(results: list[Check]) -> int:
    counts = {"INFO": 0, "PASS": 0, "WARN": 0, "FAIL": 0}
    for result in results:
        counts[result.level] = counts.get(result.level, 0) + 1
        print(f"[{result.level}] {result.message}")

    print()
    print(f"Summary: {counts['PASS']} pass, {counts['WARN']} warn, {counts['FAIL']} fail")
    return 1 if counts["FAIL"] else 0


def parse_args() -> argparse.Namespace:
    script_root = Path(__file__).resolve().parent.parent
    default_full_project = script_root / "VRKitchen"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-project-root",
        type=Path,
        default=default_full_project,
        help="Path to the full Unreal project root that contains Content.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat organization warnings as failures after migration is complete.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return print_results(audit_content(args.full_project_root.expanduser().resolve(), args.strict))


if __name__ == "__main__":
    sys.exit(main())

