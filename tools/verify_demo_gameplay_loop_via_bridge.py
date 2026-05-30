import unreal
from unreal_bridge import Editor


LEVEL_PATH = "/Game/_Project/Maps/VRKitchen_Demo"
TEST_ACTOR_LABEL_PREFIX = "AUTO_TEST_FOOD_"

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


def has_component(actor, component_name):
    if not actor:
        return False
    return any(component_name in component.get_class().get_name() for component in actor.get_components_by_class(unreal.ActorComponent))


def destroy_spawned():
    while spawned_actors:
        actor = spawned_actors.pop()
        if actor:
            try:
                actor.destroy_actor()
            except Exception:
                pass


def clean_old_test_actors():
    for actor in subsys.get_all_level_actors():
        label = actor.get_actor_label() or ""
        if label.startswith(TEST_ACTOR_LABEL_PREFIX):
            actor.destroy_actor()


def spawn_food_stack(delivery_area, tags):
    stack_center = find_component_by_name(delivery_area, "StackCenter", unreal.SceneComponent)
    require(stack_center is not None, "Delivery area lacks StackCenter component")
    if not stack_center:
        return []

    base_location = delivery_area.get_actor_location()
    created = []
    for index, tag in enumerate(tags):
        location = unreal.Vector(base_location.x, base_location.y, base_location.z + 8.0 + index * 8.0)
        actor = subsys.spawn_actor_from_class(unreal.Actor, location)
        if not actor:
            failures.append(f"Failed to spawn test food actor for tag {tag}")
            continue
        actor.set_actor_label(f"{TEST_ACTOR_LABEL_PREFIX}{index}_{tag}")
        actor.tags.append(tag)
        actor.attach_to_component(
            stack_center,
            "None",
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            False,
        )
        spawned_actors.append(actor)
        created.append(actor)
    return created


def submit_tags(delivery_area, tags):
    destroy_spawned()
    spawn_food_stack(delivery_area, tags)
    result = unreal.VRKitchenOrderValidationLibrary.submit_current_plate_validated(delivery_area)
    destroy_spawned()
    return bool(result)


def spawn_food_on_pan(pan, tag):
    destroy_spawned()
    location = pan.get_actor_location()
    actor = subsys.spawn_actor_from_class(unreal.Actor, unreal.Vector(location.x, location.y, location.z + 20.0))
    if not actor:
        failures.append(f"Failed to spawn pan test food actor for tag {tag}")
        return None
    actor.set_actor_label(f"{TEST_ACTOR_LABEL_PREFIX}PAN_{tag}")
    actor.tags.append(tag)
    actor.attach_to_actor(
        pan,
        "None",
        unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD,
        False,
    )
    spawned_actors.append(actor)
    return actor


def actor_has_tag(actor, tag):
    return bool(actor and tag in [str(actor_tag) for actor_tag in actor.tags])


def run_pan_cooking_case(pan):
    cook_component = pan.get_component_by_class(unreal.VRKitchenPanCookComponent) if pan else None
    require(cook_component is not None, "Pan cooking validation needs VRKitchenPanCookComponent")
    if not cook_component:
        return

    cook_delta = float(cook_component.get_editor_property("CookTimeSeconds")) + 0.5
    overcook_delta = float(cook_component.get_editor_property("OvercookTimeSeconds")) + 0.5

    try:
        food = spawn_food_on_pan(pan, "Raw_Patty")
        cook_component.process_food_actor_for_demo_validation(food, False, cook_delta)
        require(actor_has_tag(food, "Raw_Patty"), "Raw patty cooked while pan was away from stove")
        require(not actor_has_tag(food, "Cooked_Patty"), "Cooked tag appeared while pan was away from stove")

        cook_component.process_food_actor_for_demo_validation(food, True, cook_delta)
        require(actor_has_tag(food, "Cooked_Patty"), "Raw patty did not cook after pan returned to stove")
        require(not actor_has_tag(food, "Raw_Patty"), "Raw tag remained after patty cooked")

        cook_component.process_food_actor_for_demo_validation(food, True, overcook_delta)
        require(actor_has_tag(food, "Burnt_Patty"), "Cooked patty did not become burnt after overcooking")
        require(not actor_has_tag(food, "Cooked_Patty"), "Cooked tag remained after patty burnt")
        print("PASS cooking case: pan only cooks on stove and can overcook")
    finally:
        destroy_spawned()


def session_prop(session, property_name):
    return session.get_editor_property(property_name)


def reset_session(session):
    session.reset_session()
    require(session_prop(session, "SessionScore") == 0, "Session score did not reset to 0")
    require(session_prop(session, "CorrectOrders") == 0, "Correct order count did not reset to 0")
    require(session_prop(session, "WrongOrders") == 0, "Wrong order count did not reset to 0")
    require(session.can_accept_orders(), "Session should accept orders after reset")


def assert_stats(session, score, correct, wrong, context):
    require(session_prop(session, "SessionScore") == score, f"{context}: expected score {score}, got {session_prop(session, 'SessionScore')}")
    require(session_prop(session, "CorrectOrders") == correct, f"{context}: expected correct {correct}, got {session_prop(session, 'CorrectOrders')}")
    require(session_prop(session, "WrongOrders") == wrong, f"{context}: expected wrong {wrong}, got {session_prop(session, 'WrongOrders')}")


