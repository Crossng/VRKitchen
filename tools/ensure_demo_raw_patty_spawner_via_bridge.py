import json
import math

import unreal
from unreal_bridge import Editor, Level


LEVEL_PATH = "/Game/_Project/Maps/VRKitchen_Demo"
SPAWNER_CLASS = "/Game/Blueprints/BP_FoodSpawner.BP_FoodSpawner_C"
RAW_PATTY_CLASS = "/Game/Blueprints/BP_Patty.BP_Patty_C"
TARGET_LABEL = "BP_FoodSpawner_RawPatty"

REFERENCE_FOOD_CLASSES = {
    "bottom_bun": "/Game/Blueprints/BP_BottomBun.BP_BottomBun_C",
    "top_bun": "/Game/Blueprints/BP_TopBun.BP_TopBun_C",
    "raw_meat": "/Game/Blueprints/BP_Meat.BP_Meat_C",
}


def actor_label(actor):
    return actor.get_actor_label() or actor.get_name() or ""


def class_path(actor):
    actor_class = actor.get_class()
    return actor_class.get_path_name() if actor_class else ""


def vector_to_dict(value):
    return {"x": round(value.x, 2), "y": round(value.y, 2), "z": round(value.z, 2)}


def value_to_path(value):
    if not value:
        return ""
    if hasattr(value, "get_path_name"):
        return value.get_path_name()
    return str(value)


def get_food_to_spawn(actor):
    try:
        return value_to_path(actor.get_editor_property("FoodToSpawn"))
    except Exception:
        return ""


def set_food_to_spawn(actor, food_class_path):
    food_class = unreal.load_class(None, food_class_path)
    if not food_class:
        raise RuntimeError(f"Could not load food class: {food_class_path}")
    actor.set_editor_property("FoodToSpawn", food_class)


def distance(first, second):
    a = first.get_actor_location()
    b = second.get_actor_location()
    return math.dist((a.x, a.y, a.z), (b.x, b.y, b.z))


def find_food_spawners(actors):
    return [actor for actor in actors if class_path(actor).startswith("/Game/Blueprints/BP_FoodSpawner.")]


def choose_target_location(food_spawners):
    reference_spawners = [
        spawner for spawner in food_spawners
        if get_food_to_spawn(spawner) in REFERENCE_FOOD_CLASSES.values()
    ]
    if reference_spawners:
        avg_x = sum(spawner.get_actor_location().x for spawner in reference_spawners) / len(reference_spawners)
        avg_y = sum(spawner.get_actor_location().y for spawner in reference_spawners) / len(reference_spawners)
        avg_z = sum(spawner.get_actor_location().z for spawner in reference_spawners) / len(reference_spawners)
        return unreal.Vector(avg_x + 45.0, avg_y, avg_z)

    if food_spawners:
        base = food_spawners[0].get_actor_location()
        return unreal.Vector(base.x + 45.0, base.y, base.z)

    return unreal.Vector(-80.0, -85.0, 115.0)


def choose_target_rotation(food_spawners):
    if food_spawners:
        rot = food_spawners[0].get_actor_rotation()
        return {"pitch": rot.pitch, "yaw": rot.yaw, "roll": rot.roll}
    return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}


def main():
    Editor.load_level(level_path=LEVEL_PATH, prompt_save_changes=False)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(subsystem.get_all_level_actors())
    food_spawners = find_food_spawners(actors)

    existing_raw_patty_spawners = [
        spawner for spawner in food_spawners
        if get_food_to_spawn(spawner) == RAW_PATTY_CLASS
    ]

    result = {
        "level_path": LEVEL_PATH,
        "target_label": TARGET_LABEL,
        "raw_patty_class": RAW_PATTY_CLASS,
        "before": [
            {
                "label": actor_label(spawner),
                "food_to_spawn": get_food_to_spawn(spawner),
                "location": vector_to_dict(spawner.get_actor_location()),
            }
            for spawner in food_spawners
        ],
        "action": "",
    }

    if existing_raw_patty_spawners:
        target = existing_raw_patty_spawners[0]
        target.set_actor_label(TARGET_LABEL, mark_dirty=True)
        result["action"] = "reused_existing_raw_patty_spawner"
    else:
        target_location = choose_target_location(food_spawners)
        spawned_name = Level.spawn_actor(
            class_path=SPAWNER_CLASS,
            location={"x": target_location.x, "y": target_location.y, "z": target_location.z},
            rotation=choose_target_rotation(food_spawners),
        )
        if not spawned_name:
            raise RuntimeError("Failed to spawn BP_FoodSpawner for raw patty")

        target = None
        for actor in subsystem.get_all_level_actors():
            if actor.get_name() == spawned_name or actor_label(actor) == spawned_name:
                target = actor
                break
        if not target:
            raise RuntimeError(f"Spawned actor not found after creation: {spawned_name}")

        target.set_actor_label(TARGET_LABEL, mark_dirty=True)
        set_food_to_spawn(target, RAW_PATTY_CLASS)
        result["action"] = "spawned_raw_patty_spawner"

    if get_food_to_spawn(target) != RAW_PATTY_CLASS:
        set_food_to_spawn(target, RAW_PATTY_CLASS)
        result["action"] += "+fixed_food_to_spawn"

    # Keep the new spawner slightly separated from nearby food stations so the grip target is unambiguous.
    nearby_raw_food_spawners = [
        spawner for spawner in food_spawners
        if spawner != target and get_food_to_spawn(spawner) in REFERENCE_FOOD_CLASSES.values()
    ]
    if nearby_raw_food_spawners:
        too_close = any(distance(target, spawner) < 30.0 for spawner in nearby_raw_food_spawners)
        if too_close:
            loc = target.get_actor_location()
            target.set_actor_location(unreal.Vector(loc.x + 45.0, loc.y, loc.z), False, False)
            result["action"] += "+nudged_for_spacing"

    refreshed_spawners = find_food_spawners(list(subsystem.get_all_level_actors()))
    result["after"] = [
        {
            "label": actor_label(spawner),
            "food_to_spawn": get_food_to_spawn(spawner),
            "location": vector_to_dict(spawner.get_actor_location()),
        }
        for spawner in refreshed_spawners
    ]
    result["raw_patty_spawner_count"] = sum(
        1 for spawner in refreshed_spawners if get_food_to_spawn(spawner) == RAW_PATTY_CLASS
    )
    result["saved"] = Editor.save_current_level()

    if result["raw_patty_spawner_count"] < 1:
        raise RuntimeError("Raw patty spawner was not present after repair")

    print(json.dumps(result, ensure_ascii=False, indent=2))


main()
