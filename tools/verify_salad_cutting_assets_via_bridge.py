import json

import unreal


EXPECTED_CUTTABLES = {
    "/Game/Blueprints/BP_Lettuce": {
        "required_chops": 1,
        "spawn_count": 1,
        "chopped_class_suffix": "/Game/Blueprints/BP_ChoppedLettuce.BP_ChoppedLettuce_C",
        "expected_raw_tag": "Raw_Lettuce",
    },
    "/Game/BP_Tomato": {
        "required_chops": 1,
        "spawn_count": 1,
        "chopped_class_suffix": "/Game/Blueprints/BP_ChoppedTomato.BP_ChoppedTomato_C",
        "expected_raw_tag": "Raw_Tomato",
    },
}

EXPECTED_CHOPPED_FOODS = {
    "/Game/Blueprints/BP_ChoppedLettuce": "Chopped_Lettuce",
    "/Game/Blueprints/BP_ChoppedTomato": "Chopped_Tomato",
}


def asset_exists(asset_path):
    return bool(unreal.EditorAssetLibrary.does_asset_exist(asset_path))


def load_blueprint_cdo(asset_path):
    asset = unreal.load_asset(asset_path)
    if not asset:
        raise RuntimeError(f"Could not load Blueprint asset: {asset_path}")

    generated_class = asset.generated_class()
    if not generated_class:
        raise RuntimeError(f"Blueprint has no generated class: {asset_path}")

    cdo = unreal.get_default_object(generated_class)
    if not cdo:
        raise RuntimeError(f"Blueprint has no class default object: {asset_path}")

    return cdo


def read_property(obj, property_name):
    try:
        return obj.get_editor_property(property_name)
    except Exception as exc:
        raise RuntimeError(f"Missing expected property {property_name}: {obj.get_path_name()} ({exc})")


def object_path(value):
    if not value:
        return ""
    if hasattr(value, "get_path_name"):
        return value.get_path_name()
    return str(value)


def read_tags(cdo):
    try:
        return {str(tag) for tag in cdo.get_editor_property("Tags")}
    except Exception:
        return set()


def require(condition, message, failures):
    if not condition:
        failures.append(message)


def main():
    failures = []
    report = {
        "cuttable_foods": {},
        "chopped_foods": {},
    }

    for asset_path, expected in EXPECTED_CUTTABLES.items():
        require(asset_exists(asset_path), f"Missing cuttable salad ingredient Blueprint: {asset_path}", failures)
        if not asset_exists(asset_path):
            continue

        cdo = load_blueprint_cdo(asset_path)
        required_chops = read_property(cdo, "RequiredChops")
        spawn_count = read_property(cdo, "SpawnCount")
        chopped_class = object_path(read_property(cdo, "ChoppedClass"))
        tags = read_tags(cdo)

        report["cuttable_foods"][asset_path] = {
            "required_chops": required_chops,
            "spawn_count": spawn_count,
            "chopped_class": chopped_class,
            "tags": sorted(tags),
        }

        require(
            int(required_chops) == expected["required_chops"],
            f"{asset_path} RequiredChops should be {expected['required_chops']}, got {required_chops}",
            failures,
        )
        require(
            int(spawn_count) == expected["spawn_count"],
            f"{asset_path} SpawnCount should be {expected['spawn_count']}, got {spawn_count}",
            failures,
        )
        require(
            chopped_class.endswith(expected["chopped_class_suffix"]),
            f"{asset_path} ChoppedClass should end with {expected['chopped_class_suffix']}, got {chopped_class}",
            failures,
        )
        require(
            expected["expected_raw_tag"] in tags,
            f"{asset_path} should carry raw salad tag {expected['expected_raw_tag']}, got {sorted(tags)}",
            failures,
        )

    for asset_path, expected_tag in EXPECTED_CHOPPED_FOODS.items():
        require(asset_exists(asset_path), f"Missing chopped salad food Blueprint: {asset_path}", failures)
        if not asset_exists(asset_path):
            continue

        cdo = load_blueprint_cdo(asset_path)
        tags = read_tags(cdo)
        report["chopped_foods"][asset_path] = {
            "tags": sorted(tags),
        }
        require(
            expected_tag in tags,
            f"{asset_path} should carry chopped salad tag {expected_tag}, got {sorted(tags)}",
            failures,
        )

    unreal.log("VRKitchen salad cutting asset validation report:")
    unreal.log(json.dumps(report, ensure_ascii=False, indent=2))

    if failures:
        raise RuntimeError("Salad cutting asset validation failed: " + "; ".join(failures))

    unreal.log("VRKitchen salad cutting asset validation passed.")


main()
