import json

from unreal_bridge import Blueprint, Editor


BP_PATH = "/Game/_Project/Gameplay/Orders/BP_DeliveryArea_Runtime"
GRAPH_NAME = "EventGraph"
ACTOR_BEGIN_OVERLAP_GUID = "D1ADEC814A6B00D69BD0349FD28D4260"
result = {}

get_actor_call = Blueprint.add_call_function_node(
    blueprint_path=BP_PATH,
    graph_name=GRAPH_NAME,
    target_class_path="/Script/Engine.GameplayStatics",
    function_name="GetActorOfClass",
    node_pos_x=176,
    node_pos_y=-128,
)
score_call = Blueprint.add_call_function_node(
    blueprint_path=BP_PATH,
    graph_name=GRAPH_NAME,
    target_class_path="/Game/_Project/Gameplay/Orders/BP_OrderManager_Playable.BP_OrderManager_Playable_C",
    function_name="StableAddScore",
    node_pos_x=560,
    node_pos_y=-128,
)
clean_call = Blueprint.add_call_function_node(
    blueprint_path=BP_PATH,
    graph_name=GRAPH_NAME,
    target_class_path="/Game/_Project/Gameplay/Orders/BP_DeliveryArea_Runtime.BP_DeliveryArea_Runtime_C",
    function_name="MakeClean",
    node_pos_x=944,
    node_pos_y=-128,
)

Blueprint.set_pin_default_value(
    blueprint_path=BP_PATH,
    graph_name=GRAPH_NAME,
    node_guid=get_actor_call,
    pin_name="ActorClass",
    new_default_value="/Game/_Project/Gameplay/Orders/BP_OrderManager_Playable.BP_OrderManager_Playable_C",
)
Blueprint.set_pin_default_value(
    blueprint_path=BP_PATH,
    graph_name=GRAPH_NAME,
    node_guid=score_call,
    pin_name="PointsToAdd",
    new_default_value="1",
)

Blueprint.connect_graph_pins(
    blueprint_path=BP_PATH,
    graph_name=GRAPH_NAME,
    source_node_guid=ACTOR_BEGIN_OVERLAP_GUID,
    source_pin_name="then",
    target_node_guid=get_actor_call,
    target_pin_name="execute",
)
Blueprint.connect_graph_pins(
    blueprint_path=BP_PATH,
    graph_name=GRAPH_NAME,
    source_node_guid=get_actor_call,
    source_pin_name="then",
    target_node_guid=score_call,
    target_pin_name="execute",
)
Blueprint.connect_graph_pins(
    blueprint_path=BP_PATH,
    graph_name=GRAPH_NAME,
    source_node_guid=get_actor_call,
    source_pin_name="ReturnValue",
    target_node_guid=score_call,
    target_pin_name="self",
)
Blueprint.connect_graph_pins(
    blueprint_path=BP_PATH,
    graph_name=GRAPH_NAME,
    source_node_guid=score_call,
    source_pin_name="then",
    target_node_guid=clean_call,
    target_pin_name="execute",
)

result["compile"] = Editor.recompile_blueprint(blueprint_path=BP_PATH)
result["compile_errors"] = str(
    Blueprint.get_compile_errors(blueprint_path=BP_PATH)
)
result["created_nodes"] = {
    "get_actor_call": get_actor_call,
    "score_call": score_call,
    "clean_call": clean_call,
}

print(json.dumps(result, ensure_ascii=False, indent=2))
