"""Audit the current state of a VRKitchen asset migration report.

This script is intentionally read-only. It is useful after a migration command
partially succeeds: Unreal may create redirectors at source paths while the real
asset lands at the target path. The report identifies which entries are clean,
which are still pending, and which need manual Fix Up Redirectors in the editor.

Environment variables:
  VRKITCHEN_ASSET_MIGRATION_REPORT   JSON report written by
                                     migrate_asset_organization_via_editor.py.
  VRKITCHEN_ASSET_MIGRATION_AUDIT    Optional output JSON path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import unreal


REPORT_ENV = "VRKITCHEN_ASSET_MIGRATION_REPORT"
AUDIT_ENV = "VRKITCHEN_ASSET_MIGRATION_AUDIT"
REDIRECTOR_CLASS = "/Script/CoreUObject.ObjectRedirector"


def write_report(path: str, payload: dict) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def asset_object_path(asset_path: str) -> str:
    if not asset_path.startswith("/"):
        return asset_path
    if "." in asset_path.rsplit("/", 1)[-1]:
        return asset_path
    name = asset_path.rsplit("/", 1)[-1]
    return f"{asset_path}.{name}"


def soft_path_to_string(value) -> str:
    if hasattr(value, "to_tuple"):
        tuple_value = value.to_tuple()
        if tuple_value:
            return str(tuple_value[0])
    text = str(value)
    if "'" in text:
        return text.split("'", 2)[1]
    return text


def get_asset_info(asset_path: str) -> dict:
    object_path = asset_object_path(asset_path)
    info = {
        "asset_path": asset_path,
        "object_path": object_path,
        "exists": False,
        "class_path": "",
        "is_redirector": False,
        "redirect_target": "",
        "disk_size": -1,
    }

    if hasattr(unreal, "UnrealBridgeAssetLibrary"):
        bridge_info = unreal.UnrealBridgeAssetLibrary.get_asset_info(object_path)
        info["exists"] = bool(bridge_info.found)
        if info["exists"]:
            info["class_path"] = str(bridge_info.class_path)
            info["is_redirector"] = bool(bridge_info.is_redirector)
            info["disk_size"] = int(bridge_info.disk_size)
            if info["is_redirector"]:
                info["redirect_target"] = unreal.UnrealBridgeAssetLibrary.resolve_redirector(object_path)
        return info

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_data = asset_registry.get_asset_by_object_path(object_path)
    if asset_data and asset_data.is_valid():
        info["exists"] = True
        info["class_path"] = str(asset_data.asset_class_path)
        info["is_redirector"] = info["class_path"] == REDIRECTOR_CLASS
    return info


def get_redirectors_under_path(path: str) -> list[str]:
    if hasattr(unreal, "UnrealBridgeAssetLibrary"):
        redirectors = unreal.UnrealBridgeAssetLibrary.find_redirectors_under_path(path, True)
        return sorted(soft_path_to_string(item) for item in redirectors)

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = asset_registry.get_assets_by_path(path, recursive=True)
    redirectors: list[str] = []
    for asset_data in assets:
        if str(asset_data.asset_class_path) == REDIRECTOR_CLASS:
            redirectors.append(str(asset_data.package_name))
    return sorted(redirectors)


def classify_entry(source_info: dict, target_info: dict, action: str) -> str:
    if not target_info["asset_path"]:
        return "no-target"
    if source_info["is_redirector"] and target_info["exists"] and not target_info["is_redirector"]:
        return "migrated-with-source-redirector"
    if not source_info["exists"] and target_info["exists"] and not target_info["is_redirector"]:
        return "migrated-clean"
    if source_info["exists"] and not source_info["is_redirector"] and not target_info["exists"]:
        return "pending-source-real"
    if source_info["exists"] and not source_info["is_redirector"] and target_info["exists"] and not target_info["is_redirector"]:
        return "duplicate-real-assets"
    if source_info["is_redirector"] and not target_info["exists"]:
        return "dangling-source-redirector"
    if action == "move-directory" and source_info["exists"] is False:
        return "directory-or-empty-source"
    return "needs-review"


def main() -> None:
    report_path = os.environ.get(REPORT_ENV)
    if not report_path:
        raise RuntimeError(f"{REPORT_ENV} must point to a migration JSON report")

    data = json.loads(Path(report_path).read_text(encoding="utf-8"))
    entries = []
    status_counts: dict[str, int] = {}
    move_records = [
        record
        for record in data.get("results", [])
        if record.get("action") in {"move-asset", "move-directory"} and record.get("target")
    ]

    for record in move_records:
        source = record.get("source", "")
        target = record.get("target", "")
        action = record.get("action", "")

        if action == "move-directory":
            source_redirectors = get_redirectors_under_path(source)
            target_redirectors = get_redirectors_under_path(target)
            source_count = unreal.UnrealBridgeAssetLibrary.get_asset_count_under_path(source, "", True)
            target_count = unreal.UnrealBridgeAssetLibrary.get_asset_count_under_path(target, "", True)
            if source_count == 0 and target_count > 0:
                state = "directory-migrated-clean"
            elif source_redirectors and target_count > 0:
                state = "directory-migrated-with-source-redirectors"
            elif source_count > 0 and target_count == 0:
                state = "directory-pending-source-assets"
            elif source_count > 0 and target_count > 0:
                non_redirect_source_count = max(source_count - len(source_redirectors), 0)
                state = "directory-duplicate-or-partial" if non_redirect_source_count else "directory-migrated-with-source-redirectors"
            else:
                state = "directory-empty-or-missing"

            entry = {
                "action": action,
                "source": source,
                "target": target,
                "migration_status": record.get("status", ""),
                "migration_detail": record.get("detail", ""),
                "state": state,
                "source_asset_count": int(source_count),
                "target_asset_count": int(target_count),
                "source_redirector_count": len(source_redirectors),
                "target_redirector_count": len(target_redirectors),
                "source_redirectors_sample": source_redirectors[:20],
            }
        else:
            source_info = get_asset_info(source)
            target_info = get_asset_info(target)
            state = classify_entry(source_info, target_info, action)
            entry = {
                "action": action,
                "source_path": source,
                "target_path": target,
                "migration_status": record.get("status", ""),
                "migration_detail": record.get("detail", ""),
                "state": state,
                "source_info": source_info,
                "target_info": target_info,
            }

        entries.append(entry)
        status_counts[entry["state"]] = status_counts.get(entry["state"], 0) + 1
        unreal.log(f"[{entry['state']}] {action}: {source} -> {target}")

    payload = {
        "input_report": report_path,
        "dry_run": bool(data.get("dry_run")),
        "phases": data.get("phases", []),
        "migration_errors": data.get("errors", []),
        "state_counts": dict(sorted(status_counts.items())),
        "entries": entries,
    }

    audit_path = os.environ.get(AUDIT_ENV)
    if audit_path:
        write_report(audit_path, payload)
        unreal.log(f"Wrote migration state audit: {audit_path}")

    print(json.dumps(payload, ensure_ascii=False, indent=2))


main()
