import unreal
from unreal_bridge import Editor


LEVEL_PATH = "/Game/_Project/Maps/VRKitchen_Demo"
Editor.load_level(level_path=LEVEL_PATH, prompt_save_changes=False)

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = []
failures = []


def actor_components(actor):
    return actor.get_components_by_class(unreal.ActorComponent)


def has_component(actor, component_name):
    return any(component_name in component.get_class().get_name() for component in actor_components(actor))


def find_actor_by_label(label_fragment):
    for actor in subsys.get_all_level_actors():
        label = actor.get_actor_label() or ""
        if label_fragment in label:
            return actor
    return None


def require(condition, message):
    if not condition:
        failures.append(message)


for actor in subsys.get_all_level_actors():
    label = actor.get_actor_label() or ""
    if "Order" in label or "DeliveryArea" in label or "Pan" in label or "Stove" in label:
        actors.append(
            {
                "label": label,
                "class": actor.get_class().get_path_name(),
                "location": str(actor.get_actor_location()),
            }
        )

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

if order_manager:
    require(has_component(order_manager, "VRKitchenOrderTextCleanupComponent"), "Order manager lacks order text cleanup component")
if pan:
    require(has_component(pan, "VRKitchenPanCookComponent"), "Pan lacks pan cook component")

print(f"VRKitchen demo gameplay check: {LEVEL_PATH}")
for item in actors:
    print(f"- {item['label']} :: {item['class']} @ {item['location']}")

if failures:
    raise RuntimeError("Demo gameplay check failed: " + "; ".join(failures))

print("Demo gameplay check passed.")
