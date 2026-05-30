import json
import re

import unreal
from unreal_bridge import Blueprint, Editor


BP_PATH = "/Game/_Project/Gameplay/Orders/BP_DeliveryArea_Runtime"
FUNCTION_NAME = "SubmitCurrentPlate"
LIBRARY_CLASS = "/Script/VRKitchen.VRKitchenOrderValidationLibrary"
LIBRARY_FUNCTION = "SubmitCurrentPlateValidated"


def guid_from_node(text):
    match = re.search(r'node_guid: "([^"]+)"', text)
    return match.group(1) if match else None


result = {}

nodes = [
    str(x)
    for x in Blueprint.get_function_nodes(
        blueprint_path=BP_PATH,
        function_name=FUNCTION_NAME,
        node_type_filter="",
    )
]

entry_guid = next(
    guid_from_node(x)
    for x in nodes
    if 'node_type: "FunctionEntry"' in x
)
result_guid = next(
    guid_from_node(x)
    for x in nodes
    if 'node_type: "FunctionResult"' in x
)

result["entry_guid"] = entry_guid
result["result_guid"] = result_guid

call_guid = Blueprint.add_call_function_node(
    blueprint_path=BP_PATH,
    graph_name=FUNCTION_NAME,
    target_class_path=LIBRARY_CLASS,
    function_name=LIBRARY_FUNCTION,
    node_pos_x=420,
    node_pos_y=0,
)
result["call_guid"] = call_guid
result["call_pins_before"] = [
    str(x)
    for x in Blueprint.get_node_pins(
        blueprint_path=BP_PATH,
        graph_name=FUNCTION_NAME,
        node_guid=call_guid,
    )
]

Blueprint.connect_graph_pins(
    blueprint_path=BP_PATH,
    graph_name=FUNCTION_NAME,
    source_node_guid=entry_guid,
    source_pin_name="then",
    target_node_guid=call_guid,
    target_pin_name="execute",
)
Blueprint.connect_graph_pins(
    blueprint_path=BP_PATH,
    graph_name=FUNCTION_NAME,
    source_node_guid=call_guid,
    source_pin_name="then",
    target_node_guid=result_guid,
    target_pin_name="execute",
)

try:
    Blueprint.connect_graph_pins(
        blueprint_path=BP_PATH,
        graph_name=FUNCTION_NAME,
        source_node_guid=call_guid,
        source_pin_name="OutOk",
        target_node_guid=result_guid,
        target_pin_name="OutOk",
    )
    result["connected_outok"] = True
except Exception as exc:
    result["connect_outok_error"] = str(exc)

try:
    result["delivery_default_before"] = Blueprint.get_pin_default_value(
        blueprint_path=BP_PATH,
        graph_name=FUNCTION_NAME,
        node_guid=call_guid,
        pin_name="DeliveryArea",
    )
except Exception as exc:
    result["delivery_default_before_error"] = str(exc)

try:
    Blueprint.set_pin_default_value(
        blueprint_path=BP_PATH,
        graph_name=FUNCTION_NAME,
        node_guid=call_guid,
        pin_name="DeliveryArea",
        new_default_value="self",
    )
    result["set_delivery_default_self"] = True
except Exception as exc:
    result["set_delivery_default_self_error"] = str(exc)

try:
    result["delivery_default_after"] = Blueprint.get_pin_default_value(
        blueprint_path=BP_PATH,
        graph_name=FUNCTION_NAME,
        node_guid=call_guid,
        pin_name="DeliveryArea",
    )
except Exception as exc:
    result["delivery_default_after_error"] = str(exc)

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
