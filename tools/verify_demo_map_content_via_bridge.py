import json
import math

import unreal
from unreal_bridge import Editor


LEVEL_PATH = "/Game/_Project/Maps/VRKitchen_Demo"

REQUIRED_ACTOR_GROUPS = {
    "order_manager": ("/Game/_Project/Gameplay/Orders/BP_OrderManager_Playable.",),
    "order_tablet": ("/Game/_Project/Gameplay/Orders/BP_OrderTablet.",),
    "delivery_area": ("/Game/_Project/Gameplay/Orders/BP_DeliveryArea_Runtime.",),
    "pan": ("/Game/BP_Pan.",),
    "stove": ("/Game/BP_Stove.",),
    "cutting_board": ("/Game/Blueprints/BP_CuttingBoard.",),
    "knife": ("/Game/Blueprints/BP_Knife.",),
}

REQUIRED_MIN_COUNTS = {
    "plate": {
        "min_count": 2,
        "class_prefixes": ("/Game/BP_Plate.",),
    },
    "food_spawner": {
        "min_count": 6,
        "class_prefixes": ("/Game/Blueprints/BP_FoodSpawner.",),
    },
    "trash_visual": {
        "min_count": 1,
        "label_tokens": ("trash", "bin"),
        "class_tokens": ("trash", "bin"),
    },
}

REQUIRED_FOOD_CLASSES = {
    "bottom_bun": "/Game/Blueprints/BP_BottomBun.BP_BottomBun_C",
    "top_bun": "/Game/Blueprints/BP_TopBun.BP_TopBun_C",
    "raw_patty": "/Game/Blueprints/BP_Patty.BP_Patty_C",
    "raw_meat": "/Game/Blueprints/BP_Meat.BP_Meat_C",
    "raw_lettuce": "/Game/Blueprints/BP_Lettuce.BP_Lettuce_C",
    "raw_tomato": "/Game/BP_Tomato.BP_Tomato_C",
    "salad_dressing": "/Game/Blueprints/BP_SaladDressing.BP_SaladDressing_C",
}

REQUIRED_FOOD_TAGS = {
    "salad_dressing": {
        "asset_path": "/Game/Blueprints/BP_SaladDressing",
        "tag": "Salad_Dressing",
    },
}

MIN_REASONABLE_DISTANCE = 35.0


def class_path(actor):
    actor_class = actor.get_class()
    return actor_class.get_path_name() if actor_class else ""


def actor_label(actor):
    return actor.get_actor_label() or actor.get_name() or ""


def vector_to_dict(value):
    return {"x": round(value.x, 2), "y": round(value.y, 2), "z": round(value.z, 2)}


def actor_to_summary(actor):
    return {
        "label": actor_label(actor),
        "class_path": class_path(actor),
        "location": vector_to_dict(actor.get_actor_location()),
        "tags": [str(tag) for tag in actor.tags],
    }


def distance_between(first, second):
    first_location = first.get_actor_location()
    second_location = second.get_actor_location()
    return math.dist(
        (first_location.x, first_location.y, first_location.z),
        (second_location.x, second_location.y, second_location.z),
    )


def find_by_class_prefix(actors, prefixes):
    return [actor for actor in actors if any(class_path(actor).startswith(prefix) for prefix in prefixes)]


def find_by_text_tokens(actors, label_tokens=(), class_tokens=()):
    matches = []
    for actor in actors:
        label_text = actor_label(actor).lower()
        class_text = class_path(actor).lower()
        if any(token in label_text for token in label_tokens) or any(token in class_text for token in class_tokens):
            matches.append(actor)
    return matches


def read_object_property(actor, property_name):
    try:
        value = actor.get_editor_property(property_name)
    except Exception:
        return ""
    if not value:
        return ""
    if hasattr(value, "get_path_name"):
        return value.get_path_name()
    return str(value)


