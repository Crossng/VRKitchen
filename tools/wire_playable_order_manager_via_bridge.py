import json

import unreal
from unreal_bridge import Blueprint, Editor


BP_PATH = "/Game/_Project/Gameplay/Orders/BP_OrderManager_Playable"
GRAPH_NAME = "EventGraph"

TEST_GET_ACTOR_GUID = "0AFB78384D2BDE5D85AD2AAD53D72029"
TEST_REFRESH_GUID = "0510EB904E128516A5C477A19ECC693F"

BEGIN_DELAY_GUID = "F4F391304AB5BDCAD6D35193935EB16E"
BEGIN_CALL_GUID = "2F7F84F14C228F1862BECB931501C957"
BEGIN_EVENT_GUID = "A9B979224DCF880F7EC2A1975CAD00F9"

GEN_EVENT_GUID = "6284B4344C2C2083B5FC6D92644FBF62"
GEN_REFRESH_GUID = "B968DDB64EF88D67ACAA9894D4676CF3"
GEN_GET_ACTOR_GUID = "D56DB71D435E9A217B696E958129B1D1"

ADD_EVENT_GUID = "3AC67CE6433DF7003D5C5398F0207738"
ADD_SET_GAMESCORE_GUID = "E71970B94A5D8D96F81D5DB818DEF692"
ADD_REFRESH_GUID = "63A6D20346EABA86FC267FAC94437EFD"
ADD_GET_ACTOR_GUID = "215B164F4DB9BB016BC0D3B0416DECEE"


def disconnect_if_present(src_guid, src_pin, dst_guid, dst_pin, result, key):
    try:
        Blueprint.disconnect_pin_link(
            blueprint_path=BP_PATH,
            graph_name=GRAPH_NAME,
            source_node_guid=src_guid,
            source_pin_name=src_pin,
            target_node_guid=dst_guid,
            target_pin_name=dst_pin,
        )
        result[key] = True
    except Exception as e:
        result[key] = str(e)


def connect(src_guid, src_pin, dst_guid, dst_pin, result, key):
    try:
        result[key] = Blueprint.connect_graph_pins(
            blueprint_path=BP_PATH,
            graph_name=GRAPH_NAME,
            source_node_guid=src_guid,
            source_pin_name=src_pin,
            target_node_guid=dst_guid,
            target_pin_name=dst_pin,
        )
    except Exception as e:
        result[key] = str(e)


result = {}

# GenerateNewOrder: bypass broken struct/text chain, directly refresh tablet with fixed order text.
for pair in [
    (GEN_EVENT_GUID, "then", "8662CFC84EC02DF84EE84DA24F57864F", "execute", "disconnect_gen_old_start"),
    ("215B164F4DB9BB016BC0D3B0416DECEE", "then", "63A6D20346EABA86FC267FAC94437EFD", "execute", "disconnect_add_old_refresh_chain"),
    ("D56DB71D435E9A217B696E958129B1D1", "then", "B968DDB64EF88D67ACAA9894D4676CF3", "execute", "disconnect_gen_old_refresh_chain"),
]:
    disconnect_if_present(*pair[:-1], result=result, key=pair[-1])

for pin_name, value in [
    ("NewName", "Salad"),
    ("NewDetails", "Chopped_Lettuce, Chopped_Tomato"),
    ("CurrentScore", "0"),
]:
    Blueprint.set_pin_default_value(
        blueprint_path=BP_PATH,
        graph_name=GRAPH_NAME,
        node_guid=GEN_REFRESH_GUID,
        pin_name=pin_name,
        new_default_value=value,
    )

connect(GEN_EVENT_GUID, "then", GEN_GET_ACTOR_GUID, "execute", result, "connect_gen_event_to_getactor")
connect(GEN_GET_ACTOR_GUID, "ReturnValue", GEN_REFRESH_GUID, "self", result, "connect_gen_actor_to_refresh")
connect(GEN_GET_ACTOR_GUID, "then", GEN_REFRESH_GUID, "execute", result, "connect_gen_then_to_refresh")

# BeginPlay should still call GenerateNewOrder, keep existing start path but ensure call remains wired.
connect(BEGIN_EVENT_GUID, "then", BEGIN_DELAY_GUID, "execute", result, "connect_begin_to_delay")
connect(BEGIN_DELAY_GUID, "then", BEGIN_CALL_GUID, "execute", result, "connect_delay_to_generate")

# AddScoreAndRefresh: keep score increment, then use fixed order text but live score.
for pin_name, value in [
    ("NewName", "Salad"),
    ("NewDetails", "Chopped_Lettuce, Chopped_Tomato"),
]:
    Blueprint.set_pin_default_value(
        blueprint_path=BP_PATH,
        graph_name=GRAPH_NAME,
        node_guid=ADD_REFRESH_GUID,
        pin_name=pin_name,
        new_default_value=value,
    )

connect(ADD_EVENT_GUID, "then", ADD_SET_GAMESCORE_GUID, "execute", result, "connect_add_event_to_setscore")
connect(ADD_SET_GAMESCORE_GUID, "then", ADD_GET_ACTOR_GUID, "execute", result, "connect_setscore_to_getactor")
connect(ADD_GET_ACTOR_GUID, "ReturnValue", ADD_REFRESH_GUID, "self", result, "connect_add_actor_to_refresh")
connect(ADD_GET_ACTOR_GUID, "then", ADD_REFRESH_GUID, "execute", result, "connect_add_then_to_refresh")

result["recompiled"] = Editor.recompile_blueprint(blueprint_path=BP_PATH)
asset = unreal.load_asset(BP_PATH)
unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)

print(json.dumps(result, ensure_ascii=False, indent=2))
