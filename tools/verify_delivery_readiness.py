#!/usr/bin/env python3
"""Verify VRKitchen code/netdisk delivery boundaries.

This script is intentionally filesystem-only. It does not launch Unreal, does
not edit assets, and does not replace the existing build/Blueprint/package
validation steps.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


DEMO_MAP_PATH = "/Game/_Project/Maps/VRKitchen_Demo"
MAX_TRACKED_FILE_BYTES = 5 * 1024 * 1024

REQUIRED_FULL_PROJECT_ITEMS = {
    "VRKitchen.uproject": "project file",
    "Content/_Project/Maps/VRKitchen_Demo.umap": "demo map asset",
    "Config/DefaultEngine.ini": "engine config",
    "Config/DefaultGame.ini": "game config",
    "Source/VRKitchen/VRKitchenGameSessionComponent.cpp": "session gameplay source",
    "Source/VRKitchen/VRKitchenOrderValidationLibrary.cpp": "order validation source",
    "Source/VRKitchen/VRKitchenPanCookComponent.cpp": "pan cooking source",
    "Plugins/UnrealBridge/UnrealBridge.uplugin": "UnrealBridge plugin manifest",
    "VRKitchen_DELIVERY.md": "project delivery document",
    "VRKitchen_ASSET_ORGANIZATION.md": "asset organization guide",
    "VRKitchen_ASSET_MIGRATION_PLAN.md": "asset migration plan",
}

REQUIRED_CODE_REPO_ITEMS = {
    ".gitignore": "Git ignore rules",
    "README.md": "code-only repository README",
    "VRKitchen_DELIVERY.md": "root delivery document",
    "VRKitchen/VRKitchen.uproject": "project file copy",
    "VRKitchen/Config/DefaultEngine.ini": "engine config copy",
    "VRKitchen/Config/DefaultGame.ini": "game config copy",
    "VRKitchen/Source/VRKitchen/VRKitchenGameSessionComponent.cpp": "session gameplay source",
    "VRKitchen/Source/VRKitchen/VRKitchenOrderValidationLibrary.cpp": "order validation source",
    "VRKitchen/Source/VRKitchen/VRKitchenPanCookComponent.cpp": "pan cooking source",
    "tools/verify_demo_gameplay_loop_via_bridge.py": "gameplay automation script",
    "tools/ensure_demo_raw_patty_spawner_via_bridge.py": "raw patty spawner repair script",
    "tools/verify_demo_map_content_via_bridge.py": "demo map content validation script",
    "tools/verify_demo_content_design_via_bridge.py": "demo content design validation script",
    "tools/verify_demo_menu_quality_via_bridge.py": "demo menu quality validation script",
    "tools/verify_cleanup_recovery_via_bridge.py": "cleanup recovery validation script",
    "tools/verify_salad_cutting_assets_via_bridge.py": "salad cutting asset validation script",
    "tools/fix_salad_cutting_assets_via_bridge.py": "salad cutting asset repair script",
    "tools/ensure_demo_raw_meat_spawner_via_bridge.py": "raw meat spawner repair script",
    "tools/ensure_salad_dressing_assets_via_bridge.py": "salad dressing asset/spawner repair script",
    "tools/verify_delivery_readiness.py": "delivery readiness script",
    ".github/workflows/maintenance.yml": "maintenance CI workflow",
    "tools/tests/test_delivery_readiness.py": "delivery readiness regression tests",
    "tools/verify_asset_organization.py": "asset organization audit script",
    "tools/migrate_asset_organization_via_editor.py": "staged asset migration script",
    "tools/verify_asset_migration_report.py": "asset migration dry-run report verifier",
    "tools/audit_asset_migration_state_via_editor.py": "asset migration state audit script",
    "VRKitchen_ASSET_ORGANIZATION.md": "asset organization guide",
    "VRKitchen/VRKitchen_ASSET_ORGANIZATION.md": "project asset organization guide",
    "VRKitchen_ASSET_MIGRATION_PLAN.md": "asset migration plan",
    "VRKitchen/VRKitchen_ASSET_MIGRATION_PLAN.md": "project asset migration plan",
}

BANNED_TRACKED_PREFIXES = (
    "Content/",
    "VRKitchen/Content/",
    "Binaries/",
    "VRKitchen/Binaries/",
    "Intermediate/",
    "VRKitchen/Intermediate/",
    "Saved/",
    "VRKitchen/Saved/",
    "DerivedDataCache/",
    "VRKitchen/DerivedDataCache/",
)

BANNED_TRACKED_SUFFIXES = (
    ".uasset",
    ".umap",
    ".ubulk",
    ".uexp",
    ".fbx",
    ".zip",
    ".7z",
    ".rar",
    ".pdb",
    ".exe",
)

REQUIRED_GITIGNORE_PATTERNS = (
    "VRKitchen/Content/",
    "*.uasset",
    "*.umap",
    "VRKitchen/Binaries/",
    "VRKitchen/Intermediate/",
    "VRKitchen/Saved/",
    "VRKitchen/DerivedDataCache/",
)

FULL_PROJECT_EXCLUDE_DIRS = (
    "Binaries",
    "Intermediate",
    "Saved",
    "DerivedDataCache",
)


@dataclass
class Check:
    level: str
    message: str


def resolve_existing_default(candidate: Path, fallback: Path, marker: str) -> Path:
    if (candidate / marker).exists():
        return candidate
    if (fallback / marker).exists():
        return fallback
    return candidate


def resolve_full_project_default(candidate: Path, fallback: Path) -> Path:
    marker = Path("Content") / "_Project" / "Maps" / "VRKitchen_Demo.umap"
    if (candidate / marker).exists():
        return candidate
    if (fallback / marker).exists():
        return fallback
    return candidate


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def add_result(results: list[Check], level: str, message: str) -> None:
    results.append(Check(level, message))


def require_path(results: list[Check], root: Path, relative_path: str, label: str) -> None:
    target = root / relative_path
    if target.exists():
        add_result(results, "PASS", f"{label}: {relative_path}")
    else:
        add_result(results, "FAIL", f"Missing {label}: {relative_path}")


def git_ls_files(repo_root: Path, results: list[Check]) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        add_result(results, "WARN", f"Could not query git tracked files: {exc}")
        return []

    return [item for item in completed.stdout.split("\0") if item]


def git_status(repo_root: Path, results: list[Check]) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--short"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        add_result(results, "WARN", f"Could not query git status: {exc}")
        return ""

    return completed.stdout.strip()


def check_full_project(full_project_root: Path, results: list[Check]) -> None:
    add_result(results, "INFO", f"Full project root: {full_project_root}")
    if not full_project_root.exists():
        add_result(results, "FAIL", "Full project root does not exist")
        return

    for relative_path, label in REQUIRED_FULL_PROJECT_ITEMS.items():
        require_path(results, full_project_root, relative_path, label)

    engine_config = full_project_root / "Config" / "DefaultEngine.ini"
    game_config = full_project_root / "Config" / "DefaultGame.ini"
    if engine_config.exists():
        text = read_text(engine_config)
        if "EditorStartupMap=/Game/_Project/Maps/VRKitchen_Demo.VRKitchen_Demo" in text:
            add_result(results, "PASS", "EditorStartupMap points to VRKitchen_Demo")
        else:
            add_result(results, "FAIL", "EditorStartupMap is not VRKitchen_Demo")

        if "GameDefaultMap=/Game/_Project/Maps/VRKitchen_Demo.VRKitchen_Demo" in text:
            add_result(results, "PASS", "GameDefaultMap points to VRKitchen_Demo")
        else:
            add_result(results, "FAIL", "GameDefaultMap is not VRKitchen_Demo")

    if game_config.exists():
        text = read_text(game_config)
        if DEMO_MAP_PATH in text:
            add_result(results, "PASS", "VRKitchen_Demo is listed for cooking")
        else:
            add_result(results, "FAIL", "VRKitchen_Demo is not listed in MapsToCook")

    for directory in FULL_PROJECT_EXCLUDE_DIRS:
        if (full_project_root / directory).exists():
            add_result(results, "WARN", f"Exclude from netdisk package if present: {directory}/")


def check_code_repo(code_repo_root: Path, require_clean_git: bool, results: list[Check]) -> None:
    add_result(results, "INFO", f"Code-only repository root: {code_repo_root}")
    if not code_repo_root.exists():
        add_result(results, "FAIL", "Code-only repository root does not exist")
        return

    for relative_path, label in REQUIRED_CODE_REPO_ITEMS.items():
        require_path(results, code_repo_root, relative_path, label)

    gitignore = code_repo_root / ".gitignore"
    if gitignore.exists():
        text = read_text(gitignore)
        for pattern in REQUIRED_GITIGNORE_PATTERNS:
            if pattern in text:
                add_result(results, "PASS", f".gitignore contains {pattern}")
            else:
                add_result(results, "FAIL", f".gitignore missing {pattern}")

    tracked_files = git_ls_files(code_repo_root, results)
    if tracked_files:
        banned = [
            path
            for path in tracked_files
            if path.startswith(BANNED_TRACKED_PREFIXES)
            or path.lower().endswith(BANNED_TRACKED_SUFFIXES)
        ]
        if banned:
            add_result(results, "FAIL", "Tracked binary/large asset paths: " + ", ".join(banned[:10]))
        else:
            add_result(results, "PASS", "No tracked Content, Unreal binary assets, or package artifacts")

        large = []
        for tracked in tracked_files:
            path = code_repo_root / tracked
            if path.exists() and path.is_file() and path.stat().st_size > MAX_TRACKED_FILE_BYTES:
                large.append(f"{tracked} ({path.stat().st_size} bytes)")

        if large:
            add_result(results, "FAIL", "Tracked files larger than 5 MB: " + ", ".join(large[:10]))
        else:
            add_result(results, "PASS", "No tracked files larger than 5 MB")

    status = git_status(code_repo_root, results)
    if require_clean_git:
        if status:
            add_result(results, "FAIL", "Code repo has uncommitted changes:\n" + status)
        else:
            add_result(results, "PASS", "Code repo working tree is clean")
    elif status:
        add_result(results, "WARN", "Code repo has uncommitted changes; commit before final GitHub delivery")


def check_delivery_docs(root: Path, relative_paths: tuple[str, ...], results: list[Check]) -> None:
    required_phrases = (
        "UE 5.5.4",
        "Windows PCVR",
        "SteamVR/OpenXR",
        "/Game/_Project/Maps/VRKitchen_Demo",
        "网盘",
        "GitHub",
        "未验证",
    )

    for relative_path in relative_paths:
        path = root / relative_path
        if not path.exists():
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            add_result(results, "FAIL", f"Delivery doc is not valid UTF-8: {relative_path}")
            continue

        add_result(results, "PASS", f"Delivery doc is UTF-8 readable: {relative_path}")
        for phrase in required_phrases:
            if phrase in text:
                add_result(results, "PASS", f"{relative_path} mentions {phrase}")
            else:
                add_result(results, "WARN", f"{relative_path} does not mention {phrase}")


def check_asset_docs(root: Path, relative_paths: tuple[str, ...], results: list[Check]) -> None:
    required_phrases = (
        "Content/_Project",
        "Content/_External",
        "Content/_Legacy",
        "Content/_Dev",
        "Fix Up Redirectors",
        "不要用文件管理器直接移动",
        "GitHub",
        "网盘",
    )

    for relative_path in relative_paths:
        path = root / relative_path
        if not path.exists():
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            add_result(results, "FAIL", f"Asset organization doc is not valid UTF-8: {relative_path}")
            continue

        add_result(results, "PASS", f"Asset organization doc is UTF-8 readable: {relative_path}")
        for phrase in required_phrases:
            if phrase in text:
                add_result(results, "PASS", f"{relative_path} mentions {phrase}")
            else:
                add_result(results, "WARN", f"{relative_path} does not mention {phrase}")


def check_migration_docs(root: Path, relative_paths: tuple[str, ...], results: list[Check]) -> None:
    required_phrases = (
        "Phase 1",
        "Phase 2",
        "Phase 3",
        "Phase 4",
        "Fix Up Redirectors",
        "Unreal Editor",
        "不直接搬资产",
        "verify_asset_migration_report.py",
        "--strict",
    )

    for relative_path in relative_paths:
        path = root / relative_path
        if not path.exists():
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            add_result(results, "FAIL", f"Asset migration plan is not valid UTF-8: {relative_path}")
            continue

        add_result(results, "PASS", f"Asset migration plan is UTF-8 readable: {relative_path}")
        for phrase in required_phrases:
            if phrase in text:
                add_result(results, "PASS", f"{relative_path} mentions {phrase}")
            else:
                add_result(results, "WARN", f"{relative_path} does not mention {phrase}")


def print_results(results: list[Check]) -> int:
    counts = {"INFO": 0, "PASS": 0, "WARN": 0, "FAIL": 0}
    for result in results:
        counts[result.level] = counts.get(result.level, 0) + 1
        print(f"[{result.level}] {result.message}")

    print()
    print(
        "Summary: "
        f"{counts['PASS']} pass, {counts['WARN']} warn, {counts['FAIL']} fail"
    )
    return 1 if counts["FAIL"] else 0


def parse_args() -> argparse.Namespace:
    script_root = Path(__file__).resolve().parent.parent
    home = Path.home()

    default_full_project = resolve_full_project_default(
        script_root / "VRKitchen",
        home / "Desktop" / "CrazyKitchen" / "VRKitchen",
    )
    default_code_repo = resolve_existing_default(
        script_root,
        home / "Desktop" / "VRKitchen_CodeOnly",
        ".git",
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-project-root",
        type=Path,
        default=default_full_project,
        help="Path to the full Unreal project root that contains Content.",
    )
    parser.add_argument(
        "--code-repo-root",
        type=Path,
        default=default_code_repo,
        help="Path to the code-only GitHub repository root.",
    )
    parser.add_argument(
        "--require-clean-git",
        action="store_true",
        help="Fail if the code-only repository has uncommitted changes.",
    )
    parser.add_argument(
        "--skip-full-project",
        action="store_true",
        help="Only validate the code-only repository; useful for CI and code checkouts without Content/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    full_project_root = args.full_project_root.expanduser().resolve()
    code_repo_root = args.code_repo_root.expanduser().resolve()

    results: list[Check] = []
    if not args.skip_full_project:
        check_full_project(full_project_root, results)
    check_code_repo(code_repo_root, args.require_clean_git, results)
    if not args.skip_full_project:
        check_delivery_docs(full_project_root, ("VRKitchen_DELIVERY.md",), results)
    check_delivery_docs(code_repo_root, ("VRKitchen_DELIVERY.md", "VRKitchen/VRKitchen_DELIVERY.md"), results)
    if not args.skip_full_project:
        check_asset_docs(full_project_root, ("VRKitchen_ASSET_ORGANIZATION.md",), results)
    check_asset_docs(code_repo_root, ("VRKitchen_ASSET_ORGANIZATION.md", "VRKitchen/VRKitchen_ASSET_ORGANIZATION.md"), results)
    if not args.skip_full_project:
        check_migration_docs(full_project_root, ("VRKitchen_ASSET_MIGRATION_PLAN.md",), results)
    check_migration_docs(code_repo_root, ("VRKitchen_ASSET_MIGRATION_PLAN.md", "VRKitchen/VRKitchen_ASSET_MIGRATION_PLAN.md"), results)

    return print_results(results)


if __name__ == "__main__":
    sys.exit(main())
