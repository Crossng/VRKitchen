import json

import unreal


CUTTABLE_DEFAULTS = {
    "/Game/Blueprints/BP_Lettuce": {
        "RequiredChops": 1,
        "SpawnCount": 1,
        "ChoppedClass": "/Game/Blueprints/BP_ChoppedLettuce.BP_ChoppedLettuce_C",
        "Tag": "Raw_Lettuce",
    },
    "/Game/BP_Tomato": {
        "RequiredChops": 1,
        "SpawnCount": 1,
        "ChoppedClass": "/Game/Blueprints/BP_ChoppedTomato.BP_ChoppedTomato_C",
        "Tag": "Raw_Tomato",
    },
}

CHOPPED_DEFAULTS = {
    "/Game/Blueprints/BP_ChoppedLettuce": "Chopped_Lettuce",
    "/Game/Blueprints/BP_ChoppedTomato": "Chopped_Tomato",
}


def load_blueprint(asset_path):
    asset = unreal.load_asset(asset_path)
    if not asset:
        raise RuntimeError(f"Could not load Blueprint asset: {asset_path}")

    generated_class = asset.generated_class()
    if not generated_class:
        raise RuntimeError(f"Blueprint has no generated class: {asset_path}")

    cdo = unreal.get_default_object(generated_class)
    if not cdo:
        raise RuntimeError(f"Blueprint has no class default object: {asset_path}")

    return asset, cdo


def add_tag(cdo, tag):
    tags = list(cdo.get_editor_property("Tags"))
    existing = {str(existing_tag) for existing_tag in tags}
    if tag in existing:
        return False

    tags.append(unreal.Name(tag))
    cdo.set_editor_property("Tags", tags)
    return True


def set_if_different(cdo, property_name, value):
    current = cdo.get_editor_property(property_name)
    if property_name == "ChoppedClass":
        current_path = current.get_path_name() if current else ""
        new_class = unreal.load_class(None, value)
        if not new_class:
            raise RuntimeError(f"Could not load ChoppedClass: {value}")
        if current_path == new_class.get_path_name():
            return False
        cdo.set_editor_property(property_name, new_class)
        return True

    if int(current) == int(value):
        return False
    cdo.set_editor_property(property_name, value)
    return True


def main():
    report = {}

    for asset_path, defaults in CUTTABLE_DEFAULTS.items():
        asset, cdo = load_blueprint(asset_path)
        changed = {
            "RequiredChops": set_if_different(cdo, "RequiredChops", defaults["RequiredChops"]),
            "SpawnCount": set_if_different(cdo, "SpawnCount", defaults["SpawnCount"]),
            "ChoppedClass": set_if_different(cdo, "ChoppedClass", defaults["ChoppedClass"]),
            "Tag": add_tag(cdo, defaults["Tag"]),
        }
        unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report[asset_path] = changed

    for asset_path, tag in CHOPPED_DEFAULTS.items():
        asset, cdo = load_blueprint(asset_path)
        changed = {"Tag": add_tag(cdo, tag)}
        unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report[asset_path] = changed

    unreal.log("VRKitchen salad cutting asset fix report:")
    unreal.log(json.dumps(report, ensure_ascii=False, indent=2))


main()
