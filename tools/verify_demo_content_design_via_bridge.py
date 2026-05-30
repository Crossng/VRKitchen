import json

import unreal
from unreal_bridge import Editor


LEVEL_PATH = "/Game/_Project/Maps/VRKitchen_Demo"
TEST_ACTOR_LABEL_PREFIX = "AUTO_TEST_CONTENT_"

EXPECTED_MENU = [
    {
        "unlock_count": 0,
        "name": "经典汉堡",
        "tags": ["Bottom_Bun", "Cooked_Patty", "Top_Bun"],
        "details": "底部面包, 熟肉饼, 顶部面包",
        "stage": "基础汉堡训练",
        "dish_type": "汉堡 / 热菜",
        "process": "肉饼必须用煎锅和灶台煎熟",
        "assembly": "底部面包 -> 熟肉饼 -> 顶部面包",
        "warning": "生肉饼不能提交",
        "action": "先取底部面包",
        "route": "面包台 -> 煎锅/灶台 -> 装盘区 -> 出餐区",
        "outcomes": ["面包台拿到底部面包和顶部面包", "煎锅/灶台把生肉饼变成熟肉饼"],
        "checklist": ["底部面包在最下方", "肉饼已经煎熟", "顶部面包最后盖上"],
        "next_goal": "先稳定完成 2 单经典汉堡",
    },
    {
        "unlock_count": 2,
        "name": "香煎牛排",
        "tags": ["Cooked_Meat"],
        "details": "熟牛肉",
        "stage": "牛排煎制",
        "dish_type": "热菜 / 单品",
        "process": "生牛肉必须在煎锅/灶台上煎成熟牛肉",
        "assembly": "熟牛肉单独装盘",
        "warning": "继续加热会烧焦",
        "action": "把生牛肉放进煎锅",
        "route": "生牛肉区 -> 煎锅/灶台 -> 装盘区 -> 出餐区",
        "outcomes": ["生牛肉区拿到生牛肉", "生牛肉变成熟牛肉"],
        "checklist": ["盘上只有熟牛肉", "没有生牛肉或烧焦牛肉", "熟了就离开灶台"],
        "next_goal": "用煎锅和灶台做香煎牛排",
    },
    {
        "unlock_count": 3,
        "name": "田园沙拉",
        "tags": ["Chopped_Lettuce", "Chopped_Tomato", "Salad_Dressing"],
        "details": "切好的生菜, 切好的番茄, 沙拉酱",
        "stage": "沙拉切配",
        "dish_type": "冷菜 / 沙拉",
        "process": "生菜和番茄都要先在切菜板切好，最后加入沙拉酱，不用煎锅",
        "assembly": "切好的生菜 -> 切好的番茄 -> 沙拉酱",
        "warning": "未切蔬菜或缺少沙拉酱不能提交，沙拉顺序不能颠倒",
        "action": "先切生菜",
        "route": "蔬菜区 -> 切菜板 -> 调味区 -> 装盘区 -> 出餐区",
        "outcomes": ["切菜板产出切好的生菜和切好的番茄", "调味区拿到沙拉酱", "冷菜直接装到盘子上"],
        "checklist": ["生菜和番茄都已切好", "沙拉酱已加入", "沙拉也在盘子上装好", "顺序是切好的生菜、切好的番茄、沙拉酱"],
        "plate": "沙拉也必须先在盘子上装好",
        "next_goal": "切生菜和番茄，加沙拉酱做田园沙拉",
    },
    {
        "unlock_count": 4,
        "name": "生菜汉堡",
        "tags": ["Bottom_Bun", "Cooked_Patty", "Chopped_Lettuce", "Top_Bun"],
        "details": "底部面包, 熟肉饼, 切好的生菜, 顶部面包",
        "stage": "生菜汉堡进阶",
        "dish_type": "汉堡 / 热菜加蔬菜",
        "process": "肉饼要煎熟，生菜要切好",
        "assembly": "底部面包 -> 熟肉饼 -> 切好的生菜 -> 顶部面包",
        "warning": "生菜未切或把生菜放到肉饼下面都会失败",
        "action": "加入切好的生菜",
        "route": "面包台 -> 煎锅/灶台 -> 切菜板 -> 装盘区 -> 出餐区",
        "outcomes": ["切菜板产出切好的生菜", "装盘区把生菜放在肉饼上方"],
        "checklist": ["肉饼已经煎熟", "生菜已经切好", "顺序是底部面包、熟肉饼、切好的生菜、顶部面包"],
        "next_goal": "把切好的生菜加入汉堡",
    },
    {
        "unlock_count": 5,
        "name": "番茄汉堡",
        "tags": ["Bottom_Bun", "Cooked_Patty", "Chopped_Tomato", "Top_Bun"],
        "details": "底部面包, 熟肉饼, 切好的番茄, 顶部面包",
        "stage": "番茄切配",
        "dish_type": "汉堡 / 热菜加蔬菜",
        "process": "肉饼要煎熟，番茄要切好",
        "assembly": "底部面包 -> 熟肉饼 -> 切好的番茄 -> 顶部面包",
        "warning": "番茄未切或把顶部面包提前放下都会失败",
        "action": "加入切好的番茄",
        "route": "面包台 -> 煎锅/灶台 -> 切菜板 -> 装盘区 -> 出餐区",
        "outcomes": ["切菜板产出切好的番茄", "装盘区把番茄放在肉饼上方"],
        "checklist": ["肉饼已经煎熟", "番茄已经切好", "顶部面包必须最后放"],
        "next_goal": "切番茄，注意不要换顺序",
    },
    {
        "unlock_count": 6,
        "name": "厚肉生菜堡",
        "tags": ["Bottom_Bun", "Cooked_Meat", "Chopped_Lettuce", "Top_Bun"],
        "details": "底部面包, 熟牛肉, 切好的生菜, 顶部面包",
        "stage": "厚肉煎制",
        "dish_type": "汉堡 / 厚肉热菜",
        "process": "牛肉要煎成熟牛肉，生菜要切好",
        "assembly": "底部面包 -> 熟牛肉 -> 切好的生菜 -> 顶部面包",
        "warning": "生牛肉和烧焦牛肉不能提交，熟牛肉要及时离火",
        "action": "牛肉煎熟",
        "route": "面包台 -> 煎锅/灶台 -> 切菜板 -> 装盘区 -> 出餐区",
        "outcomes": ["煎锅/灶台把生牛肉变成熟牛肉", "切菜板产出切好的生菜"],
        "checklist": ["牛肉是熟牛肉不是生牛肉或烧焦牛肉", "生菜已经切好", "熟牛肉及时离火"],
        "next_goal": "煎熟牛肉再提交厚肉堡",
    },
    {
        "unlock_count": 7,
        "name": "豪华双肉堡",
        "tags": ["Bottom_Bun", "Cooked_Patty", "Chopped_Lettuce", "Cooked_Meat", "Chopped_Tomato", "Top_Bun"],
        "details": "底部面包, 熟肉饼, 切好的生菜, 熟牛肉, 切好的番茄, 顶部面包",
        "stage": "豪华双肉挑战",
        "dish_type": "汉堡 / 双肉挑战",
        "process": "肉饼和牛肉都要煎熟，生菜和番茄都要切好",
        "assembly": "底部面包 -> 熟肉饼 -> 切好的生菜 -> 熟牛肉 -> 切好的番茄 -> 顶部面包",
        "warning": "双肉和蔬菜层级不能跳层或调换顺序",
        "action": "按顺序放底部面包",
        "route": "面包台 -> 煎锅/灶台 -> 切菜板 -> 装盘区 -> 出餐区",
        "outcomes": ["煎锅/灶台产出熟肉饼和熟牛肉", "切菜板产出切好的生菜和切好的番茄"],
        "checklist": ["肉饼和牛肉都已煎熟", "生菜和番茄都已切好", "双肉和蔬菜层级不能调换"],
        "next_goal": "完成豪华双肉堡，准备套餐挑战",
    },
    {
        "unlock_count": 8,
        "name": "牛排沙拉套餐",
        "tags": ["Cooked_Meat", "Chopped_Lettuce", "Chopped_Tomato", "Salad_Dressing"],
        "details": "熟牛肉, 切好的生菜, 切好的番茄, 沙拉酱",
        "stage": "牛排沙拉套餐",
        "dish_type": "套餐 / 热菜加冷菜",
        "process": "牛肉要煎熟，生菜和番茄要切好，沙拉酱最后加入",
        "assembly": "熟牛肉 -> 切好的生菜 -> 切好的番茄 -> 沙拉酱",
        "warning": "套餐先热菜后冷菜，缺少配菜或沙拉酱会失败",
        "action": "先煎熟牛肉",
        "route": "生牛肉区 -> 煎锅/灶台 -> 切菜板 -> 调味区 -> 装盘区 -> 出餐区",
        "outcomes": ["煎锅/灶台产出熟牛肉", "调味区拿到沙拉酱", "盘子上先放热菜再放冷菜配菜"],
        "checklist": ["牛肉已经煎熟且没有烧焦", "沙拉酱已加入", "所有内容都在盘子上", "套餐顺序是熟牛肉、生菜、番茄、沙拉酱"],
        "plate": "沙拉也必须先在盘子上装好",
        "next_goal": "把牛排和沙拉按套餐顺序出餐",
    },
    {
        "unlock_count": 9,
        "name": "经典汉堡沙拉套餐",
        "tags": ["Bottom_Bun", "Cooked_Patty", "Top_Bun", "Chopped_Lettuce", "Chopped_Tomato", "Salad_Dressing"],
        "details": "底部面包, 熟肉饼, 顶部面包, 切好的生菜, 切好的番茄, 沙拉酱",
        "stage": "汉堡沙拉套餐",
        "dish_type": "套餐 / 汉堡加沙拉",
        "process": "肉饼要煎熟，生菜和番茄要切好，沙拉酱最后加入",
        "assembly": "底部面包 -> 熟肉饼 -> 顶部面包 -> 切好的生菜 -> 切好的番茄 -> 沙拉酱",
        "warning": "不能把蔬菜或沙拉酱夹进汉堡中间",
        "action": "先叠完整经典汉堡",
        "route": "面包台 -> 煎锅/灶台 -> 切菜板 -> 调味区 -> 装盘区 -> 出餐区",
        "outcomes": ["先产出完整经典汉堡", "调味区拿到沙拉酱", "同一个盘子上最后补沙拉配菜"],
        "checklist": ["先确认经典汉堡完整", "沙拉酱已加入", "汉堡和沙拉配菜都在盘子上", "沙拉配菜放在顶部面包之后"],
        "plate": "沙拉也必须先在盘子上装好",
        "next_goal": "完成经典汉堡沙拉套餐冲三星",
    },
]

