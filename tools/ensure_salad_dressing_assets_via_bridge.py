import json
import math

import unreal
from unreal_bridge import Editor, Level


LEVEL_PATH = "/Game/_Project/Maps/VRKitchen_Demo"
SOURCE_FOOD_BP = "/Game/Blueprints/BP_TopBun"
SALAD_DRESSING_BP = "/Game/Blueprints/BP_SaladDressing"
SALAD_DRESSING_CLASS = "/Game/Blueprints/BP_SaladDressing.BP_SaladDressing_C"
SALAD_DRESSING_TAG = "Salad_Dressing"
SALAD_DRESSING_MESH_CANDIDATES = (
    "/Game/food_select/Props/SM_Sauce_Mustard",
    "/Game/food_select/Props/SM_Sauce_Ketchup",
    "/Game/_Dev/Prototypes/food_test/Props/SM_Sauce_Mustard",
    "/Game/_Dev/Prototypes/food_test/Props/SM_Sauce_Ketchup",
)
SPAWNER_CLASS = "/Game/Blueprints/BP_FoodSpawner.BP_FoodSpawner_C"
TARGET_LABEL = "BP_FoodSpawner_SaladDressing"
REFERENCE_FOOD_CLASSES = {
    "raw_lettuce": "/Game/Blueprints/BP_Lettuce.BP_Lettuce_C",
    "raw_tomato": "/Game/BP_Tomato.BP_Tomato_C",
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

    return asset, generated_class, cdo


def ensure_blueprint():
    if unreal.EditorAssetLibrary.does_asset_exist(SALAD_DRESSING_BP):
        return unreal.load_asset(SALAD_DRESSING_BP), "reused_existing_blueprint"

    source_asset = unreal.load_asset(SOURCE_FOOD_BP)
    if not source_asset:
        raise RuntimeError(f"Could not load source food Blueprint: {SOURCE_FOOD_BP}")

    duplicated = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(
        "BP_SaladDressing",
        "/Game/Blueprints",
        source_asset,
    )
    if not duplicated:
        raise RuntimeError(f"Could not duplicate {SOURCE_FOOD_BP} to {SALAD_DRESSING_BP}")
    return duplicated, "duplicated_from_top_bun"


def set_tags(cdo):
    tags = list(cdo.get_editor_property("Tags"))
    original_tags = [str(tag) for tag in tags]
    filtered = [tag for tag in tags if str(tag) in {SALAD_DRESSING_TAG}]
    if SALAD_DRESSING_TAG not in {str(tag) for tag in filtered}:
        filtered.append(unreal.Name(SALAD_DRESSING_TAG))
    cdo.set_editor_property("Tags", filtered)
    return original_tags, [str(tag) for tag in filtered]


def load_first_existing_mesh():
    for mesh_path in SALAD_DRESSING_MESH_CANDIDATES:
        mesh = unreal.load_asset(mesh_path)
        if mesh:
            return mesh_path, mesh
    return "", None


def try_set_static_mesh(cdo):
    mesh_path, mesh = load_first_existing_mesh()
    if not mesh:
        return {"changed": False, "mesh": "", "warning": "No sauce static mesh candidate could be loaded"}

    changed_components = []
    for component in cdo.get_components_by_class(unreal.StaticMeshComponent):
        current_mesh = component.get_editor_property("static_mesh")
        current_path = current_mesh.get_path_name() if current_mesh else ""
        if current_path != mesh.get_path_name():
            component.set_editor_property("static_mesh", mesh)
            changed_components.append(component.get_name())

    return {
        "changed": bool(changed_components),
        "mesh": mesh_path,
        "components": changed_components,
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
    vegetable_spawners = [
        spawner for spawner in food_spawners
        if get_food_to_spawn(spawner) in REFERENCE_FOOD_CLASSES.values()
    ]
    if vegetable_spawners:
        avg_x = sum(spawner.get_actor_location().x for spawner in vegetable_spawners) / len(vegetable_spawners)
        avg_y = sum(spawner.get_actor_location().y for spawner in vegetable_spawners) / len(vegetable_spawners)
        avg_z = sum(spawner.get_actor_location().z for spawner in vegetable_spawners) / len(vegetable_spawners)
        return unreal.Vector(avg_x + 55.0, avg_y, avg_z)

    if food_spawners:
        base = food_spawners[0].get_actor_location()
        return unreal.Vector(base.x + 55.0, base.y, base.z)

    return unreal.Vector(-75.0, -85.0, 115.0)


def choose_target_rotation(food_spawners):
    if food_spawners:
        rot = food_spawners[0].get_actor_rotation()
        return {"pitch": rot.pitch, "yaw": rot.yaw, "roll": rot.roll}
    return {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}


def ensure_spawner():
    Editor.load_level(level_path=LEVEL_PATH, prompt_save_changes=False)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(subsystem.get_all_level_actors())
    food_spawners = find_food_spawners(actors)
    existing = [spawner for spawner in food_spawners if get_food_to_spawn(spawner) == SALAD_DRESSING_CLASS]

    if existing:
        target = existing[0]
        target.set_actor_label(TARGET_LABEL, mark_dirty=True)
        action = "reused_existing_salad_dressing_spawner"
    else:
        target_location = choose_target_location(food_spawners)
        spawned_name = Level.spawn_actor(
            class_path=SPAWNER_CLASS,
            location={"x": target_location.x, "y": target_location.y, "z": target_location.z},
            rotation=choose_target_rotation(food_spawners),
        )
        if not spawned_name:
            raise RuntimeError("Failed to spawn BP_FoodSpawner for salad dressing")

        target = None
        for actor in subsystem.get_all_level_actors():
            if actor.get_name() == spawned_name or actor_label(actor) == spawned_name:
                target = actor
                break
        if not target:
            raise RuntimeError(f"Spawned actor not found after creation: {spawned_name}")

        target.set_actor_label(TARGET_LABEL, mark_dirty=True)
        action = "spawned_salad_dressing_spawner"

    if get_food_to_spawn(target) != SALAD_DRESSING_CLASS:
        set_food_to_spawn(target, SALAD_DRESSING_CLASS)
        action += "+fixed_food_to_spawn"

    nearby_vegetable_spawners = [
        spawner for spawner in food_spawners
        if spawner != target and get_food_to_spawn(spawner) in REFERENCE_FOOD_CLASSES.values()
    ]
    if nearby_vegetable_spawners and any(distance(target, spawner) < 30.0 for spawner in nearby_vegetable_spawners):
        loc = target.get_actor_location()
        target.set_actor_location(unreal.Vector(loc.x + 45.0, loc.y, loc.z), False, False)
        action += "+nudged_for_spacing"

    refreshed = find_food_spawners(list(subsystem.get_all_level_actors()))
    return {
        "action": action,
        "salad_dressing_spawner_count": sum(1 for spawner in refreshed if get_food_to_spawn(spawner) == SALAD_DRESSING_CLASS),
        "target": {
            "label": actor_label(target),
            "food_to_spawn": get_food_to_spawn(target),
            "location": vector_to_dict(target.get_actor_location()),
        },
        "saved_level": Editor.save_current_level(),
    }


def main():
    asset, blueprint_action = ensure_blueprint()
    _, _, cdo = load_blueprint(SALAD_DRESSING_BP)
    original_tags, final_tags = set_tags(cdo)
    mesh_result = try_set_static_mesh(cdo)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)

    spawner_result = ensure_spawner()
    if spawner_result["salad_dressing_spawner_count"] < 1:
        raise RuntimeError("Salad dressing spawner was not present after repair")

    report = {
        "blueprint": {
            "path": SALAD_DRESSING_BP,
            "action": blueprint_action,
            "original_tags": original_tags,
            "final_tags": final_tags,
            "mesh": mesh_result,
        },
        "spawner": spawner_result,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


main()
