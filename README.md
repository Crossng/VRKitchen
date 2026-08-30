# VRKitchen 纯代码仓库

本仓库只保存 VRKitchen Unreal Engine 5.5.4 项目的代码、配置和小型工具。

完整 Unreal 工程资源通过云盘/网盘单独交付。请不要在这里提交大型二进制项目资源。

## 完整工程下载

完整工程源文件（`VRCrazyKitchen.zip` 等 2 个文件）通过百度网盘分享：

- [打开百度网盘分享](https://pan.baidu.com/s/1FlrQ5vl0GHLvo42fHb5gmA?pwd=rdnf)
- 提取码：`rdnf`

下载并解压完整工程后，再按照下面的“使用方式”打开 Unreal 项目。GitHub 仓库只维护代码、配置和工具，完整资源仍保留在网盘中。

## 当前 Demo 范围

- 目标环境：UE 5.5.4、Windows PCVR、通过 OpenXR 使用 SteamVR。
- Demo 地图：`/Game/_Project/Maps/VRKitchen_Demo`。
- 玩法闭环：中文订单反馈、盘面提交校验、煎锅/灶台烹饪、烧焦食材拒绝、3 分钟回合、115 分目标、连击奖励、任务完成结算、星级、正确/错误计数、递进式牛排、带沙拉酱的田园沙拉、汉堡和套餐订单，以及阶段提示、紧张度提示和下一目标引导。
- 当前未在本仓库中验证：真实 SteamVR 头显体验、手柄操作手感、Quest/Android 独立运行时。

## 使用方式

1. 从云盘/网盘下载完整 VRKitchen 工程包。
2. 将本仓库中的 `VRKitchen/` 文件夹覆盖/叠加到完整工程目录中。
3. 使用 Unreal Engine 5.5.4 打开 `VRKitchen/VRKitchen.uproject`。
4. 如果 Unreal 提示需要编译，请重新编译 `VRKitchen` C++ 模块。
5. 发布前运行 `CompileAllBlueprints`、`DataValidation`、`tools/verify_demo_gameplay_loop_via_bridge.py` 和 `tools/verify_demo_content_design_via_bridge.py`。

## 维护检查

仓库提供了一条不需要单独下载 `Content/` 目录的轻量级 CI 检查路径。在仓库根目录执行以下命令即可运行相同的本地检查：

```bash
python3 -m compileall -q tools
python3 -m unittest discover -s tools/tests -p 'test_*.py'
python3 tools/verify_delivery_readiness.py --skip-full-project --code-repo-root . --require-clean-git
```

完整交付检查仍然需要完整 Unreal 工程，是上传新的网盘工程包前的最终门禁：

```bash
python3 tools/verify_delivery_readiness.py \
  --full-project-root /path/to/VRKitchen \
  --code-repo-root . \
  --require-clean-git
```

Python 检查只验证仓库边界和工具语法，不能替代 Unreal Editor 验证、蓝图编译、Data Validation、头显测试或 Win64 打包。

如果 UnrealBridge 绑定到了非本机回环地址，请通过环境变量传入 token，避免 token 出现在 shell 历史记录中：

```bash
UNREAL_BRIDGE_TOKEN='your-token' \
  python3 tools/unreal_bridge_client.py --host 192.168.1.20 --port 54321 --ping
```

## 交付自检

在推送代码或将完整工程上传到网盘前，运行交付边界检查：

```powershell
python tools/verify_delivery_readiness.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen --code-repo-root C:\Users\hp\Desktop\VRKitchen_CodeOnly
```

该脚本会检查完整工程是否仍包含 Demo 地图、源代码、配置、插件和交付文档，并确认代码仓库没有跟踪 `Content`、`.uasset`、`.umap`、二进制文件、打包输出或超大文件。

要验证九道菜 Demo 菜单（包括带 `Salad_Dressing` 的田园沙拉和沙拉套餐）是否仍然接入玩家配方卡、订单板、工位提示、检查清单和最终三星结算流程：

```powershell
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\verify_demo_content_design_via_bridge.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

要运行轻量级菜单健康检查，确认解锁顺序、菜名唯一性、中文玩家文案以及沙拉/套餐配方规则：

```powershell
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\verify_demo_menu_quality_via_bridge.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

如果完整工程地图缺少沙拉酱 Blueprint 或食材刷新点，请在完整工程中运行幂等修复脚本，再进行地图/内容验证。脚本会保存 `.uasset/.umap`，因此生成的资源只会留在网盘工程包中，不会进入 GitHub：

```powershell
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\ensure_salad_dressing_assets_via_bridge.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

如果完整工程地图缺少牛排和牛排沙拉套餐使用的生牛肉刷新点，请运行：

```powershell
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\ensure_demo_raw_meat_spawner_via_bridge.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

## 资源整理审计

资源命名和目录规则记录在 `VRKitchen_ASSET_ORGANIZATION.md`，分阶段迁移方案记录在 `VRKitchen_ASSET_MIGRATION_PLAN.md`。当前安全流程是先审计，之后只在 Unreal Editor 内移动资源：

```powershell
python tools/verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen
```

默认审计是提示模式；只有在资源迁移完成并修复重定向器后，才使用 `--strict`。

要从完整工程生成 Markdown 迁移报告，其中包含阶段/风险/类别汇总、建议的下一批资源和对应的 dry-run 命令：

```powershell
python tools/verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_AUDIT.md
```

要对分阶段 Unreal Editor 迁移执行 dry-run：

```powershell
$env:VRKITCHEN_ASSET_MIGRATION_PHASES='phase-1,phase-2-dev-folders,phase-2-prototypes'
$env:VRKITCHEN_ASSET_MIGRATION_DRY_RUN='1'
$env:VRKITCHEN_ASSET_MIGRATION_REPORT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN.json'
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\migrate_asset_organization_via_editor.py' -unattended -nop4 -nosplash -NullRHI
```

迁移脚本默认使用 dry-run，并且不会在无人值守 commandlet 中执行 Fix Up Redirectors。真实移动资源后，请在 Unreal Editor 的 Content Browser 中手动执行 Fix Up Redirectors。

在实际移动资源前，先验证每一份迁移 dry-run 报告。验证器支持 `phase-3`、`phase-4` 等阶段别名，也支持指定具体脚本阶段：

```powershell
python tools/verify_asset_migration_report.py --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN_PHASE3.json --expected-phases phase-3
python tools/verify_asset_migration_report.py --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN_PHASE4.json --expected-phases phase-4
```

如果真实迁移只完成了一部分，请先审计当前重定向器/目标状态，再尝试下一次移动。该审计是只读的，可用于判断下一步应该在 Content Browser 中执行 Fix Up Redirectors、缩小迁移批次，还是进行人工复核：

```powershell
$env:VRKITCHEN_ASSET_MIGRATION_REPORT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_APPLY_PHASE3_CURRENT.json'
$env:VRKITCHEN_ASSET_MIGRATION_AUDIT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_AUDIT_PHASE3_CURRENT.json'
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\audit_asset_migration_state_via_editor.py' -unattended -nop4 -NoSourceControl -nosplash -NullRHI
```

## GitHub 中应包含的内容

- `VRKitchen/Source/`
- `VRKitchen/Config/`
- `VRKitchen/VRKitchen.uproject`
- `tools/` 下的小型辅助脚本
- 必要时加入 UnrealBridge 源码/Python 工具

## 不应提交到 GitHub 的内容

- `Content/`
- `Binaries/`
- `Intermediate/`
- `Saved/`
- `DerivedDataCache/`
- 大型 `.uasset`、`.umap`、`.fbx`、`.zip`、`.pdb`、`.exe` 文件和打包产物