EXPECTED_MENU_TOTAL = len(EXPECTED_MENU)


Editor.load_level(level_path=LEVEL_PATH, prompt_save_changes=False)

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
failures = []
spawned_actors = []


def require(condition, message):
    if not condition:
        failures.append(message)


def require_text_contains(value, fragment, context):
    text = str(value)
    require(fragment in text, f"{context}: expected '{fragment}' in '{text}'")


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
            try:
                actor.destroy_actor()
            except Exception:
                pass


def spawn_food_stack(delivery_area, tags):
    stack_center = find_component_by_name(delivery_area, "StackCenter", unreal.SceneComponent)
    require(stack_center is not None, "Delivery area lacks StackCenter component")
    if not stack_center:
        return

    base_location = delivery_area.get_actor_location()
    for index, tag in enumerate(tags):
        location = unreal.Vector(base_location.x, base_location.y, base_location.z + 8.0 + index * 8.0)
        actor = subsys.spawn_actor_from_class(unreal.Actor, location)
        require(actor is not None, f"Failed to spawn content design food actor for {tag}")
        if not actor:
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


def submit_tags(delivery_area, tags):
    destroy_spawned()
    spawn_food_stack(delivery_area, tags)
    result = unreal.VRKitchenOrderValidationLibrary.submit_current_plate_validated(delivery_area)
    destroy_spawned()
    return bool(result)


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
    require_text_contains(report, "沙拉与套餐盘装规则", f"{context} menu health report")