def read_blueprint_cdo_tags(asset_path):
    asset = unreal.load_asset(asset_path)
    if not asset or not asset.generated_class():
        return set()
    cdo = unreal.get_default_object(asset.generated_class())
    if not cdo:
        return set()
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
        "level_path": LEVEL_PATH,
        "required_groups": {},
        "count_groups": {},
        "food_spawners": {},
        "layout_checks": {},
    }

    Editor.load_level(level_path=LEVEL_PATH, prompt_save_changes=False)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(subsystem.get_all_level_actors())

    group_first_actor = {}
    for group_name, prefixes in REQUIRED_ACTOR_GROUPS.items():
        matches = find_by_class_prefix(actors, prefixes)
        report["required_groups"][group_name] = [actor_to_summary(actor) for actor in matches]
        require(matches, f"Missing required demo map actor group: {group_name}", failures)
        if matches:
            group_first_actor[group_name] = matches[0]

    count_group_matches = {}
    for group_name, spec in REQUIRED_MIN_COUNTS.items():
        if "class_prefixes" in spec:
            matches = find_by_class_prefix(actors, spec["class_prefixes"])
        else:
            matches = find_by_text_tokens(
                actors,
                label_tokens=spec.get("label_tokens", ()),
                class_tokens=spec.get("class_tokens", ()),
            )
        count_group_matches[group_name] = matches
        report["count_groups"][group_name] = [actor_to_summary(actor) for actor in matches]
        require(
            len(matches) >= spec["min_count"],
            f"Demo map needs at least {spec['min_count']} {group_name} actor(s), found {len(matches)}",
            failures,
        )

    food_spawners = count_group_matches.get("food_spawner", [])
    spawner_classes = {
        actor_label(spawner): read_object_property(spawner, "FoodToSpawn")
        for spawner in food_spawners
    }
    report["food_spawners"] = spawner_classes
    spawned_class_values = set(spawner_classes.values())
    for food_name, expected_class in REQUIRED_FOOD_CLASSES.items():
        require(
            expected_class in spawned_class_values,
            f"Food spawners do not cover {food_name}: expected {expected_class}, got {sorted(spawned_class_values)}",
            failures,
        )

    report["food_tags"] = {}
    for food_name, expected in REQUIRED_FOOD_TAGS.items():
        tags = read_blueprint_cdo_tags(expected["asset_path"])
        report["food_tags"][food_name] = sorted(tags)
        require(
            expected["tag"] in tags,
            f"{food_name} asset should carry order tag {expected['tag']}, got {sorted(tags)}",
            failures,
        )

    if "pan" in group_first_actor and "stove" in group_first_actor:
        pan_stove_distance = distance_between(group_first_actor["pan"], group_first_actor["stove"])
        report["layout_checks"]["pan_stove_distance"] = round(pan_stove_distance, 2)
        require(
            pan_stove_distance <= 160.0,
            f"Pan should be near stove for the cooking demo, distance is {pan_stove_distance:.2f}",
            failures,
        )

    if "cutting_board" in group_first_actor and "knife" in group_first_actor:
        cutting_tool_distance = distance_between(group_first_actor["cutting_board"], group_first_actor["knife"])
        report["layout_checks"]["cutting_tool_distance"] = round(cutting_tool_distance, 2)
        require(
            cutting_tool_distance <= 180.0,
            f"Knife should be near cutting board for the salad demo, distance is {cutting_tool_distance:.2f}",
            failures,
        )

    for first_name, second_name in (
        ("order_manager", "delivery_area"),
        ("order_tablet", "delivery_area"),
        ("pan", "cutting_board"),
    ):
        if first_name not in group_first_actor or second_name not in group_first_actor:
            continue
        distance = distance_between(group_first_actor[first_name], group_first_actor[second_name])
        key = f"{first_name}_to_{second_name}_distance"
        report["layout_checks"][key] = round(distance, 2)
        require(
            distance >= MIN_REASONABLE_DISTANCE,
            f"{first_name} and {second_name} look stacked on the same point, distance is {distance:.2f}",
            failures,
        )

    unreal.log("VRKitchen demo map content validation report:")
    unreal.log(json.dumps(report, ensure_ascii=False, indent=2))

    if failures:
        raise RuntimeError("Demo map content validation failed: " + "; ".join(failures))

    unreal.log("VRKitchen demo map content validation passed.")


main()