def run_failure_case(session, delivery_area, name, tags):
    reset_session(session)
    ok = submit_tags(delivery_area, tags)
    require(not ok, f"{name}: submission should fail")
    assert_stats(session, 0, 0, 1, name)
    print(f"PASS failure case: {name}")


order_manager = find_actor_by_label("BP_OrderManager_Playable")
delivery_area = find_actor_by_label("BP_DeliveryArea")
order_tablet = find_actor_by_label("BP_OrderTablet")
pan = find_actor_by_label("BP_Pan")
stove = find_actor_by_label("BP_Stove")

require(order_manager is not None, "Missing BP_OrderManager_Playable in demo map")
require(delivery_area is not None, "Missing BP_DeliveryArea in demo map")
require(order_tablet is not None, "Missing BP_OrderTablet in demo map")
require(pan is not None, "Missing BP_Pan in demo map")
require(stove is not None, "Missing BP_Stove in demo map")
require(hasattr(unreal, "VRKitchenOrderValidationLibrary"), "Missing VRKitchen order validation library")
require(hasattr(unreal, "VRKitchenGameSessionComponent"), "Missing VRKitchen game session component")
require(hasattr(unreal, "VRKitchenPanCookComponent"), "Missing VRKitchen pan cook component")
require(has_component(order_manager, "VRKitchenOrderTextCleanupComponent"), "Order manager lacks order text cleanup component")
require(has_component(pan, "VRKitchenPanCookComponent"), "Pan lacks pan cook component")

clean_old_test_actors()

if pan:
    run_pan_cooking_case(pan)

if order_manager and delivery_area:
    # The first empty submit creates the runtime session component in editor commandlets.
    unreal.VRKitchenOrderValidationLibrary.submit_current_plate_validated(delivery_area)
    session = order_manager.get_component_by_class(unreal.VRKitchenGameSessionComponent)
    require(session is not None, "Session component was not created on order manager")

    if session:
        simple_order = ["Bottom_Bun", "Cooked_Patty", "Top_Bun"]

        reset_session(session)
        ok = submit_tags(delivery_area, simple_order)
        require(ok, "Correct simple order should succeed")
        assert_stats(session, 10, 1, 0, "correct order")
        print("PASS success case: correct simple order adds score")

        run_failure_case(session, delivery_area, "empty plate", [])
        run_failure_case(session, delivery_area, "raw food", ["Bottom_Bun", "Raw_Patty", "Top_Bun"])
        run_failure_case(session, delivery_area, "burnt food", ["Bottom_Bun", "Burnt_Patty", "Top_Bun"])
        run_failure_case(session, delivery_area, "missing food", ["Bottom_Bun", "Cooked_Patty"])
        run_failure_case(session, delivery_area, "extra food", ["Bottom_Bun", "Cooked_Patty", "Top_Bun", "Chopped_Lettuce"])
        run_failure_case(session, delivery_area, "wrong order", ["Cooked_Patty", "Bottom_Bun", "Top_Bun"])

        reset_session(session)
        ok = submit_tags(delivery_area, simple_order)
        require(ok, "Pre-timeout correct order should succeed")
        session.end_session()
        previous_score = session_prop(session, "SessionScore")
        previous_correct = session_prop(session, "CorrectOrders")
        ok_after_end = submit_tags(delivery_area, simple_order)
        require(not ok_after_end, "Order submit after time end should fail")
        require(session_prop(session, "SessionScore") == previous_score, "Score changed after time end")
        require(session_prop(session, "CorrectOrders") == previous_correct, "Correct count changed after time end")
        require(not session.can_accept_orders(), "Session should not accept orders after end")
        print("PASS timeout case: no scoring after session end")

        session.reset_session()
        require(session.can_accept_orders(), "Session should accept orders after reset")
        assert_stats(session, 0, 0, 0, "reset after timeout")
        print("PASS reset case: session can restart after time end")

        reset_session(session)
        require(submit_tags(delivery_area, simple_order), "First simple order should succeed")
        require(submit_tags(delivery_area, simple_order), "Second simple order should succeed")
        require(not submit_tags(delivery_area, simple_order), "Third simple order should fail after difficulty increases")
        lettuce_order = ["Bottom_Bun", "Cooked_Patty", "Chopped_Lettuce", "Top_Bun"]
        require(submit_tags(delivery_area, lettuce_order), "Third progressive lettuce order should succeed")
        require(session_prop(session, "CorrectOrders") == 3, "Three completed orders were not recorded")
        require(session_prop(session, "WrongOrders") == 1, "Difficulty probe failure should be counted once")
        require(session_prop(session, "SessionScore") == 28, f"Expected score 28 after progression probe, got {session_prop(session, 'SessionScore')}")
        print("PASS progression case: third order requires chopped ingredient")

destroy_spawned()

if failures:
    raise RuntimeError("Demo gameplay validation failed: " + "; ".join(failures))

print("VRKitchen demo gameplay validation passed.")