def assert_stage_coaching(session, orders_until_next, unlock_fragment, preview_fragment, path_fragment, context):
    require(session.get_correct_orders_until_next_stage() == orders_until_next, f"{context}: expected {orders_until_next} orders until next stage, got {session.get_correct_orders_until_next_stage()}")
    require_text_contains(session.get_current_stage_unlock_text(), unlock_fragment, f"{context} unlock text")
    require_text_contains(session.get_next_stage_preview_text(), preview_fragment, f"{context} next stage preview")
    require_text_contains(session.get_learning_path_text(), path_fragment, f"{context} learning path")
    require_text_contains(session.get_stage_coaching_text(), unlock_fragment, f"{context} coaching unlock")
    require_text_contains(session.get_stage_coaching_text(), preview_fragment, f"{context} coaching preview")
    require_text_contains(session.get_stage_coaching_text(), path_fragment, f"{context} coaching path")
    require_text_contains(session.get_player_objective_text(), preview_fragment.split("「")[0].replace("解锁 ", "").strip(), f"{context} objective stage preview")
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
    require_text_contains(session.get_current_order_quick_card_text(), "订单速查", f"{context} quick card title")
    require_text_contains(session.get_current_order_quick_card_text(), ingredients_fragment, f"{context} quick card ingredients")
    require_text_contains(session.get_current_order_quick_card_text(), action_fragment, f"{context} quick card action")
    require_text_contains(session.get_current_order_quick_card_text(), recovery_fragment, f"{context} quick card recovery")
    require_text_contains(session.get_current_plate_assembly_guide_text(), "盘", f"{context} plate assembly guide")
    require_text_contains(session.get_current_order_quick_card_text(), "盘子", f"{context} quick card plating")


