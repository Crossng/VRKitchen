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


def require_feedback_contains(session, fragment, context):
    require_text_contains(session_prop(session, "LastFeedbackMessage"), fragment, f"{context} feedback")


def submit_tags_expect_feedback(session, delivery_area, tags, expected_feedback_fragment, context):
    ok = submit_tags(delivery_area, tags)
    require(not ok, f"{context}: submission should fail")
    require_feedback_contains(session, expected_feedback_fragment, context)
    return ok


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


def assert_menu_progress(session, step, total, item_fragment, route_fragment, context):
    require(session.get_menu_route_total() == total, f"{context}: expected menu route total {total}, got {session.get_menu_route_total()}")
    require(session.get_current_menu_route_step() == step, f"{context}: expected menu step {step}, got {session.get_current_menu_route_step()}")
    require_text_contains(session.get_current_menu_item_text(), item_fragment, f"{context} current menu item")
    require_text_contains(session.get_menu_progress_text(), f"{step}/{total}", f"{context} menu progress")
    require_text_contains(session.get_menu_progress_text(), item_fragment, f"{context} menu progress item")
    require_text_contains(session.get_menu_route_text(), route_fragment, f"{context} menu route")


def assert_menu_route_health(session, context):
    report = session.get_demo_menu_route_quality_report_text()
    require(session.is_demo_menu_route_healthy(), f"{context}: demo menu route should be healthy\n{report}")
    require_text_contains(report, "菜单自检: 通过", f"{context} menu health report")
    require_text_contains(report, "菜单数量: 9", f"{context} menu health report")
    require_text_contains(report, "沙拉与套餐规则", f"{context} menu health report")


def assert_stage_coaching(session, orders_until_next, unlock_fragment, preview_fragment, path_fragment, context):
    require(session.get_correct_orders_until_next_stage() == orders_until_next, f"{context}: expected {orders_until_next} orders until next stage, got {session.get_correct_orders_until_next_stage()}")
    require_text_contains(session.get_current_stage_unlock_text(), unlock_fragment, f"{context} unlock text")
    require_text_contains(session.get_next_stage_preview_text(), preview_fragment, f"{context} next stage preview")
    require_text_contains(session.get_learning_path_text(), path_fragment, f"{context} learning path")
    require_text_contains(session.get_stage_coaching_text(), unlock_fragment, f"{context} coaching unlock")
    require_text_contains(session.get_stage_coaching_text(), preview_fragment, f"{context} coaching preview")
    require_text_contains(session.get_stage_coaching_text(), path_fragment, f"{context} coaching path")
    require_text_contains(session.get_player_objective_text(), preview_fragment, f"{context} objective stage preview")
    require_text_contains(session.get_tutorial_hint_text(), preview_fragment, f"{context} tutorial stage preview")


def assert_player_objective(session, ingredients_fragment, action_fragment, station_fragment, recovery_fragment, context):
    require_text_contains(session.get_current_required_ingredients_text(), ingredients_fragment, f"{context} required ingredients")
    require_text_contains(session.get_current_action_step_text(), action_fragment, f"{context} action step")
    require_text_contains(session.get_current_station_route_text(), station_fragment, f"{context} station route")
    require_text_contains(session.get_failure_recovery_text(), recovery_fragment, f"{context} recovery text")
    require_text_contains(session.get_player_objective_text(), ingredients_fragment, f"{context} objective ingredients")
    require_text_contains(session.get_player_objective_text(), action_fragment, f"{context} objective action")
    require_text_contains(session.get_player_objective_text(), station_fragment, f"{context} objective station route")
    require_text_contains(session.get_player_objective_text(), recovery_fragment, f"{context} objective recovery")


