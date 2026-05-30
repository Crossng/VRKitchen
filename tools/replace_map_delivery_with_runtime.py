import json

import unreal
from unreal_bridge import Editor, Level


LEVEL_PATH = "/Game/VRTemplate/Maps/VRTemplateMap"
NEW_CLASS = "/Game/_Project/Gameplay/Orders/BP_DeliveryArea_Runtime.BP_DeliveryArea_Runtime_C"
NEW_LABEL = "BP_DeliveryArea_Runtime0"
NEW_LOCATION = {"x": 170.0, "y": 325.0, "z": 117.0}

Editor.load_level(level_path=LEVEL_PATH, prompt_save_changes=False)

result = {"removed": [], "spawned": None}

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in subsys.get_all_level_actors():
    label = actor.get_actor_label() or ""
    if "DeliveryArea" in label:
        result["removed"].append(label)
        subsys.destroy_actor(actor)

spawned_name = Level.spawn_actor(
    class_path=NEW_CLASS,
    location=NEW_LOCATION,
    rotation={"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
)
if spawned_name:
    Level.set_actor_label(actor_name=spawned_name, new_label=NEW_LABEL)
result["spawned"] = spawned_name
result["saved"] = Editor.save_current_level()

print(json.dumps(result, ensure_ascii=False, indent=2))