def assert_recipe_card(session, dish_type_fragment, process_fragment, assembly_fragment, warning_fragment, context):
    require_text_contains(session.get_current_dish_type_text(), dish_type_fragment, f"{context} dish type")
    require_text_contains(session.get_current_recipe_process_text(), process_fragment, f"{context} process")
    require_text_contains(session.get_current_recipe_assembly_text(), assembly_fragment, f"{context} assembly")
    require_text_contains(session.get_current_recipe_warning_text(), warning_fragment, f"{context} warning")
    require_text_contains(session.get_current_recipe_card_text(), dish_type_fragment, f"{context} recipe card dish type")
    require_text_contains(session.get_current_recipe_card_text(), process_fragment, f"{context} recipe card process")
    require_text_contains(session.get_current_recipe_card_text(), assembly_fragment, f"{context} recipe card assembly")
    require_text_contains(session.get_current_recipe_card_text(), warning_fragment, f"{context} recipe card warning")
    require_text_contains(session.get_tutorial_text(), dish_type_fragment, f"{context} tutorial recipe dish type")
    require_text_contains(session.get_tutorial_text(), warning_fragment, f"{context} tutorial recipe warning")
    require_text_contains(session.get_current_order_board_text(), dish_type_fragment, f"{context} order board dish type")
    require_text_contains(session.get_current_order_board_text(), process_fragment, f"{context} order board process")
    require_text_contains(session.get_current_order_board_text(), assembly_fragment, f"{context} order board assembly")
    require_text_contains(session.get_current_order_board_text(), warning_fragment, f"{context} order board warning")


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


def assert_pre_submit_checklist(session, *fragments, context):
    checklist = session.get_current_pre_submit_checklist_text()
    require_text_contains(checklist, "出餐前检查", f"{context} checklist title")
    require_text_contains(session.get_player_objective_text(), "出餐前检查", f"{context} objective checklist title")
    require_text_contains(session.get_current_order_board_text(), "出餐前检查", f"{context} order board checklist title")
    for fragment in fragments:
        require_text_contains(checklist, fragment, f"{context} checklist")
        require_text_contains(session.get_player_objective_text(), fragment, f"{context} objective checklist")
        require_text_contains(session.get_current_order_board_text(), fragment, f"{context} order board checklist")


