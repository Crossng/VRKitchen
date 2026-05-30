# VRKitchen 资源命名与目录整理规范

## 目标

最终项目需要把“项目自有资源、第三方资源、模板遗留资源、临时开发资源”清楚分开，避免所有资产混在 `Content` 根目录。当前阶段先建立规范和扫描工具，不直接批量移动 `.uasset/.umap`，防止蓝图引用断裂。

## 推荐目录结构

```text
Content/
  _Project/
    Maps/
    Core/
    Gameplay/
      Food/
      Cooking/
      Orders/
      Delivery/
      Interaction/
    UI/
    Art/
      Food/
      Props/
      Environment/
      Materials/
      Textures/
      Audio/
      FX/
    VR/
  _External/
    Marketplace/
    RestaurantPack/
    TemplateSource/
  _Legacy/
    VRTemplate/
    StarterContent/
  _Dev/
    Prototypes/
    TestMaps/
```

## 分类边界

- `Content/_Project`：本项目正式使用的地图、玩法蓝图、UI、食材、厨房道具、演示关卡专属美术和音频。
- `Content/_External`：第三方包、Marketplace 餐厅包、FBX 导入源、贴图源文件和不适合改名的外部素材。
- `Content/_Legacy`：UE 模板、旧地图、历史验证资源、暂时还可能被引用但不属于最终玩法的遗留内容。
- `Content/_Dev`：开发者临时目录、原型、测试食材、测试地图、临时调试资源；交付前要决定删除还是转正。

## 命名规范

- 蓝图 Actor：`BP_功能_对象`，例如 `BP_Food_RawPatty`、`BP_Cook_Pan`、`BP_Order_Manager`。
- Widget：`WBP_功能`，例如 `WBP_OrderTablet`。
- 材质：`M_对象_用途`，材质实例：`MI_对象_用途`。
- 贴图：`T_对象_用途`，例如 `T_Patty_BaseColor`、`T_Patty_Normal`。
- 静态网格：`SM_对象`，骨骼网格：`SK_对象`。
- 动画蓝图：`ABP_对象`，动画序列：`A_动作`。
- 数据资产：`DA_功能`，数据表：`DT_功能`，枚举：`E_功能`。
- 音效：`SFX_事件`，音乐：`BGM_场景`。
- Niagara：`NS_效果`。
- 地图可以使用清晰场景名，例如 `VRKitchen_Demo`；测试地图放入 `_Dev/TestMaps`。
- 玩家可见文本使用中文；Actor Tag、C++ API、变量名继续使用英文，避免破坏现有蓝图引用。

## 当前命名取舍

- 现有活跃蓝图暂时不强制重命名，优先保证引用不断；先迁移目录，再在最后阶段逐个重命名。
- 第三方包资源可以保留原名，只要放在 `_External` 下并在文档里说明来源。
- `_Legacy` 里的模板资源可以暂时保留旧命名；只有确认仍要参与最终交付时才重命名。
- `verify_asset_organization.py --strict` 只适合最终迁移和重定向器修复完成后启用。

## 当前整理原则

- 交付 Demo 地图固定为 `/Game/_Project/Maps/VRKitchen_Demo`。
- 项目新增资源默认进入 `Content/_Project`。
- 第三方包或原始素材进入 `Content/_External`，不要直接散在根目录。
- VRTemplate、StarterContent 等历史模板资源迁移前先归类到 `Content/_Legacy`，确认引用后再删除。
- 临时验证资源、测试地图、实验蓝图进入 `Content/_Dev`，交付前决定是否删除或转正。

## 迁移步骤

1. 阅读 `VRKitchen_ASSET_MIGRATION_PLAN.md`，确认本轮只处理哪个阶段。
2. 用 `tools/verify_asset_organization.py` 扫描当前资源分布，并用 `--report` 导出带 phase/risk 汇总和推荐下一批的 Markdown 报告。
3. 先在 Unreal Editor 中移动资产，不要用文件管理器直接移动 `.uasset/.umap`。
4. 每次只迁移一个小模块，例如 Food、Cooking、Orders、UI。
5. 迁移后在 Content Browser 对旧目录执行 `Fix Up Redirectors`。
6. 重新运行 C++ 构建、CompileAllBlueprints、DataValidation、玩法自动化和 Win64 打包。
7. 确认引用无误后，再删除 `_Legacy` 或 `_Dev` 中不需要的资源。

## 当前推荐下一批

- 先只 dry-run `phase-2-dev-folders` 和 `phase-2-prototypes`，观察 `Collections`、`Developers`、`food_test` 是否会移动到 `_Dev`。
- 不在命令行 unattended 模式中自动 Fix Up Redirectors；真实迁移后打开 Unreal Editor 手动修复。
- `VRTemplate`、`Blueprints`、根目录活跃蓝图、订单区和食材蓝图属于高风险或中风险，不应和开发临时资源一起迁移。

## GitHub 与网盘边界

- GitHub 只放 `Source`、`Config`、`.uproject`、说明文档和小工具。
- `Content`、`.uasset`、`.umap`、`Binaries`、`Intermediate`、`Saved`、`DerivedDataCache` 不上传 GitHub。
- 完整工程资源通过网盘交付；上传网盘前排除可重建目录。
