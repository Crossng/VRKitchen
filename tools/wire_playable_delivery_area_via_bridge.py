import json

import unreal
from unreal_bridge import Blueprint, Editor


BP_PATH = "/Game/_Project/Gameplay/Orders/BP_DeliveryArea_Playable"
GRAPH_NAME = "EventGraph"

GET_MANAGER_GUID = "F3EBF9B745D4E4FAD00C4580D30BA36F"
ADD_SCORE_GUIDS = [
    "6480E9154EDF0759E9C47EABAE63AA0A",
    "3844AE414BD29589DD167492AE128D3A",
    "DA24B0D04AFD5C1DDF0A6283C63FB452",
]
GEN_ORDER_GUID = "1E60730A4F0CEFF0F91D9687B3344E1C"
GET_CURRENT_ORDER_GUID = "B92032B1485D6AA709DCEC9D91732873"

PLAYABLE_CLASS = "/Game/_Project/Gameplay/Orders/BP_OrderManager_Playable.BP_OrderManager_Playable_C"

result = {}

Blueprint.set_pin_default_value(
    blueprint_path=BP_PATH,
    graph_name=GRAPH_NAME,
    node_guid=GET_MANAGER_GUID,
    pin_name="ActorClass",
    new_default_value=PLAYABLE_CLASS,
)

replaced = {}
for guid in ADD_SCORE_GUIDS + [GEN_ORDER_GUID]:
    try:
        report = Blueprint.replace_node_preserving_connections(
            blueprint_path=BP_PATH,
            graph_name=GRAPH_NAME,
            old_node_guid=guid,
            new_node_class_path=PLAYABLE_CLASS,
        )
        replaced[guid] = str(report)
    except Exception as e:
        replaced[guid] = f"ERROR: {e}"
result["replaced_calls"] = replaced

try:
    report = Blueprint.replace_node_preserving_connections(
        blueprint_path=BP_PATH,
        graph_name=GRAPH_NAME,
        old_node_guid=GET_CURRENT_ORDER_GUID,
        new_node_class_path=PLAYABLE_CLASS,
    )
    result["replaced_currentorder_get"] = str(report)
except Exception as e:
    result["replaced_currentorder_get"] = f"ERROR: {e}"

result["recompiled"] = Editor.recompile_blueprint(blueprint_path=BP_PATH)
asset = unreal.load_asset(BP_PATH)
unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)

print(json.dumps(result, ensure_ascii=False, indent=2))