def assert_performance_summary(session, attempts, accuracy, accuracy_fragment, mistake_fragment, focus_fragment, context):
    require(session.get_total_order_attempts() == attempts, f"{context}: expected attempts {attempts}, got {session.get_total_order_attempts()}")
    require(session.get_accuracy_percent() == accuracy, f"{context}: expected accuracy {accuracy}, got {session.get_accuracy_percent()}")
    require_text_contains(session.get_accuracy_text(), accuracy_fragment, f"{context} accuracy text")
    require_text_contains(session.get_mistake_summary_text(), mistake_fragment, f"{context} mistake summary")
    require_text_contains(session.get_next_run_focus_text(), focus_fragment, f"{context} next run focus")
    require_text_contains(session.get_performance_summary_text(), accuracy_fragment, f"{context} performance accuracy")
    require_text_contains(session.get_performance_summary_text(), mistake_fragment, f"{context} performance mistakes")
    require_text_contains(session.get_performance_summary_text(), focus_fragment, f"{context} performance focus")


def assert_menu_step_texts(session, step_index, spec, context):
    require(session.get_current_menu_route_step() == step_index + 1, f"{context}: wrong current menu step")
    require_text_contains(session.get_menu_progress_text(), f"{step_index + 1}/{EXPECTED_MENU_TOTAL}", f"{context} menu progress")
    require_text_contains(session.get_current_menu_item_text(), spec["name"], f"{context} item name")
    require_text_contains(session.get_current_menu_item_text(), spec["details"], f"{context} item details")
    require_text_contains(session.get_order_stage_text(), spec["stage"], f"{context} stage text")
    require_text_contains(session.get_current_required_ingredients_text(), spec["details"], f"{context} required ingredients")
    require_text_contains(session.get_current_action_step_text(), spec["action"], f"{context} action")
    require_text_contains(session.get_current_station_route_text(), spec["route"], f"{context} station route")
    require_text_contains(session.get_current_station_outcome_text(), spec["outcomes"][0], f"{context} station outcome 1")
    if len(spec["outcomes"]) > 1:
        require_text_contains(session.get_current_station_outcome_text(), spec["outcomes"][1], f"{context} station outcome 2")
    for fragment in spec["checklist"]:
        require_text_contains(session.get_current_pre_submit_checklist_text(), fragment, f"{context} checklist")
        require_text_contains(session.get_current_order_quick_card_text(), fragment, f"{context} quick card checklist")
    if "plate" in spec:
        require_text_contains(session.get_current_plate_assembly_guide_text(), spec["plate"], f"{context} plate guide")
        require_text_contains(session.get_player_objective_text(), spec["plate"], f"{context} objective plate guide")
        require_text_contains(session.get_current_order_board_text(), spec["plate"], f"{context} order board plate guide")
        require_text_contains(session.get_current_order_quick_card_text(), spec["plate"], f"{context} quick card plate guide")
        require_text_contains(session.get_tutorial_text(), spec["plate"], f"{context} tutorial plate guide")
    require_text_contains(session.get_current_dish_type_text(), spec["dish_type"], f"{context} dish type")
    require_text_contains(session.get_current_recipe_process_text(), spec["process"], f"{context} process")
    require_text_contains(session.get_current_recipe_assembly_text(), spec["assembly"], f"{context} assembly")
    require_text_contains(session.get_current_recipe_warning_text(), spec["warning"], f"{context} warning")
    require_text_contains(session.get_current_recipe_card_text(), spec["name"], f"{context} recipe card name")
    require_text_contains(session.get_current_recipe_card_text(), spec["details"], f"{context} recipe card details")
    require_text_contains(session.get_current_order_board_text(), spec["name"], f"{context} order board name")
    require_text_contains(session.get_current_order_board_text(), spec["details"], f"{context} order board details")
    require_text_contains(session.get_current_order_board_text(), spec["action"], f"{context} order board action")
    require_text_contains(session.get_current_order_board_text(), spec["next_goal"], f"{context} order board next goal")
    require_text_contains(session.get_current_order_quick_card_text(), f"{step_index + 1}/{EXPECTED_MENU_TOTAL}", f"{context} quick card progress")
    require_text_contains(session.get_current_order_quick_card_text(), spec["name"], f"{context} quick card name")
    require_text_contains(session.get_player_objective_text(), spec["details"], f"{context} objective ingredients")
    require_text_contains(session.get_player_objective_text(), spec["action"], f"{context} objective action")
    require_text_contains(session.get_player_objective_text(), spec["route"], f"{context} objective route")
    require_text_contains(session.get_player_objective_text(), "保持当前节奏", f"{context} objective recovery")
    require_text_contains(session.get_tutorial_text(), spec["dish_type"], f"{context} tutorial dish type")
    require_text_contains(session.get_tutorial_text(), spec["warning"], f"{context} tutorial warning")


