
import json
import unreal
from unreal_bridge import Editor, Level

Editor.load_level(level_path='/Game/VRTemplate/Maps/VRTemplateMap', prompt_save_changes=False)

spawns = [
    ('/Game/_Project/Gameplay/Orders/BP_OrderManager_Playable.BP_OrderManager_Playable_C', {'x':245.0,'y':25.0,'z':130.0}, 'BP_OrderManager_Playable0'),
    ('/Game/_Project/Gameplay/Orders/BP_DeliveryArea_Playable.BP_DeliveryArea_Playable_C', {'x':170.0,'y':325.0,'z':117.0}, 'BP_DeliveryArea_Playable0'),
]
result = []
for class_path, loc, label in spawns:
    name = Level.spawn_actor(class_path=class_path, location=loc, rotation={'pitch':0.0,'yaw':0.0,'roll':0.0})
    ok = Level.set_actor_label(actor_name=name, new_label=label) if name else False
    result.append({'class_path':class_path,'spawned_name':name,'label_set':ok})

saved = Editor.save_current_level()
print(json.dumps({'spawns':result,'saved':saved}, ensure_ascii=False, indent=2))
