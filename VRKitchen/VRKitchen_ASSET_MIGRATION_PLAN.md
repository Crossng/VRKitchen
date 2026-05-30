# VRKitchen 资源整理第一阶段迁移计划

## 本阶段目标

当前目标不是立即搬运全部 `.uasset/.umap`，而是把资源整理变成可控流程：先分类、出报告、确定迁移阶段和风险，再在 Unreal Editor 内逐批移动并修复 Redirectors。

## 当前审计结论

- Demo 地图已经位于 `Content/_Project/Maps/VRKitchen_Demo.umap`。
- `Content/_Project/Core`、`Content/_Project/Gameplay`、`Content/_Project/UI` 已存在。
- `Content/_Project/Art`、`Content/_External`、`Content/_Legacy`、`Content/_Dev` 目标结构已经创建。
- `Content` 根目录仍有可迁移资产，例如 `BP_Pan.uasset`、`BP_PickFood.uasset`、`BP_Plate.uasset`、`BP_Stove.uasset`、旧地图和导入贴图。
- `VRTemplate`、`StarterContent`、`FPWeapon`、`LevelPrototyping`、`VRSpectator` 等应归为 `Content/_Legacy`，但必须先确认引用。
- `Fast_Food_Restaurant` 与 FBX sidecar 目录应归为 `Content/_External`。
- `Collections`、`Developers` 与 `food_test` 仍应归为 `Content/_Dev`；下一批先做 dry-run，不直接移动真实资产。
- 最新资源审计为 `7 pass / 24 warn / 0 fail`，说明结构在变干净，但还没有进入严格完成状态。

## 已执行内容

- 已通过 `tools/migrate_asset_organization_via_editor.py` 创建目标目录结构。
- 已把 `phase-2-dev-folders` 与 `phase-2-prototypes` 确认为下一批低风险 dry-run 目标，真实迁移前不直接改动 `.uasset/.umap`。
- 已生成 `VRKitchen_ASSET_AUDIT.md` 和 `VRKitchen_ASSET_MIGRATION_APPLY_PHASE1_2.json` 作为完整工程本地审计记录；这些报告不需要进入 GitHub。
- 命令行迁移脚本默认不执行 Fix Up Redirectors，因为 UE 5.5.4 的 AssetTools 在 unattended commandlet 中可能触发断言；每批真实资产迁移后，应在可视化 Unreal Editor 的 Content Browser 中手动执行 Fix Up Redirectors，再跑验证。

## 分阶段路线

### Phase 1：审计与空结构

- 创建缺失的目标目录结构。
- 使用 `tools/verify_asset_organization.py --report ...` 输出当前资源分类报告；报告会按 phase/risk/category 汇总，并给出推荐下一批迁移。
- 不移动任何 `.uasset/.umap`。
- 可用 `tools/migrate_asset_organization_via_editor.py` 的 dry-run/执行模式重复生成或确认该结构。

### Phase 2：开发与测试资源

- 迁移 `Developers`、`food_test`、临时测试地图和原型资源到 `Content/_Dev`。
- 迁移前确认它们不在当前 Demo 地图和 Cook 配置中。
- `Collections`、`Developers` 和 `food_test` 下一步要先 dry-run；确认引用安全后，才在 Unreal Editor 内执行真实迁移。

### Phase 3：模板、第三方与旧地图

- 迁移 `StarterContent`、`LevelPrototyping`、`FPWeapon` 到 `Content/_Legacy`。
- 迁移 `Fast_Food_Restaurant`、FBX sidecar、导入源文件到 `Content/_External`。
- 旧 `Kitchen_Demo_Map` 进入 `Content/_Legacy/Maps` 或确认无用后删除。
- `VRTemplate` 风险更高，只有在确认当前 Demo 不再依赖模板路径时才迁移。

### Phase 4：核心玩法资产

- 逐模块迁移：
- Food：`BP_PickFood`、`BP_Tomato`、食材相关蓝图。
- Cooking：`BP_Pan`、`BP_Stove`、煎锅/灶台相关资产。
- Delivery：`BP_Plate`、出餐区相关资产。
- Orders：订单板、订单管理器、订单 UI 资产。
- 每迁移一个模块都必须在 Unreal Editor 中执行 Fix Up Redirectors。

### Phase 5：美术、音频与 UI 归档

- 把 Materials、Models、Environment、Lighting、Audio、UI 按归属移动到 `Content/_Project/Art` 或 `Content/_External`。
- 对第三方包保留原始来源说明，方便网盘交付和后续排查。

### Phase 6：严格门禁

- 当资源迁移完成且验证全绿后，运行：

```powershell
python tools\verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen --strict
```

- 只有在 `--strict` 通过后，才把资源组织视为最终完成。

## 每批迁移后的必跑验证

迁移脚本 dry-run 示例：

```powershell
$env:VRKITCHEN_ASSET_MIGRATION_PHASES='phase-1,phase-2-dev-folders,phase-2-prototypes'
$env:VRKITCHEN_ASSET_MIGRATION_DRY_RUN='1'
$env:VRKITCHEN_ASSET_MIGRATION_REPORT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN.json'
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\migrate_asset_organization_via_editor.py' -unattended -nop4 -nosplash -NullRHI
```

真实迁移时把 `VRKITCHEN_ASSET_MIGRATION_DRY_RUN` 改为 `0`。默认保持 `VRKITCHEN_ASSET_MIGRATION_FIXUP=0`，迁移后在 Unreal Editor 中手动执行 Fix Up Redirectors。

```powershell
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Build\BatchFiles\Build.bat' VRKitchenEditor Win64 Development -Project='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -WaitMutex -NoHotReloadFromIDE

& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=CompileAllBlueprints -unattended -nop4 -nosplash -NullRHI

& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=DataValidation -unattended -nop4 -nosplash -NullRHI

& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\verify_demo_gameplay_loop_via_bridge.py' -unattended -nop4 -nosplash -NullRHI

python tools\verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen
```

## 当前不直接搬资产的原因

- 现有 `Content` 中很多资产仍可能被蓝图、地图、材质或模板链引用。
- 文件管理器移动 `.uasset/.umap` 会绕过 UE Redirector，容易造成引用断裂。
- 没有真实 VR 头显时，不应在缺少交互回归的情况下大规模调整关键玩法资产路径。
