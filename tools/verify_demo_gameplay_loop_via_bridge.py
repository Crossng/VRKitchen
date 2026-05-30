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
    require(session_prop(session, "CurrentStreak") == 0, "Current streak did not reset to 0")
    require(session_prop(session, "BestStreak") == 0, "Best streak did not reset to 0")
    require(session_prop(session, "TargetScore") >= 115, "Target score should keep the full combo demo menu visible")
    require(session.can_accept_orders(), "Session should accept orders after reset")


def assert_stats(session, score, correct, wrong, context):
    require(session_prop(session, "SessionScore") == score, f"{context}: expected score {score}, got {session_prop(session, 'SessionScore')}")
    require(session_prop(session, "CorrectOrders") == correct, f"{context}: expected correct {correct}, got {session_prop(session, 'CorrectOrders')}")
    require(session_prop(session, "WrongOrders") == wrong, f"{context}: expected wrong {wrong}, got {session_prop(session, 'WrongOrders')}")


def require_text_contains(value, fragment, context):
    text = str(value)
    require(fragment in text, f"{context}: expected '{fragment}' in '{text}'")


def assert_session_guidance(session, stage_index, stage_fragment, urgency_level, urgency_fragment, goal_fragment, hint_fragment, context):
    require(session.get_order_stage_index() == stage_index, f"{context}: expected stage {stage_index}, got {session.get_order_stage_index()}")
    require_text_contains(session.get_order_stage_text(), stage_fragment, f"{context} stage text")
    require(session.get_urgency_level() == urgency_level, f"{context}: expected urgency {urgency_level}, got {session.get_urgency_level()}")
    require_text_contains(session.get_urgency_text(), urgency_fragment, f"{context} urgency text")
    require_text_contains(session.get_next_goal_text(), goal_fragment, f"{context} next goal")
    require_text_contains(session.get_tutorial_hint_text(), hint_fragment, f"{context} tutorial hint")


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
        steak_order = ["Cooked_Meat"]
        salad_order = ["Chopped_Lettuce", "Chopped_Tomato"]
        lettuce_order = ["Bottom_Bun", "Cooked_Patty", "Chopped_Lettuce", "Top_Bun"]
        tomato_order = ["Bottom_Bun", "Cooked_Patty", "Chopped_Tomato", "Top_Bun"]
        meat_order = ["Bottom_Bun", "Cooked_Meat", "Chopped_Lettuce", "Top_Bun"]
        deluxe_order = ["Bottom_Bun", "Cooked_Patty", "Chopped_Lettuce", "Cooked_Meat", "Chopped_Tomato", "Top_Bun"]
        steak_salad_combo_order = ["Cooked_Meat", "Chopped_Lettuce", "Chopped_Tomato"]
        burger_salad_combo_order = ["Bottom_Bun", "Cooked_Patty", "Top_Bun", "Chopped_Lettuce", "Chopped_Tomato"]

        reset_session(session)
        assert_session_guidance(
            session,
            1,
            "基础汉堡",
            0,
            "节奏稳定",
            "经典汉堡",
            "经典汉堡",
            "initial guidance",
        )
        original_session_length = session_prop(session, "SessionLengthSeconds")
        session.set_editor_property("SessionLengthSeconds", 44.0)
        reset_session(session)
        assert_session_guidance(
            session,
            1,
            "基础汉堡",
            1,
            "注意时间",
            "经典汉堡",
            "注意时间",
            "warning guidance",
        )
        session.set_editor_property("SessionLengthSeconds", 19.0)
        reset_session(session)
        assert_session_guidance(
            session,
            1,
            "基础汉堡",
            2,
            "最后冲刺",
            "经典汉堡",
            "时间紧张",
            "critical guidance",
        )
        session.set_editor_property("SessionLengthSeconds", original_session_length)
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
        require(submit_tags(delivery_area, simple_order), "Target run first simple order should succeed")
        require(submit_tags(delivery_area, simple_order), "Target run second simple order should succeed")
        require(submit_tags(delivery_area, steak_order), "Target run third steak order should succeed")
        require(submit_tags(delivery_area, salad_order), "Target run fourth salad order should succeed")
        require(submit_tags(delivery_area, lettuce_order), "Target run fifth lettuce burger should succeed")
        assert_stats(session, 55, 5, 0, "mid-run score and streak bonus run")
        require(session_prop(session, "CurrentStreak") == 5, "Current streak should track five correct orders")
        require(session_prop(session, "BestStreak") == 5, "Best streak should track five correct orders")
        require(session.get_star_rating() == 2, f"Expected two-star rating at 55 points, got {session.get_star_rating()}")
        require(str(session.get_result_title()) == "继续练习", f"Expected in-progress title before target, got {session.get_result_title()}")
        require(str(session.get_result_grade_text()) == "二星", f"Expected two-star grade text, got {session.get_result_grade_text()}")
        require(not bool(session.get_editor_property("bMissionCleared")), "Mission should not clear before the full menu run")
        require(session.can_accept_orders(), "Session should keep accepting orders before the full menu target")
        print("PASS mid-run case: score, streak bonus, and partial rating work before target")

        reset_session(session)
        require(submit_tags(delivery_area, simple_order), "Extended run first simple order should succeed")
        require(submit_tags(delivery_area, simple_order), "Extended run second simple order should succeed")
        require(submit_tags(delivery_area, steak_order), "Extended run third steak order should succeed")
        require(submit_tags(delivery_area, salad_order), "Extended run fourth salad order should succeed")
        require(submit_tags(delivery_area, lettuce_order), "Extended run fifth lettuce burger should succeed")
        require(submit_tags(delivery_area, tomato_order), "Extended run sixth tomato burger should succeed")
        require(submit_tags(delivery_area, meat_order), "Extended run seventh thick meat order should succeed")
        require(submit_tags(delivery_area, deluxe_order), "Extended run eighth double meat order should succeed")
        require(submit_tags(delivery_area, steak_salad_combo_order), "Extended run ninth steak salad combo should succeed")
        require(submit_tags(delivery_area, burger_salad_combo_order), "Extended run tenth burger salad combo should succeed")
        assert_stats(session, 115, 10, 0, "extended steak salad combo and burger salad combo run")
        require(session_prop(session, "CurrentStreak") == 10, "Current streak should track ten correct orders")
        require(session_prop(session, "BestStreak") == 10, "Best streak should track ten correct orders")
        require(session.get_star_rating() == 3, f"Expected three-star rating at 115 points, got {session.get_star_rating()}")
        require(str(session.get_result_grade_text()) == "三星", f"Expected three-star grade text, got {session.get_result_grade_text()}")
        require(bool(session.get_editor_property("bMissionCleared")), "Extended run should clear mission at 115 points")
        print("PASS extended recipe case: steak, salad, thick meat, double meat, and combo orders work")

        reset_session(session)
        require(submit_tags(delivery_area, simple_order), "First simple order should succeed")
        require(submit_tags(delivery_area, simple_order), "Second simple order should succeed")
        assert_session_guidance(
            session,
            2,
            "牛排煎制",
            0,
            "节奏稳定",
            "香煎牛排",
            "香煎牛排",
            "steak stage guidance",
        )
        require(not submit_tags(delivery_area, simple_order), "Third simple order should fail after steak stage starts")
        require_text_contains(session.get_tutorial_hint_text(), "刚才出错", "failure recovery tutorial")
        require(not submit_tags(delivery_area, ["Raw_Meat"]), "Raw meat should fail for steak order")
        require(not submit_tags(delivery_area, ["Burnt_Meat"]), "Burnt meat should fail for steak order")
        require(submit_tags(delivery_area, steak_order), "Third progressive steak order should succeed")
        assert_session_guidance(
            session,
            3,
            "沙拉切配",
            0,
            "节奏稳定",
            "田园沙拉",
            "田园沙拉",
            "salad stage guidance",
        )
        require(not submit_tags(delivery_area, ["Raw_Lettuce", "Chopped_Tomato"]), "Raw lettuce should fail for salad order")
        require(not submit_tags(delivery_area, ["Chopped_Tomato", "Chopped_Lettuce"]), "Reversed salad order should fail")
        require(not submit_tags(delivery_area, ["Chopped_Lettuce", "Chopped_Tomato", "Top_Bun"]), "Salad with extra bun should fail")
        require(submit_tags(delivery_area, salad_order), "Fourth progressive salad order should succeed")
        assert_session_guidance(
            session,
            4,
            "生菜汉堡进阶",
            0,
            "节奏稳定",
            "切好的生菜",
            "生菜汉堡",
            "lettuce burger stage guidance",
        )
        require(session_prop(session, "CorrectOrders") == 4, "Four completed orders were not recorded")
        require(session_prop(session, "WrongOrders") == 6, "Steak and salad probe failures should be counted")
        require(session_prop(session, "SessionScore") == 28, f"Expected score 28 after steak and salad progression probes, got {session_prop(session, 'SessionScore')}")
        print("PASS progression case: steak and salad orders require processed ingredients")

        reset_session(session)
        require(submit_tags(delivery_area, simple_order), "Combo probe first simple order should succeed")
        require(submit_tags(delivery_area, simple_order), "Combo probe second simple order should succeed")
        require(submit_tags(delivery_area, steak_order), "Combo probe third steak order should succeed")
        require(submit_tags(delivery_area, salad_order), "Combo probe fourth salad order should succeed")
        require(submit_tags(delivery_area, lettuce_order), "Combo probe fifth lettuce burger should succeed")
        require(submit_tags(delivery_area, tomato_order), "Combo probe sixth tomato burger should succeed")
        require(submit_tags(delivery_area, meat_order), "Combo probe seventh thick meat order should succeed")
        require(submit_tags(delivery_area, deluxe_order), "Combo probe eighth double meat order should succeed")
        assert_session_guidance(
            session,
            8,
            "牛排沙拉套餐",
            0,
            "节奏稳定",
            "牛排和沙拉",
            "牛排沙拉套餐",
            "steak salad combo guidance",
        )
        require(not submit_tags(delivery_area, ["Cooked_Meat", "Chopped_Lettuce"]), "Steak salad combo missing tomato should fail")
        require(not submit_tags(delivery_area, ["Chopped_Lettuce", "Cooked_Meat", "Chopped_Tomato"]), "Steak salad combo wrong order should fail")
        require(not submit_tags(delivery_area, ["Cooked_Meat", "Chopped_Lettuce", "Chopped_Tomato", "Top_Bun"]), "Steak salad combo with extra bun should fail")
        require(submit_tags(delivery_area, steak_salad_combo_order), "Steak salad combo should succeed after probes")
        assert_session_guidance(
            session,
            9,
            "汉堡沙拉套餐",
            0,
            "节奏稳定",
            "经典汉堡沙拉套餐",
            "经典汉堡沙拉套餐",
            "burger salad combo guidance",
        )
        require(not submit_tags(delivery_area, simple_order), "Burger salad combo missing salad side should fail")
        require(not submit_tags(delivery_area, ["Bottom_Bun", "Cooked_Patty", "Chopped_Lettuce", "Top_Bun", "Chopped_Tomato"]), "Burger salad combo wrong order should fail")
        require(not submit_tags(delivery_area, ["Bottom_Bun", "Cooked_Patty", "Top_Bun", "Chopped_Lettuce", "Chopped_Tomato", "Cooked_Meat"]), "Burger salad combo with extra steak should fail")
        require(submit_tags(delivery_area, burger_salad_combo_order), "Burger salad combo should succeed after probes")
        assert_stats(session, 98, 10, 6, "combo order failure probes")
        require(not bool(session.get_editor_property("bMissionCleared")), "Combo probe run should not clear mission after deliberate penalties")
        print("PASS combo case: steak salad and burger salad combo orders reject missing, extra, and wrong-order submissions")

destroy_spawned()

if failures:
    raise RuntimeError("Demo gameplay validation failed: " + "; ".join(failures))

print("VRKitchen demo gameplay validation passed.")