def validate_current_stage(session, spec, step_index, context):
    if step_index == 0:
        assert_menu_progress(session, 1, EXPECTED_MENU_TOTAL, "经典汉堡", "经典汉堡 -> 2.香煎牛排", context)
        assert_stage_coaching(session, 2, "开局基础训练", "解锁 2/9「香煎牛排」", "1.经典汉堡[当前]", context)
        assert_player_objective(session, "底部面包, 熟肉饼, 顶部面包", "煎熟肉饼", "面包台 -> 煎锅/灶台", "保持当前节奏", context)
        assert_recipe_card(session, "汉堡 / 热菜", "肉饼必须用煎锅", "底部面包 -> 熟肉饼 -> 顶部面包", "生肉饼不能提交", context)
        assert_station_outcome(session, "面包台拿到底部面包", "生肉饼变成熟肉饼", "装盘区按三层叠好", context=context)
        assert_pre_submit_checklist(session, "底部面包在最下方", "肉饼已经煎熟", "顶部面包最后盖上", context=context)
        require_text_contains(session.get_tutorial_hint_text(), "解锁 2/9「香煎牛排」", f"{context} tutorial hint")
    elif step_index == 1:
        assert_menu_progress(session, 2, EXPECTED_MENU_TOTAL, "香煎牛排", "牛排沙拉套餐", context)
        assert_stage_coaching(session, 1, "已完成 2 单正确订单", "解锁 3/9「田园沙拉」", "2.香煎牛排[当前]", context)
        assert_player_objective(session, "熟牛肉", "把生牛肉放进煎锅", "生牛肉区 -> 煎锅/灶台", "保持当前节奏", context)
        assert_recipe_card(session, "热菜 / 单品", "生牛肉必须", "熟牛肉单独装盘", "继续加热会烧焦", context)
        assert_station_outcome(session, "生牛肉区拿到生牛肉", "生牛肉变成熟牛肉", "装盘区只放熟牛肉", context=context)
        assert_pre_submit_checklist(session, "盘上只有熟牛肉", "没有生牛肉或烧焦牛肉", "熟了就离开灶台", context=context)
        require_text_contains(session.get_tutorial_hint_text(), "解锁 3/9「田园沙拉」", f"{context} tutorial hint")
    elif step_index == 2:
        assert_menu_progress(session, 3, EXPECTED_MENU_TOTAL, "田园沙拉", "汉堡沙拉套餐", context)
        assert_stage_coaching(session, 1, "已完成 3 单正确订单", "解锁 4/9「生菜汉堡」", "3.田园沙拉[当前]", context)
        assert_player_objective(session, "切好的生菜, 切好的番茄, 沙拉酱", "先切生菜", "蔬菜区 -> 切菜板 -> 调味区", "保持当前节奏", context)
        assert_recipe_card(session, "冷菜 / 沙拉", "最后加入沙拉酱", "切好的生菜 -> 切好的番茄 -> 沙拉酱", "缺少沙拉酱不能提交", context)
        assert_station_outcome(session, "切菜板产出切好的生菜", "调味区拿到沙拉酱", "冷菜直接装到盘子上", context=context)
        assert_pre_submit_checklist(session, "生菜和番茄都已切好", "沙拉酱已加入", "沙拉也在盘子上装好", "顺序是切好的生菜、切好的番茄、沙拉酱", context=context)
        require_text_contains(session.get_current_plate_assembly_guide_text(), "沙拉也必须先在盘子上装好", f"{context} plate guide")
        require_text_contains(session.get_tutorial_hint_text(), "解锁 4/9「生菜汉堡」", f"{context} tutorial hint")
    elif step_index == 7:
        assert_menu_progress(session, 8, EXPECTED_MENU_TOTAL, "牛排沙拉套餐", "经典汉堡沙拉套餐", context)
        assert_stage_coaching(session, 1, "已完成 8 单正确订单", "解锁 9/9「经典汉堡沙拉套餐」", "8.牛排沙拉套餐[当前]", context)
        assert_player_objective(session, "熟牛肉, 切好的生菜, 切好的番茄, 沙拉酱", "先煎熟牛肉", "生牛肉区 -> 煎锅/灶台", "保持当前节奏", context)
        assert_recipe_card(session, "套餐 / 热菜加冷菜", "沙拉酱最后加入", "熟牛肉 -> 切好的生菜 -> 切好的番茄 -> 沙拉酱", "缺少配菜或沙拉酱会失败", context)
        assert_station_outcome(session, "煎锅/灶台产出熟牛肉", "调味区拿到沙拉酱", "盘子上先放热菜再放冷菜配菜", context=context)
        assert_pre_submit_checklist(session, "牛肉已经煎熟且没有烧焦", "沙拉酱已加入", "所有内容都在盘子上", "套餐顺序是熟牛肉、生菜、番茄、沙拉酱", context=context)
        require_text_contains(session.get_current_plate_assembly_guide_text(), "沙拉也必须先在盘子上装好", f"{context} plate guide")
        require_text_contains(session.get_tutorial_hint_text(), "解锁 9/9「经典汉堡沙拉套餐」", f"{context} tutorial hint")
    elif step_index == 8:
        assert_menu_progress(session, 9, EXPECTED_MENU_TOTAL, "经典汉堡沙拉套餐", "牛排沙拉套餐", context)
        assert_stage_coaching(session, 0, "已完成 9 单正确订单", "已到最终菜单", "9.经典汉堡沙拉套餐[当前]", context)
        assert_player_objective(session, "底部面包, 熟肉饼, 顶部面包, 切好的生菜, 切好的番茄, 沙拉酱", "先叠完整经典汉堡", "面包台 -> 煎锅/灶台", "保持当前节奏", context)
        assert_recipe_card(session, "套餐 / 汉堡加沙拉", "沙拉酱最后加入", "底部面包 -> 熟肉饼 -> 顶部面包 -> 切好的生菜 -> 切好的番茄 -> 沙拉酱", "不能把蔬菜或沙拉酱夹进汉堡中间", context)
        assert_station_outcome(session, "先产出完整经典汉堡", "调味区拿到沙拉酱", "同一个盘子上最后补沙拉配菜", context=context)
        assert_pre_submit_checklist(session, "先确认经典汉堡完整", "沙拉酱已加入", "汉堡和沙拉配菜都在盘子上", "沙拉配菜放在顶部面包之后", context=context)
        require_text_contains(session.get_current_plate_assembly_guide_text(), "沙拉也必须先在盘子上装好", f"{context} plate guide")
        require_text_contains(session.get_tutorial_hint_text(), "已到最终菜单", f"{context} tutorial hint")
    else:
        require_text_contains(session.get_menu_route_text(), spec["name"], f"{context} route listing")
        require_text_contains(session.get_current_menu_item_text(), spec["name"], f"{context} menu item name")
        require_text_contains(session.get_current_menu_item_text(), spec["details"], f"{context} menu item details")
        require_text_contains(session.get_current_stage_unlock_text(), f"已完成 {spec['unlock_count']} 单正确订单", f"{context} unlock text")


