import json

import unreal
from unreal_bridge import Blueprint, Editor


BP_PATH = "/Game/_Project/Gameplay/Orders/BP_DeliveryArea_Runtime"
FUNCTION_NAME = "SubmitCurrentPlate"
CALL_FUNCTION = "SubmitCurrentPlateValidated"

result = {}
nodes = [
    str(x)
    for x in Blueprint.get_function_nodes(
        blueprint_path=BP_PATH,
        function_name=FUNCTION_NAME,
        node_type_filter="",
    )
]

call_guid = None
for node in nodes:
    if CALL_FUNCTION in node:
        marker = 'node_guid: "'
        call_guid = node.split(marker)[1].split('"')[0]
        break

if not call_guid:
    # Bridge node summaries do not always include the function name, so find
    # the call node by looking for the DeliveryArea pin.
    for node in nodes:
        if 'node_type: "FunctionCall"' not in node:
            continue
        guid = node.split('node_guid: "')[1].split('"')[0]
        pins = [
            str(x)
            for x in Blueprint.get_node_pins(
                blueprint_path=BP_PATH,
                graph_name=FUNCTION_NAME,
                node_guid=guid,
            )
        ]
        if any('name: "DeliveryArea"' in pin for pin in pins):
            call_guid = guid
            break

result["call_guid"] = call_guid

self_guid = Blueprint.add_node_by_class_name(
    blueprint_path=BP_PATH,
    graph_name=FUNCTION_NAME,
    node_class_path="/Script/BlueprintGraph.K2Node_Self",
    node_pos_x=160,
    node_pos_y=160,
)
result["self_guid"] = self_guid
result["self_pins"] = [
    str(x)
    for x in Blueprint.get_node_pins(
        blueprint_path=BP_PATH,
        graph_name=FUNCTION_NAME,
        node_guid=self_guid,
    )
]

connected = False
for pin_name in ["self", "Self", "ReturnValue"]:
    try:
        Blueprint.connect_graph_pins(
            blueprint_path=BP_PATH,
            graph_name=FUNCTION_NAME,
            source_node_guid=self_guid,
            source_pin_name=pin_name,
            target_node_guid=call_guid,
            target_pin_name="DeliveryArea",
        )
        result["connected_self_pin"] = pin_name
        connected = True
        break
    except Exception as exc:
        result[f"connect_{pin_name}_error"] = str(exc)

result["connected"] = connected
result["call_pins_after"] = [
    str(x)
    for x in Blueprint.get_node_pins(
        blueprint_path=BP_PATH,
        graph_name=FUNCTION_NAME,
        node_guid=call_guid,
    )
]
result["compile"] = Editor.recompile_blueprint(blueprint_path=BP_PATH)
result["compile_errors"] = str(Blueprint.get_compile_errors(blueprint_path=BP_PATH))

asset = unreal.load_asset(BP_PATH)
unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
result["saved"] = True

print(json.dumps(result, ensure_ascii=False, indent=2))
