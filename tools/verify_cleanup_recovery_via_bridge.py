import unreal
from unreal_bridge import Editor


LEVEL_PATH = "/Game/_Project/Maps/VRKitchen_Demo"
TEST_ACTOR_LABEL_PREFIX = "AUTO_TEST_CLEANUP_"

Editor.load_level(level_path=LEVEL_PATH, prompt_save_changes=False)

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
failures = []
spawned_actors = []


def require(condition, message):
    if not condition:
        failures.append(message)


def find_actor_by_label(label_fragment):
    for actor in subsys.get_all_level_actors():
        label = actor.get_actor_label() or ""
        if label_fragment in label:
            return actor
    return None


def find_component_by_name(actor, component_name, component_class=unreal.ActorComponent):
    if not actor:
        return None
    for component in actor.get_components_by_class(component_class):
        if component.get_name() == component_name:
            return component
    return None


def destroy_spawned():
    while spawned_actors:
        actor = spawned_actors.pop()
        if actor:
            try:
                actor.destroy_actor()
            except Exception:
                pass


def clean_old_test_actors():
    for actor in list(subsys.get_all_level_actors()):
        label = actor.get_actor_label() or ""
        if label.startswith(TEST_ACTOR_LABEL_PREFIX):
            actor.destroy_actor()


def actor_exists(actor):
    return actor in list(subsys.get_all_level_actors())


def spawn_tagged_actor(label_suffix, location, tag):
    actor = subsys.spawn_actor_from_class(unreal.Actor, location)
    require(actor is not None, f"Failed to spawn cleanup test actor {label_suffix}")
    if not actor:
        return None
    actor.set_actor_label(f"{TEST_ACTOR_LABEL_PREFIX}{label_suffix}")
    actor.tags.append(tag)
    spawned_actors.append(actor)
    return actor


def attach_actor_to_component(actor, component, z_offset):
    actor.attach_to_component(
        component,
        "None",
        unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD,
        False,
    )
    actor.set_actor_relative_location(unreal.Vector(0.0, 0.0, z_offset), False, False)


def read_session_stats(session):
    return {
        "score": int(session.get_editor_property("SessionScore")),
        "correct": int(session.get_editor_property("CorrectOrders")),
        "wrong": int(session.get_editor_property("WrongOrders")),
        "streak": int(session.get_editor_property("CurrentStreak")),
    }


def find_or_create_session(order_manager, delivery_area):
    session = order_manager.get_component_by_class(unreal.VRKitchenGameSessionComponent) if order_manager else None
    if session:
        session.reset_session()
        return session

    # The same runtime path used by order submission creates the session component on demand.
    unreal.VRKitchenOrderValidationLibrary.submit_current_plate_validated(delivery_area)
    session = order_manager.get_component_by_class(unreal.VRKitchenGameSessionComponent) if order_manager else None
    if session:
        session.reset_session()
    return session


def run_clear_current_plate_case(delivery_area, session):
    stack_center = find_component_by_name(delivery_area, "StackCenter", unreal.SceneComponent)
    require(stack_center is not None, "Delivery area lacks StackCenter")
    if not stack_center:
        return

    session.reset_session()
    stats_before = read_session_stats(session)
    base_location = delivery_area.get_actor_location()
    food_a = spawn_tagged_actor("PLATE_A", unreal.Vector(base_location.x, base_location.y, base_location.z + 20.0), "Chopped_Lettuce")
    food_b = spawn_tagged_actor("PLATE_B", unreal.Vector(base_location.x, base_location.y, base_location.z + 35.0), "Chopped_Tomato")
    attach_actor_to_component(food_a, stack_center, 8.0)
    attach_actor_to_component(food_b, stack_center, 16.0)

    removed = unreal.VRKitchenOrderValidationLibrary.clear_current_plate(delivery_area)
    stats_after = read_session_stats(session)

    require(int(removed) == 2, f"ClearCurrentPlate should remove 2 food actors, removed {removed}")
    require(not actor_exists(food_a), "ClearCurrentPlate did not destroy first plate food")
    require(not actor_exists(food_b), "ClearCurrentPlate did not destroy second plate food")
    require(stats_after == stats_before, f"ClearCurrentPlate should not change session stats, before={stats_before}, after={stats_after}")
    print("PASS cleanup case: ClearCurrentPlate removes stacked food without scoring")


def run_cleanup_area_case(session):
    session.reset_session()
    stats_before = read_session_stats(session)
    cleanup_area = subsys.spawn_actor_from_class(unreal.Actor, unreal.Vector(120.0, 120.0, 120.0))
    require(cleanup_area is not None, "Failed to spawn temporary cleanup area")
    if not cleanup_area:
        return
    cleanup_area.set_actor_label(f"{TEST_ACTOR_LABEL_PREFIX}AREA")
    spawned_actors.append(cleanup_area)

    food = spawn_tagged_actor("BIN_FOOD", unreal.Vector(120.0, 120.0, 140.0), "Burnt_Patty")
    food.attach_to_actor(
        cleanup_area,
        "None",
        unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD,
        False,
    )

    removed = unreal.VRKitchenOrderValidationLibrary.clear_food_actors_in_cleanup_area(cleanup_area)
    stats_after = read_session_stats(session)

    require(int(removed) == 1, f"ClearFoodActorsInCleanupArea should remove 1 food actor, removed {removed}")
    require(not actor_exists(food), "ClearFoodActorsInCleanupArea did not destroy attached food")
    require(actor_exists(cleanup_area), "ClearFoodActorsInCleanupArea should not destroy the cleanup area actor")
    require(stats_after == stats_before, f"ClearFoodActorsInCleanupArea should not change session stats, before={stats_before}, after={stats_after}")
    print("PASS cleanup case: ClearFoodActorsInCleanupArea discards food without scoring")


try:
    clean_old_test_actors()
    delivery_area = find_actor_by_label("BP_DeliveryArea_Runtime")
    order_manager = find_actor_by_label("BP_OrderManager_Playable")
    require(delivery_area is not None, "Missing BP_DeliveryArea_Runtime in demo map")
    require(order_manager is not None, "Missing BP_OrderManager_Playable in demo map")
    session = find_or_create_session(order_manager, delivery_area) if order_manager and delivery_area else None
    require(session is not None, "Could not create or find VRKitchenGameSessionComponent")

    if delivery_area and session:
        run_clear_current_plate_case(delivery_area, session)
        run_cleanup_area_case(session)
finally:
    destroy_spawned()

if failures:
    raise RuntimeError("Cleanup recovery validation failed: " + "; ".join(failures))

print("VRKitchen cleanup recovery validation passed.")