def assert_recipe_card(session, dish_type_fragment, process_fragment, assembly_fragment, warning_fragment, context):
    require_text_contains(session.get_current_dish_type_text(), dish_type_fragment, f"{context} dish type")
    require_text_contains(session.get_current_recipe_process_text(), process_fragment, f"{context} process")
    require_text_contains(session.get_current_recipe_assembly_text(), assembly_fragment, f"{context} assembly")
    require_text_contains(session.get_current_recipe_warning_text(), warning_fragment, f"{context} warning")
    require_text_contains(session.get_current_recipe_card_text(), dish_type_fragment, f"{context} recipe card dish type")
    require_text_contains(session.get_current_recipe_card_text(), process_fragment, f"{context} recipe card process")
    require_text_contains(session.get_current_recipe_card_text(), assembly_fragment, f"{context} recipe card assembly")
    require_text_contains(session.get_current_recipe_card_text(), warning_fragment, f"{context} recipe card warning")
    require_text_contains(session.get_player_objective_text(), dish_type_fragment, f"{context} objective recipe dish type")
    require_text_contains(session.get_tutorial_text(), dish_type_fragment, f"{context} tutorial recipe dish type")
    require_text_contains(session.get_tutorial_text(), warning_fragment, f"{context} tutorial recipe warning")
    require_text_contains(session.get_current_order_board_text(), dish_type_fragment, f"{context} order board dish type")
    require_text_contains(session.get_current_order_board_text(), process_fragment, f"{context} order board process")
    require_text_contains(session.get_current_order_board_text(), assembly_fragment, f"{context} order board assembly")
    require_text_contains(session.get_current_order_board_text(), warning_fragment, f"{context} order board warning")


def assert_pre_submit_checklist(session, *fragments, context):
    checklist = session.get_current_pre_submit_checklist_text()
    require_text_contains(checklist, "出餐前检查", f"{context} checklist title")
    require_text_contains(session.get_player_objective_text(), "出餐前检查", f"{context} objective checklist title")
    require_text_contains(session.get_current_order_board_text(), "出餐前检查", f"{context} order board checklist title")
    for fragment in fragments:
        require_text_contains(checklist, fragment, f"{context} checklist")
        require_text_contains(session.get_player_objective_text(), fragment, f"{context} objective checklist")
        require_text_contains(session.get_current_order_board_text(), fragment, f"{context} order board checklist")


def assert_station_outcome(session, *fragments, context):
    outcome = session.get_current_station_outcome_text()
    require_text_contains(outcome, "工位结果", f"{context} outcome title")
    require_text_contains(session.get_player_objective_text(), "工位结果", f"{context} objective outcome title")
    require_text_contains(session.get_current_order_board_text(), "工位结果", f"{context} order board outcome title")
    require_text_contains(session.get_tutorial_text(), "工位结果", f"{context} tutorial outcome title")
    for fragment in fragments:
        require_text_contains(outcome, fragment, f"{context} outcome")
        require_text_contains(session.get_player_objective_text(), fragment, f"{context} objective outcome")
        require_text_contains(session.get_current_order_board_text(), fragment, f"{context} order board outcome")
        require_text_contains(session.get_tutorial_text(), fragment, f"{context} tutorial outcome")


