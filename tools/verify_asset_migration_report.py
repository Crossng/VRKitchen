#!/usr/bin/env python3
"""Verify VRKitchen asset migration JSON reports.

The Unreal migration command can run in dry-run mode before any real Content
move. This verifier makes that dry-run auditable: a dry-run report must contain
only planned or skipped work, no errors, the expected migration phases, and the
expected move records for each selected phase.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_EXPECTED_PHASES = (
    "phase-1",
    "phase-2-dev-folders",
    "phase-2-prototypes",
)

DRY_RUN_ALLOWED_STATUSES = {"plan", "skip"}

PHASE_GROUP_ALIASES = {
    "phase-2": (
        "phase-2-dev-folders",
        "phase-2-prototypes",
    ),
    "phase-3": (
        "phase-3-external",
        "phase-3-legacy",
        "phase-3-root-legacy",
        "phase-3-root-external",
    ),
    "phase-4": (
        "phase-4-root-gameplay",
        "phase-4-food-blueprints",
        "phase-4-interaction-blueprints",
        "phase-4-legacy-duplicates",
    ),
}

EXPECTED_MOVES_BY_PHASE = {
    "phase-2-dev-folders": (
        ("move-directory", "/Game/Collections", "/Game/_Dev/Collections"),
        ("move-directory", "/Game/Developers", "/Game/_Dev/Developers"),
    ),
    "phase-2-prototypes": (
        ("move-directory", "/Game/food_test", "/Game/_Dev/Prototypes/food_test"),
    ),
    "phase-3-external": (
        ("move-directory", "/Game/Fast_Food_Restaurant", "/Game/_External/Marketplace/Fast_Food_Restaurant"),
        ("move-directory", "/Game/SM_PanStove_01.fbm", "/Game/_External/TemplateSource/PanStove/SM_PanStove_01.fbm"),
        ("move-directory", "/Game/SM_WallMonitor_01.fbm", "/Game/_External/TemplateSource/WallMonitor/SM_WallMonitor_01.fbm"),
        ("move-directory", "/Game/SM_WallMonitor_01_fbm", "/Game/_External/TemplateSource/WallMonitor/SM_WallMonitor_01_fbm"),
    ),
    "phase-3-legacy": (
        ("move-directory", "/Game/Characters", "/Game/_Legacy/Characters"),
        ("move-directory", "/Game/FPWeapon", "/Game/_Legacy/FPWeapon"),
        ("move-directory", "/Game/LevelPrototyping", "/Game/_Legacy/LevelPrototyping"),
        ("move-directory", "/Game/Maps", "/Game/_Legacy/Maps/ImportedMaps"),
        ("move-directory", "/Game/StarterContent", "/Game/_Legacy/StarterContent"),
        ("move-directory", "/Game/VRSpectator", "/Game/_Legacy/VRSpectator"),
    ),
    "phase-3-root-legacy": (
        ("move-asset", "/Game/Kitchen_Demo_Map", "/Game/_Legacy/Maps/Kitchen_Demo_Map"),
        ("move-asset", "/Game/Kitchen_Demo_Map_BuiltData", "/Game/_Legacy/Maps/Kitchen_Demo_Map_BuiltData"),
    ),
    "phase-3-root-external": (
        ("move-asset", "/Game/SM_PanStove_01", "/Game/_External/TemplateSource/PanStove/SM_PanStove_01"),
        ("move-asset", "/Game/texture_pbr_20250901", "/Game/_External/TemplateSource/PanStove/Textures/texture_pbr_20250901"),
        ("move-asset", "/Game/texture_pbr_20250901_metallic", "/Game/_External/TemplateSource/PanStove/Textures/texture_pbr_20250901_metallic"),
        ("move-asset", "/Game/texture_pbr_20250901_normal", "/Game/_External/TemplateSource/PanStove/Textures/texture_pbr_20250901_normal"),
        ("move-asset", "/Game/texture_pbr_20250901_roughness", "/Game/_External/TemplateSource/PanStove/Textures/texture_pbr_20250901_roughness"),
    ),
    "phase-4-root-gameplay": (
        ("move-asset", "/Game/BP_Pan", "/Game/_Project/Gameplay/Cooking/BP_Pan"),
        ("move-asset", "/Game/BP_Stove", "/Game/_Project/Gameplay/Cooking/BP_Stove"),
        ("move-asset", "/Game/BP_PickFood", "/Game/_Project/Gameplay/Food/BP_PickFood"),
        ("move-asset", "/Game/BP_Tomato", "/Game/_Project/Gameplay/Food/BP_Tomato"),
        ("move-asset", "/Game/BP_Plate", "/Game/_Project/Gameplay/Delivery/BP_Plate"),
    ),
    "phase-4-food-blueprints": (
        ("move-asset", "/Game/Blueprints/BP_BottomBun", "/Game/_Project/Gameplay/Food/BP_BottomBun"),
        ("move-asset", "/Game/Blueprints/BP_ChoppedLettuce", "/Game/_Project/Gameplay/Food/BP_ChoppedLettuce"),
        ("move-asset", "/Game/Blueprints/BP_ChoppedTomato", "/Game/_Project/Gameplay/Food/BP_ChoppedTomato"),
        ("move-asset", "/Game/Blueprints/BP_FoodSpawner", "/Game/_Project/Gameplay/Food/BP_FoodSpawner"),
        ("move-asset", "/Game/Blueprints/BP_Lettuce", "/Game/_Project/Gameplay/Food/BP_Lettuce"),
        ("move-asset", "/Game/Blueprints/BP_Meat", "/Game/_Project/Gameplay/Food/BP_Meat"),
        ("move-asset", "/Game/Blueprints/BP_Patty", "/Game/_Project/Gameplay/Food/BP_Patty"),
        ("move-asset", "/Game/Blueprints/BP_TopBun", "/Game/_Project/Gameplay/Food/BP_TopBun"),
        ("move-asset", "/Game/Blueprints/BP_row_meat", "/Game/_Project/Gameplay/Food/BP_RowMeat"),
    ),
    "phase-4-interaction-blueprints": (
        ("move-asset", "/Game/Blueprints/BP_Bin", "/Game/_Project/Gameplay/Interaction/BP_Bin"),
        ("move-asset", "/Game/Blueprints/BP_CuttingBoard", "/Game/_Project/Gameplay/Interaction/BP_CuttingBoard"),
        ("move-asset", "/Game/Blueprints/BP_Knife", "/Game/_Project/Gameplay/Interaction/BP_Knife"),
        ("move-asset", "/Game/Blueprints/BP_Sponge", "/Game/_Project/Gameplay/Interaction/BP_Sponge"),
    ),
    "phase-4-legacy-duplicates": (
        ("move-asset", "/Game/Blueprints/BP_OrderTablet", "/Game/_Legacy/Blueprints/BP_OrderTablet"),
        ("move-asset", "/Game/Blueprints/ST_Recipe", "/Game/_Legacy/Blueprints/ST_Recipe"),
        ("move-asset", "/Game/Blueprints/WBP_Orderscreen", "/Game/_Legacy/Blueprints/WBP_Orderscreen"),
    ),
}


@dataclass
class Check:
    level: str
    message: str


def add_result(results: list[Check], level: str, message: str) -> None:
    results.append(Check(level, message))


def parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def expand_phase_aliases(phases: tuple[str, ...]) -> tuple[str, ...]:
    expanded: list[str] = []
    for phase in phases:
        if phase in PHASE_GROUP_ALIASES:
            expanded.extend(PHASE_GROUP_ALIASES[phase])
        else:
            expanded.append(phase)
    return tuple(dict.fromkeys(expanded))


def load_report(path: Path, results: list[Check]) -> dict[str, Any] | None:
    if not path.exists():
        add_result(results, "FAIL", f"Report does not exist: {path}")
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        add_result(results, "FAIL", f"Report is not valid UTF-8: {exc}")
        return None
    except json.JSONDecodeError as exc:
        add_result(results, "FAIL", f"Report is not valid JSON: {exc}")
        return None

    if not isinstance(data, dict):
        add_result(results, "FAIL", "Report root must be a JSON object")
        return None

    add_result(results, "PASS", f"Loaded migration report: {path}")
    return data


def result_value(record: Any, key: str) -> str:
    if not isinstance(record, dict):
        return ""
    value = record.get(key, "")
    return value if isinstance(value, str) else str(value)


def matching_record(records: list[Any], action: str, source: str, target: str) -> dict[str, Any] | None:
    for record in records:
        if not isinstance(record, dict):
            continue
        if (
            result_value(record, "action") == action
            and result_value(record, "source") == source
            and result_value(record, "target") == target
        ):
            return record
    return None


def verify_expected_phases(data: dict[str, Any], expected_phases: tuple[str, ...], results: list[Check]) -> None:
    phases_value = data.get("phases", [])
    if not isinstance(phases_value, list) or not all(isinstance(item, str) for item in phases_value):
        add_result(results, "FAIL", "Report phases must be a string array")
        return

    actual_phases = tuple(phases_value)
    if not expected_phases:
        add_result(results, "INFO", "No expected phase list was provided")
        return

    missing = [phase for phase in expected_phases if phase not in actual_phases]
    unexpected = [phase for phase in actual_phases if phase not in expected_phases]
    if missing:
        add_result(results, "FAIL", "Report is missing expected phases: " + ", ".join(missing))
    else:
        add_result(results, "PASS", "Report contains expected phases: " + ", ".join(expected_phases))

    if unexpected:
        add_result(results, "FAIL", "Report contains unexpected phases: " + ", ".join(unexpected))

    if actual_phases == expected_phases:
        add_result(results, "PASS", "Report phase order matches the expected dry-run gate")
    elif not missing and not unexpected:
        add_result(results, "WARN", "Report phases match as a set but not in the expected order")


def verify_errors(data: dict[str, Any], results: list[Check]) -> None:
    errors = data.get("errors", [])
    if not isinstance(errors, list):
        add_result(results, "FAIL", "Report errors field must be an array")
        return

    if errors:
        add_result(results, "FAIL", "Migration report contains errors: " + "; ".join(str(item) for item in errors))
    else:
        add_result(results, "PASS", "Migration report contains no errors")


def verify_dry_run(data: dict[str, Any], require_dry_run: bool, results: list[Check]) -> None:
    dry_run = data.get("dry_run")
    if dry_run is True:
        add_result(results, "PASS", "Report declares dry_run=true")
    elif require_dry_run:
        add_result(results, "FAIL", f"Expected dry_run=true, got {dry_run!r}")
    else:
        add_result(results, "WARN", f"Report is not a dry-run report: dry_run={dry_run!r}")


def verify_records(data: dict[str, Any], require_dry_run: bool, expected_phases: tuple[str, ...], require_expected_moves: bool, results: list[Check]) -> None:
    records = data.get("results", [])
    if not isinstance(records, list):
        add_result(results, "FAIL", "Report results field must be an array")
        return

    add_result(results, "PASS", f"Report contains {len(records)} result records")
    status_counts = Counter(result_value(record, "status") for record in records)
    action_counts = Counter(result_value(record, "action") for record in records)
    add_result(results, "INFO", "Result statuses: " + ", ".join(f"{key}={value}" for key, value in sorted(status_counts.items())))
    add_result(results, "INFO", "Result actions: " + ", ".join(f"{key}={value}" for key, value in sorted(action_counts.items())))

    if require_dry_run:
        invalid = [
            record
            for record in records
            if result_value(record, "status") not in DRY_RUN_ALLOWED_STATUSES
        ]
        if invalid:
            sample = "; ".join(
                f"{result_value(record, 'status')} {result_value(record, 'action')} {result_value(record, 'source')}"
                for record in invalid[:5]
            )
            add_result(results, "FAIL", "Dry-run report contains non-plan/non-skip records: " + sample)
        else:
            add_result(results, "PASS", "Dry-run report contains only plan/skip records")

    if not require_expected_moves:
        add_result(results, "INFO", "Expected move checks are disabled")
        return

    checked_phases = [phase for phase in expected_phases if phase in EXPECTED_MOVES_BY_PHASE]
    if checked_phases:
        add_result(results, "INFO", "Checking expected move records for phases: " + ", ".join(checked_phases))
    else:
        add_result(results, "INFO", "No expected move records are registered for the selected phases")

    for phase in expected_phases:
        for action, source, target in EXPECTED_MOVES_BY_PHASE.get(phase, ()):
            record = matching_record(records, action, source, target)
            if record:
                add_result(
                    results,
                    "PASS",
                    f"Expected {phase} {action} is represented as {result_value(record, 'status')}: {source} -> {target}",
                )
            else:
                add_result(results, "FAIL", f"Missing expected {phase} {action}: {source} -> {target}")


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        required=True,
        type=Path,
        help="Path to the JSON report written by migrate_asset_organization_via_editor.py.",
    )
    parser.add_argument(
        "--expected-phases",
        default=",".join(DEFAULT_EXPECTED_PHASES),
        help=(
            "Comma-separated migration phases expected in the report. "
            "Group aliases phase-2, phase-3, and phase-4 expand to their concrete script phases. "
            "Use an empty string to skip phase checks."
        ),
    )
    parser.add_argument(
        "--allow-applied-report",
        action="store_true",
        help="Allow dry_run=false reports. By default this verifier is a dry-run safety gate.",
    )
    parser.add_argument(
        "--skip-expected-moves",
        action="store_true",
        help="Skip checks for the known phase-2 move entries.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: list[Check] = []
    report_path = args.report.expanduser().resolve()
    expected_phases = expand_phase_aliases(parse_csv(args.expected_phases))
    require_dry_run = not args.allow_applied_report

    data = load_report(report_path, results)
    if data is not None:
        verify_dry_run(data, require_dry_run, results)
        verify_expected_phases(data, expected_phases, results)
        verify_errors(data, results)
        verify_records(data, require_dry_run, expected_phases, not args.skip_expected_moves, results)

    return print_results(results)


if __name__ == "__main__":
    sys.exit(main())
