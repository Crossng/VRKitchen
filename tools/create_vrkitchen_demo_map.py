import unreal


SOURCE_MAP = "/Game/VRTemplate/Maps/VRTemplateMap"
DESTINATION_DIR = "/Game/_Project/Maps"
DESTINATION_NAME = "VRKitchen_Demo"
DESTINATION_MAP = f"{DESTINATION_DIR}/{DESTINATION_NAME}"


def main():
    if not unreal.EditorAssetLibrary.does_directory_exist(DESTINATION_DIR):
        unreal.EditorAssetLibrary.make_directory(DESTINATION_DIR)

    if unreal.EditorAssetLibrary.does_asset_exist(DESTINATION_MAP):
        unreal.log(f"{DESTINATION_MAP} already exists; leaving existing demo map in place.")
        unreal.EditorAssetLibrary.save_asset(DESTINATION_MAP, only_if_is_dirty=False)
        return

    source_asset = unreal.EditorAssetLibrary.load_asset(SOURCE_MAP)
    if source_asset is None:
        raise RuntimeError(f"Could not load source map: {SOURCE_MAP}")

    duplicated_asset = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(
        DESTINATION_NAME,
        DESTINATION_DIR,
        source_asset,
    )
    if duplicated_asset is None:
        raise RuntimeError(f"Could not duplicate {SOURCE_MAP} to {DESTINATION_MAP}")

    unreal.EditorAssetLibrary.save_asset(DESTINATION_MAP, only_if_is_dirty=False)
    unreal.log(f"Created demo map: {DESTINATION_MAP}")


main()