def assert_performance_summary(session, attempts, accuracy, accuracy_fragment, mistake_fragment, focus_fragment, context):
    require(session.get_total_order_attempts() == attempts, f"{context}: expected attempts {attempts}, got {session.get_total_order_attempts()}")
    require(session.get_accuracy_percent() == accuracy, f"{context}: expected accuracy {accuracy}, got {session.get_accuracy_percent()}")
    require_text_contains(session.get_accuracy_text(), accuracy_fragment, f"{context} accuracy text")
    require_text_contains(session.get_mistake_summary_text(), mistake_fragment, f"{context} mistake summary")
    require_text_contains(session.get_next_run_focus_text(), focus_fragment, f"{context} next run focus")
    require_text_contains(session.get_performance_summary_text(), accuracy_fragment, f"{context} performance accuracy")
    require_text_contains(session.get_performance_summary_text(), mistake_fragment, f"{context} performance mistakes")
    require_text_contains(session.get_performance_summary_text(), focus_fragment, f"{context} performance focus")


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
        assert_menu_route_health(session, "initial menu route health")
        simple_order = ["Bottom_Bun", "Cooked_Patty", "Top_Bun"]
        steak_order = ["Cooked_Meat"]
        salad_order = ["Chopped_Lettuce", "Chopped_Tomato", "Salad_Dressing"]
        lettuce_order = ["Bottom_Bun", "Cooked_Patty", "Chopped_Lettuce", "Top_Bun"]
        tomato_order = ["Bottom_Bun", "Cooked_Patty", "Chopped_Tomato", "Top_Bun"]
        meat_order = ["Bottom_Bun", "Cooked_Meat", "Chopped_Lettuce", "Top_Bun"]
        deluxe_order = ["Bottom_Bun", "Cooked_Patty", "Chopped_Lettuce", "Cooked_Meat", "Chopped_Tomato", "Top_Bun"]
        steak_salad_combo_order = ["Cooked_Meat", "Chopped_Lettuce", "Chopped_Tomato", "Salad_Dressing"]
        burger_salad_combo_order = ["Bottom_Bun", "Cooked_Patty", "Top_Bun", "Chopped_Lettuce", "Chopped_Tomato", "Salad_Dressing"]

        reset_session(session)
        assert_menu_progress(session, 1, 9, "经典汉堡", "经典汉堡 -> 2.香煎牛排", "initial menu progress")
        assert_stage_coaching(session, 2, "开局基础训练", "解锁 2/9「香煎牛排」", "1.经典汉堡[当前]", "initial stage coaching")
        assert_player_objective(session, "底部面包, 熟肉饼, 顶部面包", "煎熟肉饼", "面包台 -> 煎锅/灶台", "保持当前节奏", "initial player objective")
        assert_recipe_card(session, "汉堡 / 热菜", "肉饼必须用煎锅", "底部面包 -> 熟肉饼 -> 顶部面包", "生肉饼不能提交", "initial recipe card")
        assert_station_outcome(session, "面包台拿到底部面包", "生肉饼变成熟肉饼", "装盘区按三层叠好", context="initial station outcome")
        assert_pre_submit_checklist(session, "底部面包在最下方", "肉饼已经煎熟", "顶部面包最后盖上", context="initial pre-submit checklist")
        assert_performance_summary(session, 0, 0, "暂无提交", "没有错误订单", "第一单经典汉堡", "initial performance summary")
        require_text_contains(session.get_menu_route_text(), "田园沙拉", "menu route includes salad")
        require_text_contains(session.get_menu_route_text(), "经典汉堡沙拉套餐", "menu route includes final combo")
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
        require_feedback_contains(session, "出餐成功", "correct simple order")
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
        assert_performance_summary(session, 5, 100, "100% (5/5)", "没有错误订单", "推进到第 5/9 阶段", "mid-run performance summary")
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
        assert_performance_summary(session, 10, 100, "100% (10/10)", "没有错误订单", "已完成三星路线", "extended run performance summary")
        require(session.get_star_rating() == 3, f"Expected three-star rating at 115 points, got {session.get_star_rating()}")
        require(str(session.get_result_grade_text()) == "三星", f"Expected three-star grade text, got {session.get_result_grade_text()}")
        require(bool(session.get_editor_property("bMissionCleared")), "Extended run should clear mission at 115 points")
        require_text_contains(session.get_tutorial_hint_text(), "挑战完成", "completed run tutorial hint")
        require_text_contains(session.get_tutorial_hint_text(), "已完成三星路线", "completed run next focus")
        print("PASS extended recipe case: steak, salad, thick meat, double meat, and combo orders work")

        reset_session(session)
        require(submit_tags(delivery_area, simple_order), "First simple order should succeed")
        require(submit_tags(delivery_area, simple_order), "Second simple order should succeed")
        assert_menu_progress(session, 2, 9, "香煎牛排", "牛排沙拉套餐", "steak menu progress")
        assert_stage_coaching(session, 1, "已完成 2 单正确订单", "解锁 3/9「田园沙拉」", "2.香煎牛排[当前]", "steak stage coaching")
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
        require_text_contains(session.get_failure_recovery_text(), "清理盘子上的多余食材", "wrong dish recovery text")
        require_text_contains(session.get_player_objective_text(), "所需食材: 熟牛肉", "steak objective required ingredient")
        require_text_contains(session.get_player_objective_text(), "推荐步骤: 把生牛肉放进煎锅", "steak objective action")
        assert_recipe_card(session, "热菜 / 单品", "生牛肉必须", "熟牛肉单独装盘", "继续加热会烧焦", "steak recipe card")
        assert_station_outcome(session, "生牛肉区拿到生牛肉", "生牛肉变成熟牛肉", "装盘区只放熟牛肉", context="steak station outcome")
        assert_pre_submit_checklist(session, "盘上只有熟牛肉", "没有生牛肉或烧焦牛肉", "熟了就离开灶台", context="steak pre-submit checklist")
        submit_tags_expect_feedback(session, delivery_area, ["Raw_Meat"], "牛肉还没煎熟", "raw meat steak order")
        require_text_contains(session.get_failure_recovery_text(), "确认煎锅在灶台上", "raw meat recovery text")
        submit_tags_expect_feedback(session, delivery_area, ["Burnt_Meat"], "牛肉烧焦了", "burnt meat steak order")
        require_text_contains(session.get_failure_recovery_text(), "丢弃烧焦食材", "burnt meat recovery text")
        require(submit_tags(delivery_area, steak_order), "Third progressive steak order should succeed")
        assert_menu_progress(session, 3, 9, "田园沙拉", "汉堡沙拉套餐", "salad menu progress")
        assert_stage_coaching(session, 1, "已完成 3 单正确订单", "解锁 4/9「生菜汉堡」", "3.田园沙拉[当前]", "salad stage coaching")
        assert_player_objective(session, "切好的生菜, 切好的番茄, 沙拉酱", "先切生菜", "冷菜，不用煎锅", "保持当前节奏", "salad player objective")
        assert_recipe_card(session, "冷菜 / 沙拉", "最后加入沙拉酱", "切好的生菜 -> 切好的番茄 -> 沙拉酱", "缺少沙拉酱不能提交", "salad recipe card")
        assert_station_outcome(session, "切菜板产出切好的生菜", "调味区拿到沙拉酱", "冷菜直接装盘不进煎锅", context="salad station outcome")
        assert_pre_submit_checklist(session, "生菜和番茄都已切好", "沙拉酱已加入", "顺序是切好的生菜、切好的番茄、沙拉酱", context="salad pre-submit checklist")
        require_text_contains(session.get_current_station_route_text(), "蔬菜区 -> 切菜板 -> 调味区 -> 装盘区 -> 出餐区", "salad station route path")
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
        submit_tags_expect_feedback(session, delivery_area, ["Raw_Lettuce", "Chopped_Tomato"], "生菜还没切", "raw lettuce salad order")
        require_text_contains(session.get_failure_recovery_text(), "切菜板处理", "raw lettuce recovery text")
        submit_tags_expect_feedback(session, delivery_area, ["Chopped_Lettuce", "Raw_Tomato", "Salad_Dressing"], "番茄还没切", "raw tomato salad order")
        submit_tags_expect_feedback(session, delivery_area, ["Chopped_Lettuce", "Chopped_Tomato"], "缺少食材：沙拉酱", "salad missing dressing")
        submit_tags_expect_feedback(session, delivery_area, ["Chopped_Lettuce", "Salad_Dressing", "Chopped_Tomato"], "沙拉顺序错误", "salad dressing wrong order")
        submit_tags_expect_feedback(session, delivery_area, ["Chopped_Tomato", "Chopped_Lettuce", "Salad_Dressing"], "沙拉顺序错误", "reversed salad order")
        require_text_contains(session.get_failure_recovery_text(), "重新叠放", "salad order recovery text")
        submit_tags_expect_feedback(session, delivery_area, ["Chopped_Lettuce", "Chopped_Tomato", "Salad_Dressing", "Top_Bun"], "多了食材：顶部面包", "salad with extra bun")
        require_text_contains(session.get_failure_recovery_text(), "清理盘子上的多余食材", "extra food recovery text")
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
        require(session_prop(session, "WrongOrders") == 9, "Steak and salad probe failures should be counted")
        require(session_prop(session, "SessionScore") == 22, f"Expected score 22 after steak and salad progression probes, got {session_prop(session, 'SessionScore')}")
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
        assert_menu_progress(session, 8, 9, "牛排沙拉套餐", "经典汉堡沙拉套餐", "steak salad combo menu progress")
        assert_stage_coaching(session, 1, "已完成 8 单正确订单", "解锁 9/9「经典汉堡沙拉套餐」", "8.牛排沙拉套餐[当前]", "steak salad combo stage coaching")
        assert_player_objective(session, "熟牛肉, 切好的生菜, 切好的番茄, 沙拉酱", "先煎熟牛肉", "先热菜，再冷菜配菜", "保持当前节奏", "steak salad combo player objective")
        assert_recipe_card(session, "套餐 / 热菜加冷菜", "沙拉酱最后加入", "熟牛肉 -> 切好的生菜 -> 切好的番茄 -> 沙拉酱", "缺少配菜或沙拉酱会失败", "steak salad combo recipe card")
        assert_station_outcome(session, "煎锅/灶台产出熟牛肉", "调味区拿到沙拉酱", "先放热菜再放冷菜配菜", context="steak salad combo station outcome")
        assert_pre_submit_checklist(session, "牛肉已经煎熟且没有烧焦", "沙拉酱已加入", "套餐顺序是熟牛肉、生菜、番茄、沙拉酱", context="steak salad combo pre-submit checklist")
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
        submit_tags_expect_feedback(session, delivery_area, ["Cooked_Meat", "Chopped_Lettuce"], "套餐缺少配菜：切好的番茄, 沙拉酱", "steak salad combo missing tomato")
        submit_tags_expect_feedback(session, delivery_area, ["Cooked_Meat", "Chopped_Lettuce", "Chopped_Tomato"], "套餐缺少配菜：沙拉酱", "steak salad combo missing dressing")
        submit_tags_expect_feedback(session, delivery_area, ["Chopped_Lettuce", "Cooked_Meat", "Chopped_Tomato", "Salad_Dressing"], "套餐顺序错误：先放熟牛肉", "steak salad combo wrong order")
        submit_tags_expect_feedback(session, delivery_area, ["Cooked_Meat", "Chopped_Lettuce", "Chopped_Tomato", "Salad_Dressing", "Top_Bun"], "套餐多了食材：顶部面包", "steak salad combo with extra bun")
        require(submit_tags(delivery_area, steak_salad_combo_order), "Steak salad combo should succeed after probes")
        assert_menu_progress(session, 9, 9, "经典汉堡沙拉套餐", "牛排沙拉套餐", "burger salad combo menu progress")
        assert_stage_coaching(session, 0, "已完成 9 单正确订单", "已到最终菜单", "9.经典汉堡沙拉套餐[当前]", "burger salad combo stage coaching")
        assert_player_objective(session, "底部面包, 熟肉饼, 顶部面包, 切好的生菜, 切好的番茄, 沙拉酱", "先叠完整经典汉堡", "先完成汉堡，再补冷菜配菜", "保持当前节奏", "burger salad combo player objective")
        assert_recipe_card(session, "套餐 / 汉堡加沙拉", "沙拉酱最后加入", "顶部面包 -> 切好的生菜 -> 切好的番茄 -> 沙拉酱", "不能把蔬菜或沙拉酱夹进汉堡中间", "burger salad combo recipe card")
        assert_station_outcome(session, "先产出完整经典汉堡", "调味区拿到沙拉酱", "最后补沙拉配菜", context="burger salad combo station outcome")
        assert_pre_submit_checklist(session, "先确认经典汉堡完整", "沙拉酱已加入", "沙拉配菜放在顶部面包之后", context="burger salad combo pre-submit checklist")
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
        submit_tags_expect_feedback(session, delivery_area, simple_order, "套餐缺少配菜：切好的生菜, 切好的番茄, 沙拉酱", "burger salad combo missing salad side")
        submit_tags_expect_feedback(session, delivery_area, ["Bottom_Bun", "Cooked_Patty", "Top_Bun", "Chopped_Lettuce", "Chopped_Tomato"], "套餐缺少配菜：沙拉酱", "burger salad combo missing dressing")
        submit_tags_expect_feedback(session, delivery_area, ["Bottom_Bun", "Cooked_Patty", "Chopped_Lettuce", "Top_Bun", "Chopped_Tomato", "Salad_Dressing"], "套餐顺序错误：先完成经典汉堡", "burger salad combo wrong order")
        submit_tags_expect_feedback(session, delivery_area, ["Bottom_Bun", "Cooked_Patty", "Top_Bun", "Chopped_Lettuce", "Chopped_Tomato", "Salad_Dressing", "Cooked_Meat"], "套餐多了食材：熟牛肉", "burger salad combo with extra steak")
        require(submit_tags(delivery_area, burger_salad_combo_order), "Burger salad combo should succeed after probes")
        assert_stats(session, 94, 10, 8, "combo order failure probes")
        assert_performance_summary(session, 18, 56, "56% (10/18)", "共 8 次错误", "菜单路线已经跑完", "combo probe performance summary")
        require(not bool(session.get_editor_property("bMissionCleared")), "Combo probe run should not clear mission after deliberate penalties")
        print("PASS combo case: steak salad and burger salad combo orders reject missing, extra, and wrong-order submissions")

destroy_spawned()

if failures:
    raise RuntimeError("Demo gameplay validation failed: " + "; ".join(failures))

print("VRKitchen demo gameplay validation passed.")
