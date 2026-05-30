# VRKitchen SteamVR 演示交付说明

## 项目定位

本版本是 UE 5.5.4 的 VRKitchen 演示可交付版，目标运行环境是 Windows PCVR + SteamVR/OpenXR。当前重点是展示完整玩法闭环：接订单、处理食材、煎锅烹饪、叠盘、提交订单、正确/错误反馈、倒计时回合和连续订单流程。

## 启动方式

1. 使用 Unreal Engine 5.5.4 打开 `VRKitchen.uproject`。
2. 默认启动地图为 `/Game/_Project/Maps/VRKitchen_Demo`。
3. SteamVR 用户请确保 SteamVR 已安装，并在 OpenXR 设置中使用 SteamVR Runtime。
4. 没有头显时可以进行编辑器验证、蓝图编译、数据验证和 Win64 打包验证，但不能确认真实 VR 手柄手感。

## 已完成内容

- 订单系统可以生成当前订单并显示在订单板/订单 UI。
- 盘子提交时会按食材顺序严格校验。
- 正确订单显示“出餐成功”并加分。
- 错误订单会显示中文原因，包括缺少食材、多了食材、顺序错误、未知食材、未处理食材。
- 生肉饼和生肉可以在煎锅 + 灶台上烹饪，完成后显示“已煎熟”。
- 熟肉继续停留在热锅上会烧焦，烧焦食材不能通过订单。
- Demo 回合默认 3 分钟，正确订单 +10 分，错误订单默认 -2 分且不扣到负数。
- Demo 有目标分、连击奖励、任务完成和星级结算；达到目标分后会停止继续提交并显示挑战成功。
- 订单会随正确完成数递进：前期经典汉堡，中期加入生菜/番茄，后期进入厚肉生菜堡和豪华双肉堡。
- 运行时会显示中文新手提示、剩余时间、分数、完成数、错误数、当前阶段、紧张度和下一目标。
- 时间进入 45 秒内会提示“注意时间”，进入 20 秒内会提示“最后冲刺”；教程文本会随订单阶段和错误恢复动态变化。
- Demo 地图入口已经整理为 `/Game/_Project/Maps/VRKitchen_Demo`。
- 资源整理规范已经写入 `VRKitchen_ASSET_ORGANIZATION.md`，第一阶段迁移路线写入 `VRKitchen_ASSET_MIGRATION_PLAN.md`；目标结构和 `Collections/Developers` 低风险清理已完成，当前剩余审计为 `7 pass / 22 warn / 0 fail`。
- 后续迁移使用 `tools/migrate_asset_organization_via_editor.py` 先 dry-run，再小批量执行；命令行默认不执行 Fix Up Redirectors，真实迁移后需要在 Unreal Editor 的 Content Browser 中手动修复重定向器。

## 已验证项目

- `VRKitchenEditor Win64 Development` C++ 构建通过。
- `CompileAllBlueprints` 蓝图编译通过，要求保持 `0 errors / 0 warnings / 0 failed blueprints`。
- `DataValidation` 资源数据验证通过，要求保持 `Success - 0 errors / 0 warnings`。
- `BuildCookRun` Win64 Development 打包通过。
- 自动化玩法脚本 `tools/verify_demo_gameplay_loop_via_bridge.py` 已覆盖核心 Demo 规则：
- 正确订单成功加分。
- 空盘提交失败并提示“请先放上食材”。
- 生食材提交失败并提示“不能提交未处理食材”。
- 烧焦食材提交失败并提示“食材烧焦了”。
- 缺少食材、多余食材、顺序错误分别失败。
- 倒计时结束后不能继续加分或增加正确订单数。
- 倒计时结束后可通过重置重新开始。
- 达到目标分后会进入任务完成结算，显示评级和最佳连击。
- 连续完成至少 3 单后订单难度递进到包含切配食材，后续还能进入厚肉和双肉订单。
- 煎锅离开灶台不烹饪，回到灶台后可以继续煎熟，熟肉继续受热会烧焦。
- 会话组件暴露阶段文本、紧张度、下一目标和教程提示，自动化会检查这些信息可调用且会随进度变化。

## 自动化验证说明

- 最近一次增强玩法验证时间：2026-05-30。
- Unreal 命令行返回 `Success - 0 error(s)`。
- 命令行环境中可能出现 USD 插件路径、OpenXR/SteamVR Runtime 或 Steam 日志写入警告；这些属于当前无头显/无完整 SteamVR 运行环境下的环境噪声，不等同于玩法脚本失败。
- 结算阶段支持按 `R` 重新开始一局。
- 如果后续修改蓝图或地图，请至少重新运行 C++ 构建、蓝图编译、数据验证、玩法脚本和 Win64 打包。

## 交付前自检

每次完成一轮新目标、准备推送 GitHub 或上传网盘前，建议先运行：

```powershell
python ..\tools\verify_delivery_readiness.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen --code-repo-root C:\Users\hp\Desktop\VRKitchen_CodeOnly
```

脚本只做文件和配置层面的交付边界检查：完整工程是否包含 Demo 地图、源码、配置、插件和说明；代码版仓库是否没有误跟踪 `Content`、`.uasset`、`.umap`、二进制输出和大文件。它不能替代 C++ 构建、蓝图编译、DataValidation、玩法自动化、Win64 打包和真实头显测试。

资源整理审计可以运行：

```powershell
python tools\verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen
```

该脚本默认只给出警告，不移动资源；等完成 Unreal Editor 内迁移和引用修复后，可加 `--strict` 作为最终项目结构门禁。

如果需要输出可读迁移清单，可运行：

```powershell
python tools\verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_AUDIT.md
```

如果需要先预演下一批迁移，可运行：

```powershell
$env:VRKITCHEN_ASSET_MIGRATION_PHASES='phase-1,phase-2-prototypes'
$env:VRKITCHEN_ASSET_MIGRATION_DRY_RUN='1'
$env:VRKITCHEN_ASSET_MIGRATION_REPORT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN.json'
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\migrate_asset_organization_via_editor.py' -unattended -nop4 -nosplash -NullRHI
```

## 未验证项目

- 真实 SteamVR 头显运行体验。
- VR 手柄抓取、叠放、切菜、出餐区交互手感。
- Quest/Android 独立运行。

## 交付方式

- 完整工程通过网盘交付，必须包含 `Content`、`Config`、`Source`、`Plugins` 和 `VRKitchen.uproject`。
- GitHub 仓库只放代码、配置、说明和小工具，不上传 `Content` 大资源、`.uasset`、`.umap`、`Binaries`、`Intermediate`、`Saved`、`DerivedDataCache`。
- 当前 GitHub 仓库地址为 `https://github.com/Crossng/VRKitchen.git`。

## 建议上传网盘时排除

- `Intermediate`
- `Saved`
- `DerivedDataCache`
- `Binaries`

这些目录可以重新生成；如果担心接收方没有编译环境，可以额外保留 `Binaries`，但包体会更大。
