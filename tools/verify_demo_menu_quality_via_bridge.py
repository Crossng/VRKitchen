import unreal
from unreal_bridge import Editor


LEVEL_PATH = "/Game/_Project/Maps/VRKitchen_Demo"


Editor.load_level(level_path=LEVEL_PATH, prompt_save_changes=False)

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
failures = []


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


order_manager = find_actor_by_label("BP_OrderManager_Playable")
delivery_area = find_actor_by_label("BP_DeliveryArea")

require(order_manager is not None, "Missing BP_OrderManager_Playable in demo map")
require(delivery_area is not None, "Missing BP_DeliveryArea in demo map")
require(hasattr(unreal, "VRKitchenOrderValidationLibrary"), "Missing VRKitchenOrderValidationLibrary")
require(hasattr(unreal, "VRKitchenGameSessionComponent"), "Missing VRKitchenGameSessionComponent")

if order_manager and delivery_area:
    if not order_manager.get_component_by_class(unreal.VRKitchenGameSessionComponent):
        unreal.VRKitchenOrderValidationLibrary.submit_current_plate_validated(delivery_area)

    session = order_manager.get_component_by_class(unreal.VRKitchenGameSessionComponent)
    require(session is not None, "Session component was not created on the playable order manager")

    if session:
        report = session.get_demo_menu_route_quality_report_text()
        require(session.is_demo_menu_route_healthy(), f"Demo menu route should be healthy:\n{report}")
        require_text_contains(report, "菜单自检: 通过", "menu health report")
        require_text_contains(report, "菜单数量: 9", "menu health report")
        require_text_contains(report, "中文玩家文案", "menu health report")
        require_text_contains(report, "切菜/煎锅/调味区提示", "menu health report")
        require_text_contains(report, "沙拉与套餐盘装规则", "menu health report")
        require_text_contains(session.get_menu_route_text(), "田园沙拉", "menu route")
        require_text_contains(session.get_demo_menu_route_quality_report_text(), "盘装", "menu health report plating rule")
        station_guide = session.get_kitchen_station_guide_text()
        for fragment in ["厨房工位导览", "面包台", "蔬菜区", "切菜板", "调味区", "煎锅/灶台", "装盘区", "出餐区", "清理区"]:
            require_text_contains(station_guide, fragment, "kitchen station guide")
        print(report)

if failures:
    raise RuntimeError("Demo menu quality verification failed: " + "; ".join(failures))

print("Success - demo menu quality report is healthy")
