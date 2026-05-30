#!/usr/bin/env python3
"""Audit VRKitchen Content organization without moving assets.

The default mode is advisory: it reports legacy/root-level assets and naming
issues as warnings. Use --strict when the project is ready to enforce the final
layout after assets have been migrated inside Unreal Editor.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
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

TOP_LEVEL_CLASSIFICATION = {
    "Audio": ("project", "Content/_Project/Art/Audio or Content/_External/<Pack>/Audio", "phase-5", "medium", "Review whether the sounds are project-owned or imported."),
    "Blueprints": ("project", "Content/_Project/Gameplay", "phase-4", "high", "Contains active gameplay Blueprints; migrate only inside Unreal Editor."),
    "Characters": ("legacy", "Content/_Legacy/Characters", "phase-3", "medium", "Looks like template/mannequin content; confirm runtime references first."),
    "Collections": ("dev", "Content/_Dev/Collections", "phase-2", "low", "Editor organization data; safe to classify after reference review."),
    "Developers": ("dev", "Content/_Dev/Developers", "phase-2", "low", "Developer scratch content."),
    "Environment": ("project", "Content/_Project/Art/Environment or Content/_External/<Pack>/Environment", "phase-5", "medium", "Review source before deciding project vs external."),
    "FPWeapon": ("legacy", "Content/_Legacy/FPWeapon", "phase-3", "medium", "First-person template content."),
    "Fast_Food_Restaurant": ("external", "Content/_External/Marketplace/Fast_Food_Restaurant", "phase-3", "medium", "Third-party restaurant pack."),
    "LevelPrototyping": ("legacy", "Content/_Legacy/LevelPrototyping", "phase-3", "low", "Template prototyping meshes/materials."),
    "Lighting": ("project", "Content/_Project/Art/Lighting", "phase-5", "medium", "Scene lighting assets; verify map references."),
    "Maps": ("legacy", "Content/_Legacy/Maps or Content/_Dev/TestMaps", "phase-3", "medium", "Demo map is already under _Project; older maps should be reviewed."),
    "Materials": ("project", "Content/_Project/Art/Materials or Content/_External/<Pack>/Materials", "phase-5", "medium", "Review material ownership."),
    "Models": ("project", "Content/_Project/Art/Props or Content/_External/<Pack>/Models", "phase-5", "medium", "Review mesh ownership."),
    "SM_PanStove_01.fbm": ("external", "Content/_External/TemplateSource/SM_PanStove_01.fbm", "phase-3", "low", "FBX sidecar import folder."),
    "SM_WallMonitor_01.fbm": ("external", "Content/_External/TemplateSource/SM_WallMonitor_01.fbm", "phase-3", "low", "FBX sidecar import folder."),
    "SM_WallMonitor_01_fbm": ("external", "Content/_External/TemplateSource/SM_WallMonitor_01_fbm", "phase-3", "low", "FBX sidecar import folder."),
    "StarterContent": ("legacy", "Content/_Legacy/StarterContent", "phase-3", "low", "UE StarterContent."),
    "UI": ("project", "Content/_Project/UI", "phase-4", "medium", "Project UI should move under _Project/UI."),
    "VRSpectator": ("legacy", "Content/_Legacy/VRSpectator", "phase-3", "medium", "Template spectator content."),
    "VRTemplate": ("legacy", "Content/_Legacy/VRTemplate", "phase-3", "high", "VR Template may still have live references; migrate carefully."),
    "food_select": ("project", "Content/_Project/Gameplay/Food", "phase-4", "medium", "Project food selection assets."),
    "food_test": ("dev", "Content/_Dev/Prototypes/food_test", "phase-2", "low", "Prototype/test food assets."),
}

ROOT_ASSET_CLASSIFICATION = {
    "BP_Pan.uasset": ("project", "Content/_Project/Gameplay/Cooking", "phase-4", "high", "Active pan Blueprint; migrate only inside Unreal Editor."),
    "BP_PickFood.uasset": ("project", "Content/_Project/Gameplay/Food", "phase-4", "high", "Active food pickup/spawn Blueprint."),
    "BP_Plate.uasset": ("project", "Content/_Project/Gameplay/Delivery", "phase-4", "high", "Active plate/stacking Blueprint."),
    "BP_Stove.uasset": ("project", "Content/_Project/Gameplay/Cooking", "phase-4", "high", "Active stove Blueprint."),
    "BP_Tomato.uasset": ("project", "Content/_Project/Gameplay/Food", "phase-4", "medium", "Food Blueprint."),
    "Kitchen_Demo_Map.umap": ("legacy", "Content/_Legacy/Maps", "phase-3", "medium", "Old map; current delivery map is VRKitchen_Demo."),
    "Kitchen_Demo_Map_BuiltData.uasset": ("legacy", "Content/_Legacy/Maps", "phase-3", "medium", "Built data for old map."),
    "SM_PanStove_01.fbx": ("external", "Content/_External/TemplateSource/PanStove", "phase-3", "low", "Original FBX source file."),
    "texture_pbr_20250901.uasset": ("external", "Content/_External/TemplateSource/PanStove/Textures", "phase-3", "low", "Imported texture source."),
    "texture_pbr_20250901_metallic.uasset": ("external", "Content/_External/TemplateSource/PanStove/Textures", "phase-3", "low", "Imported texture source."),
    "texture_pbr_20250901_normal.uasset": ("external", "Content/_External/TemplateSource/PanStove/Textures", "phase-3", "low", "Imported texture source."),
    "texture_pbr_20250901_roughness.uasset": ("external", "Content/_External/TemplateSource/PanStove/Textures", "phase-3", "low", "Imported texture source."),
}

PHASE_LABELS = {
    "phase-1": "Create missing folder structure and keep audit-only mode.",
    "phase-2": "Move dev-only prototypes after confirming they are not cooked.",
    "phase-3": "Move template/external/legacy folders with redirector fix-up.",
    "phase-4": "Move active gameplay assets one module at a time.",
    "phase-5": "Move art/audio/UI polish assets after ownership review.",
    "phase-6": "Enable --strict and fail the build on organization drift.",
}

PHASE_ORDER = tuple(PHASE_LABELS)
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
CATEGORY_ORDER = {"dev": 0, "external": 1, "legacy": 2, "project": 3, "review": 4, "rename-review": 5}

MIGRATION_SCRIPT_PHASES = {
    "phase-2": ("phase-2-dev-folders", "phase-2-prototypes"),
    "phase-3": ("phase-3-external", "phase-3-legacy", "phase-3-root-legacy", "phase-3-root-external"),
    "phase-4": ("phase-4-root-gameplay", "phase-4-food-blueprints", "phase-4-interaction-blueprints", "phase-4-legacy-duplicates"),
}

VALIDATION_GATE_COMMANDS = (
    "VRKitchenEditor Win64 Development C++ build",
    "CompileAllBlueprints",
    "DataValidation",
    "tools/verify_demo_gameplay_loop_via_bridge.py",
    "Win64 Development BuildCookRun package smoke",
    "tools/verify_delivery_readiness.py",
)


@dataclass
class Check:
    level: str
    message: str


@dataclass
class Finding:
    kind: str
    path: str
    category: str
    destination: str
    phase: str
    risk: str
    note: str


def add(results: list[Check], level: str, message: str) -> None:
    results.append(Check(level, message))


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def first_items(items: list[str], limit: int = 20) -> str:
    visible = items[:limit]
    suffix = "" if len(items) <= limit else f" ... (+{len(items) - limit} more)"
    return ", ".join(visible) + suffix


def phase_sort_key(phase: str) -> tuple[int, str]:
    try:
        return (PHASE_ORDER.index(phase), phase)
    except ValueError:
        return (len(PHASE_ORDER), phase)


def finding_sort_key(finding: Finding) -> tuple[tuple[int, str], int, int, str, str]:
    return (
        phase_sort_key(finding.phase),
        RISK_ORDER.get(finding.risk, 99),
        CATEGORY_ORDER.get(finding.category, 99),
        finding.kind,
        finding.path,
    )


def sorted_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=finding_sort_key)


def markdown_cell(value: str) -> str:
    return value.replace("|", "/").replace("\n", " ")


def append_counter_table(lines: list[str], title: str, counts: Counter[str], preferred_order: tuple[str, ...] = ()) -> None:
    lines.extend(["", f"## {title}", "", "| Value | Count |", "| --- | ---: |"])
    ordered_keys = [key for key in preferred_order if key in counts]
    ordered_keys.extend(sorted(key for key in counts if key not in ordered_keys))
    if not ordered_keys:
        lines.append("| none | 0 |")
        return
    for key in ordered_keys:
        lines.append(f"| `{key}` | {counts[key]} |")


def append_findings_table(lines: list[str], findings: list[Finding], empty_message: str) -> None:
    if not findings:
        lines.append(empty_message)
        return
    lines.extend([
        "| Kind | Path | Category | Suggested Destination | Phase | Risk | Note |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    for finding in sorted_findings(findings):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(finding.kind),
                    f"`{markdown_cell(finding.path)}`",
                    markdown_cell(finding.category),
                    f"`{markdown_cell(finding.destination)}`",
                    markdown_cell(finding.phase),
                    markdown_cell(finding.risk),
                    markdown_cell(finding.note),
                ]
            )
            + " |"
        )


def powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_dry_run_command(full_project_root: Path, script_phases: tuple[str, ...], report_name: str) -> list[str]:
    project_file = full_project_root / "VRKitchen.uproject"
    script_path = full_project_root.parent / "tools" / "migrate_asset_organization_via_editor.py"
    report_path = full_project_root.parent / report_name
    return [
        f"$env:VRKITCHEN_ASSET_MIGRATION_PHASES={powershell_quote('phase-1,' + ','.join(script_phases))}",
        "$env:VRKITCHEN_ASSET_MIGRATION_DRY_RUN='1'",
        f"$env:VRKITCHEN_ASSET_MIGRATION_REPORT={powershell_quote(str(report_path))}",
        f"& 'D:\\Program Files (x86)\\Epic Games\\UE_5.5\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe' {powershell_quote(str(project_file))} -run=pythonscript -script={powershell_quote(str(script_path))} -unattended -nop4 -nosplash -NullRHI",
    ]


def recommend_next_findings(findings: list[Finding]) -> list[Finding]:
    for phase in PHASE_ORDER:
        candidates = [finding for finding in findings if finding.phase == phase and finding.risk == "low"]
        if candidates:
            return sorted_findings(candidates)
    for phase in PHASE_ORDER:
        candidates = [finding for finding in findings if finding.phase == phase]
        if candidates:
            return sorted_findings(candidates)
    return []


def classification_for_top_level(name: str) -> tuple[str, str, str, str, str]:
    if name in TOP_LEVEL_CLASSIFICATION:
        return TOP_LEVEL_CLASSIFICATION[name]
    if name in LEGACY_CANDIDATE_DIRS:
        return ("legacy", "Content/_Legacy", "phase-3", "medium", "Template or legacy folder.")
    if name in EXTERNAL_CANDIDATE_DIRS:
        return ("external", "Content/_External", "phase-3", "medium", "Imported or third-party folder.")
    if name in DEV_CANDIDATE_DIRS:
        return ("dev", "Content/_Dev", "phase-2", "low", "Developer/test folder.")
    return ("review", "Content/_Project or Content/_External after reference review", "phase-5", "medium", "Needs ownership/reference review.")


def classification_for_root_asset(name: str) -> tuple[str, str, str, str, str]:
    if name in ROOT_ASSET_CLASSIFICATION:
        return ROOT_ASSET_CLASSIFICATION[name]
    return ("review", "Content/_Project or Content/_External after reference review", "phase-5", "medium", "Root-level asset needs ownership/reference review.")


def has_good_asset_name(path: Path) -> bool:
    stem = path.stem
    suffix = path.suffix.lower()
    if suffix == ".umap":
        return stem in MAP_NAME_EXCEPTIONS or stem.startswith(("MAP_", "L_"))
    if suffix in {".ubulk", ".uexp"}:
        return True
    return stem.startswith(ALLOWED_ASSET_PREFIXES)


def audit_content(full_project_root: Path, strict: bool) -> tuple[list[Check], list[Finding]]:
    results: list[Check] = []
    findings: list[Finding] = []
    content_root = full_project_root / "Content"
    add(results, "INFO", f"Full project root: {full_project_root}")

    if not content_root.exists():
        add(results, "FAIL", "Missing Content directory")
        return results, findings

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
            category, destination, phase, risk, note = classification_for_top_level(name)
            findings.append(Finding("top-level-folder", f"Content/{name}", category, destination, phase, risk, note))
            add(results, "WARN", f"Top-level folder needs classification: Content/{name} -> {destination} ({phase}, risk={risk})")
    else:
        add(results, "PASS", "Only approved top-level Content folders are present")

    root_asset_files = sorted(
        relpath(item, content_root)
        for item in content_root.iterdir()
        if item.is_file() and item.suffix.lower() in ASSET_SUFFIXES
    )
    if root_asset_files:
        for asset_path in root_asset_files:
            category, destination, phase, risk, note = classification_for_root_asset(asset_path)
            findings.append(Finding("root-asset", f"Content/{asset_path}", category, destination, phase, risk, note))
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
        for asset_path in bad_names:
            findings.append(Finding("naming", f"Content/{asset_path}", "rename-review", "Rename inside its final folder", "phase-6", "medium", "Rename only after migration and redirector fix-up."))
        add(results, "WARN", "Assets that do not follow the naming prefix guide: " + first_items(bad_names))
    else:
        add(results, "PASS", "Scanned asset filenames follow the naming prefix guide")

    if findings:
        category_counts = Counter(finding.category for finding in findings)
        phase_counts = Counter(finding.phase for finding in findings)
        risk_counts = Counter(finding.risk for finding in findings)
        add(results, "INFO", "Finding categories: " + ", ".join(f"{key}={value}" for key, value in sorted(category_counts.items())))
        add(results, "INFO", "Finding phases: " + ", ".join(f"{key}={value}" for key, value in sorted(phase_counts.items())))
        add(results, "INFO", "Finding risks: " + ", ".join(f"{key}={value}" for key, value in sorted(risk_counts.items())))

    if strict:
        for result in results:
            if result.level == "WARN":
                result.level = "FAIL"

    return results, findings


def build_markdown_report(full_project_root: Path, findings: list[Finding]) -> str:
    category_counts = Counter(finding.category for finding in findings)
    phase_counts = Counter(finding.phase for finding in findings)
    risk_counts = Counter(finding.risk for finding in findings)
    recommended_findings = recommend_next_findings(findings)
    recommended_phase = recommended_findings[0].phase if recommended_findings else ""
    script_phases = MIGRATION_SCRIPT_PHASES.get(recommended_phase, ())

    lines = [
        "# VRKitchen Asset Organization Audit",
        "",
        f"- Full project root: `{full_project_root}`",
        f"- Findings: {len(findings)}",
        "- This report is read-only. Move assets only inside Unreal Editor and then run Fix Up Redirectors.",
        "- GitHub remains code/config/docs/tools only; full Content assets stay in the netdisk project package.",
        "",
        "## Current Summary",
        "",
        f"- Phase findings: {', '.join(f'{key}={value}' for key, value in sorted(phase_counts.items(), key=lambda item: phase_sort_key(item[0])) ) or 'none'}",
        f"- Risk findings: {', '.join(f'{key}={value}' for key, value in sorted(risk_counts.items(), key=lambda item: RISK_ORDER.get(item[0], 99)) ) or 'none'}",
        f"- Category findings: {', '.join(f'{key}={value}' for key, value in sorted(category_counts.items(), key=lambda item: CATEGORY_ORDER.get(item[0], 99)) ) or 'none'}",
        "",
    ]

    append_counter_table(lines, "Findings By Phase", phase_counts, PHASE_ORDER)
    append_counter_table(lines, "Findings By Risk", risk_counts, ("low", "medium", "high"))
    append_counter_table(lines, "Findings By Category", category_counts, ("dev", "external", "legacy", "project", "review", "rename-review"))

    lines.extend(["", "## Recommended Next Batch", ""])
    if recommended_findings:
        lines.append(f"- Recommended audit phase: `{recommended_phase}`")
        lines.append("- Start with the rows below because they are the earliest low-risk findings currently visible.")
        lines.append("- Keep this as a dry-run unless you are ready to open Unreal Editor, fix redirectors, and run the full validation gate.")
        lines.append("")
        append_findings_table(lines, recommended_findings, "No recommended findings.")
        if script_phases:
            lines.extend(["", "Dry-run command:", "", "```powershell"])
            lines.extend(build_dry_run_command(full_project_root, script_phases, f"VRKitchen_ASSET_MIGRATION_DRYRUN_{recommended_phase}.json"))
            lines.extend(["```", ""])
        else:
            lines.append("")
            lines.append("No migration script phase is mapped for this audit phase yet; create a dedicated small-batch migration before moving assets.")
    else:
        lines.append("No findings remain. This is the point where `--strict` can become a final gate.")

    lines.extend([
        "",
        "## Validation Gate After Any Real Move",
        "",
    ])
    for command in VALIDATION_GATE_COMMANDS:
        lines.append(f"- {command}")

    lines.extend([
        "",
        "## Migration Phases",
        "",
    ])
    for phase, description in PHASE_LABELS.items():
        lines.append(f"- `{phase}`: {description}")

    lines.extend([
        "",
        "## Findings",
        "",
    ])

    append_findings_table(lines, findings, "No findings.")

    lines.extend([
        "",
        "## Safe Migration Rule",
        "",
        "Do not move `.uasset` or `.umap` files in the file explorer. Use Unreal Editor AssetTools or Content Browser moves, fix redirectors, then rerun build, Blueprint compile, DataValidation, gameplay automation, and packaging smoke tests.",
        "",
    ])
    return "\n".join(lines)


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
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional Markdown report path for the current organization findings.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    full_project_root = args.full_project_root.expanduser().resolve()
    results, findings = audit_content(full_project_root, args.strict)
    if args.report:
        report_path = args.report.expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_report(full_project_root, findings), encoding="utf-8")
        add(results, "INFO", f"Wrote Markdown report: {report_path}")
    return print_results(results)


if __name__ == "__main__":
    sys.exit(main())