def advance_with_current_order(session, delivery_area, spec, advance_count, step_index):
    for attempt in range(advance_count):
        context = f"{spec['name']} submission {attempt + 1}/{advance_count}"
        before_correct_orders = int(session.get_editor_property("CorrectOrders"))
        ok = submit_tags(delivery_area, spec["tags"])
        require(ok, f"{context}: expected tag stack should submit successfully")
        expected_feedback = "任务完成" if step_index == EXPECTED_MENU_TOTAL - 1 else "出餐成功"
        require_text_contains(session.get_editor_property("LastFeedbackMessage"), expected_feedback, f"{context} success feedback")
        require(
            int(session.get_editor_property("CorrectOrders")) == before_correct_orders + 1,
            f"{context}: correct order count did not increment",
        )
        require(int(session.get_editor_property("WrongOrders")) == 0, f"{context}: wrong order count should stay at 0")
        if step_index < EXPECTED_MENU_TOTAL - 1 and attempt < advance_count - 1:
            require(session.get_current_menu_route_step() == step_index + 1, f"{context}: stage should remain on current step")
            require_text_contains(session.get_current_menu_item_text(), spec["name"], f"{context} current item should remain")


def main():
    report = {
        "level_path": LEVEL_PATH,
        "expected_menu_total": EXPECTED_MENU_TOTAL,
        "steps": [],
    }

    clean_old_test_actors()
    order_manager = find_actor_by_label("BP_OrderManager_Playable")
    delivery_area = find_actor_by_label("BP_DeliveryArea")
    require(order_manager is not None, "Missing BP_OrderManager_Playable in demo map")
    require(delivery_area is not None, "Missing BP_DeliveryArea in demo map")
    require(hasattr(unreal, "VRKitchenGameSessionComponent"), "Missing VRKitchenGameSessionComponent")
    require(hasattr(unreal, "VRKitchenOrderValidationLibrary"), "Missing VRKitchenOrderValidationLibrary")

    if delivery_area:
        # Prime the runtime session component; the map creates it on first submit.
        submit_tags(delivery_area, [])

    session = order_manager.get_component_by_class(unreal.VRKitchenGameSessionComponent) if order_manager else None
    require(session is not None, "Session component was not created on the playable order manager")

    if session and delivery_area:
        reset_session(session)
        assert_menu_route_health(session, "initial menu route health")
        unique_names = {spec["name"] for spec in EXPECTED_MENU}
        require(len(unique_names) == EXPECTED_MENU_TOTAL, "Expected menu names must be unique")

        for step_index, spec in enumerate(EXPECTED_MENU):
            context = f"menu step {step_index + 1} {spec['name']}"
            assert_menu_step_texts(session, step_index, spec, context)
            validate_current_stage(session, spec, step_index, context)
            if step_index < EXPECTED_MENU_TOTAL - 1:
                advance_count = EXPECTED_MENU[step_index + 1]["unlock_count"] - spec["unlock_count"]
            else:
                advance_count = 1

            advance_with_current_order(session, delivery_area, spec, advance_count, step_index)
            report["steps"].append(
                {
                    "index": step_index + 1,
                    "unlock_count": spec["unlock_count"],
                    "name": spec["name"],
                    "tags": spec["tags"],
                    "details": spec["details"],
                }
            )

        route_text = str(session.get_menu_route_text())
        for spec in EXPECTED_MENU:
            require_text_contains(route_text, spec["name"], "full menu route")

        require(session.get_editor_property("bMissionCleared"), "Mission should be cleared after the final correct order")
        require(not session.can_accept_orders(), "Session should stop accepting orders after the final correct order")
        require_text_contains(session.get_result_title(), "挑战成功", "final result title")
        require_text_contains(session.get_result_grade_text(), "三星", "final result grade")
        require_text_contains(session.get_tutorial_hint_text(), "挑战完成", "final tutorial hint")
        assert_performance_summary(session, 10, 100, "100% (10/10)", "没有错误订单", "已完成三星路线", "final performance summary")

    destroy_spawned()

    unreal.log("VRKitchen demo content design validation report:")
    unreal.log(json.dumps(report, ensure_ascii=False, indent=2))

    if failures:
        raise RuntimeError("Demo content design validation failed: " + "; ".join(failures))

    unreal.log("VRKitchen demo content design validation passed.")


main()
