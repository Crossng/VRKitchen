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
- `food_test` 原型资源本体已迁移到 `Content/_Dev/Prototypes/food_test`；旧 `Content/food_test` 仍残留 redirector 和 `.fbx/.png` sidecar 文件，必须在可视化 Unreal Editor 中 Fix Up Redirectors 并人工确认后再清理。
- `Collections`、`Developers` 顶层空目录已通过 Unreal Editor API 清理，目标目录保留在 `Content/_Dev/Collections` 与 `Content/_Dev/Developers`。
- Phase 3 大目录命令行迁移曾出现半成功状态：部分根目录贴图和 `SM_WallMonitor_01_fbm` 已迁到 `_External`，源路径留下 redirector；`Fast_Food_Restaurant`、`Maps` 与 `Kitchen_Demo_Map` 的大目录/旧地图迁移未完成。后续不要重复一键大目录迁移，应先在可视化 Unreal Editor 中 Fix Up Redirectors，再按小批次处理。
- 最新资源审计为 `7 pass / 22 warn / 0 fail`，说明结构在变干净，但还没有进入严格完成状态。

## 已执行内容

- 已通过 `tools/migrate_asset_organization_via_editor.py` 创建目标目录结构。
- 已对 `phase-2-prototypes` 执行真实迁移，迁移报告为 `VRKitchen_ASSET_MIGRATION_APPLY_PHASE2_PROTOTYPES.json`；报告验证通过，但命令行返回值受 SourceControl 旧路径 `C:/Users/MullerAu` 噪声影响，需以后续验证和报告内容为准。
- 已对 `phase-2-dev-folders` 执行 dry-run 和真实整理，顶层 `Content/Collections` 与 `Content/Developers` 空目录已清理，`Content/_Dev/Collections` 与 `Content/_Dev/Developers` 保留为目标结构。
- 已对 Phase 3 执行 dry-run 并生成 `VRKitchen_ASSET_MIGRATION_DRYRUN_PHASE3_CURRENT.json`，报告验证通过；随后真实执行生成 `VRKitchen_ASSET_MIGRATION_APPLY_PHASE3_CURRENT.json`，该报告包含失败项，必须视为半成功迁移记录而不是完成记录。
- 已新增 `tools/audit_asset_migration_state_via_editor.py`，用于只读检查半成功迁移后的源/目标资产状态、redirector 状态和待人工处理项。
- 已生成 `VRKitchen_ASSET_AUDIT.md` 和 `VRKitchen_ASSET_MIGRATION_APPLY_PHASE1_2.json` 作为完整工程本地审计记录；这些报告不需要进入 GitHub。
- 命令行迁移脚本默认不执行 Fix Up Redirectors，因为 UE 5.5.4 的 AssetTools 在 unattended commandlet 中可能触发断言；每批真实资产迁移后，应在可视化 Unreal Editor 的 Content Browser 中手动执行 Fix Up Redirectors，再跑验证。

## 分阶段路线

### Phase 1：审计与空结构

- 创建缺失的目标目录结构。
- 使用 `tools/verify_asset_organization.py --report ...` 输出当前资源分类报告；报告会按 phase/risk/category 汇总，并给出推荐下一批迁移。
- 不移动任何 `.uasset/.umap`。
- 可用 `tools/migrate_asset_organization_via_editor.py` 的 dry-run/执行模式重复生成或确认该结构。

### Phase 2：开发与测试资源

- 迁移 `Developers`、临时测试地图和原型资源到 `Content/_Dev`。
- 迁移前确认它们不在当前 Demo 地图和 Cook 配置中。
- `Collections`、`Developers` 下一步要先 dry-run；确认引用安全后，才在 Unreal Editor 内执行真实迁移。
- `food_test` 的下一步不是重复迁移，而是在可视化 Unreal Editor 中对旧目录执行 Fix Up Redirectors，确认没有引用断裂后再处理残留 sidecar 文件。

### Phase 3：模板、第三方与旧地图

- 迁移 `StarterContent`、`LevelPrototyping`、`FPWeapon` 到 `Content/_Legacy`。
- 迁移 `Fast_Food_Restaurant`、FBX sidecar、导入源文件到 `Content/_External`。
- 旧 `Kitchen_Demo_Map` 进入 `Content/_Legacy/Maps` 或确认无用后删除。
- `VRTemplate` 风险更高，只有在确认当前 Demo 不再依赖模板路径时才迁移。
- 不要在 unattended commandlet 中再次整体执行 Phase 3 大目录真实迁移；先打开可视化 Unreal Editor，在 Content Browser 对 `/Game` 或相关源目录执行 Fix Up Redirectors，再运行 `audit_asset_migration_state_via_editor.py` 判断哪些条目仍是实物资产。

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

dry-run 报告必须先通过安全门禁，确认报告仍是 `dry_run=true`、没有 `errors`、没有真实执行状态，并且下一批 phase-2 迁移动作都出现在报告里：

```powershell
python C:\Users\hp\Desktop\CrazyKitchen\tools\verify_asset_migration_report.py --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN.json
```

后续预演 Phase 3 或 Phase 4 时，不要只检查 JSON 能否打开；必须用 `--expected-phases` 指定本批具体阶段，让脚本核对每一个预期移动动作都已经出现在 dry-run 报告里：

```powershell
python C:\Users\hp\Desktop\CrazyKitchen\tools\verify_asset_migration_report.py --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN_PHASE3.json --expected-phases phase-3

python C:\Users\hp\Desktop\CrazyKitchen\tools\verify_asset_migration_report.py --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN_PHASE4.json --expected-phases phase-4
```

`phase-3` 会展开为 `phase-3-external`、`phase-3-legacy`、`phase-3-root-legacy` 和 `phase-3-root-external`；`phase-4` 会展开为 `phase-4-root-gameplay`、`phase-4-food-blueprints`、`phase-4-interaction-blueprints` 和 `phase-4-legacy-duplicates`。如果只预演其中一小批，也可以直接传具体脚本阶段名，例如 `--expected-phases phase-4-food-blueprints`。

真实迁移时把 `VRKITCHEN_ASSET_MIGRATION_DRY_RUN` 改为 `0`。默认保持 `VRKITCHEN_ASSET_MIGRATION_FIXUP=0`，迁移后在 Unreal Editor 中手动执行 Fix Up Redirectors。

如果真实迁移报告包含 `errors`，不要立刻重复执行同一批迁移。先运行只读状态审计：

```powershell
$env:VRKITCHEN_ASSET_MIGRATION_REPORT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_APPLY_PHASE3_CURRENT.json'
$env:VRKITCHEN_ASSET_MIGRATION_AUDIT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_AUDIT_PHASE3_CURRENT.json'
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\audit_asset_migration_state_via_editor.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

审计结果中 `migrated-with-source-redirector` 和 `directory-migrated-with-source-redirectors` 表示目标实物资产存在、源路径是 redirector；下一步应在可视化 Unreal Editor 中 Fix Up Redirectors，而不是用文件管理器删除。`directory-pending-source-assets` 表示源目录仍有真实资产，需要拆成更小批次迁移或人工确认引用后再处理。

```powershell
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Build\BatchFiles\Build.bat' VRKitchenEditor Win64 Development -Project='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -WaitMutex -NoHotReloadFromIDE

& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=CompileAllBlueprints -unattended -nop4 -nosplash -NullRHI

& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=DataValidation -unattended -nop4 -nosplash -NullRHI

& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\verify_demo_gameplay_loop_via_bridge.py' -unattended -nop4 -nosplash -NullRHI

& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\verify_salad_cutting_assets_via_bridge.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI

python tools\verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen
```

## 当前不直接搬资产的原因

- 现有 `Content` 中很多资产仍可能被蓝图、地图、材质或模板链引用。
- 文件管理器移动 `.uasset/.umap` 会绕过 UE Redirector，容易造成引用断裂。
- 没有真实 VR 头显时，不应在缺少交互回归的情况下大规模调整关键玩法资产路径。
