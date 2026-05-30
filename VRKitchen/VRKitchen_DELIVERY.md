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
- 错误订单会显示中文原因，包括具体缺少/多出的食材、沙拉或套餐顺序错误、未知食材、未切蔬菜、未煎熟肉类和烧焦肉类。
- 生肉饼和生肉可以在煎锅 + 灶台上烹饪，完成后显示“已煎熟”。
- 熟肉继续停留在热锅上会烧焦，烧焦食材不能通过订单。
- Demo 回合默认 3 分钟，目标 115 分，正确订单 +10 分，错误订单默认 -2 分且不扣到负数。
- Demo 有目标分、连击奖励、任务完成和星级结算；二星门槛 55 分，三星/目标完成门槛 115 分，达到目标分后会停止继续提交并显示挑战成功。
- 订单会随正确完成数递进：前期经典汉堡，中期加入香煎牛排、田园沙拉、生菜汉堡和番茄汉堡，后期进入厚肉生菜堡、豪华双肉堡、牛排沙拉套餐和经典汉堡沙拉套餐。
- Demo 会话组件会暴露菜单路线、当前菜品和菜单进度文本，例如 `1/9 经典汉堡` 到 `9/9 经典汉堡沙拉套餐`，用于订单板/UI 展示和自动化验收。
- Demo 会话组件还会暴露当前订单所需食材、推荐操作步骤、失败修复建议和综合玩家目标文本，用于把“下一步该做什么”直接显示给玩家。
- Demo 会话组件会暴露当前菜品工位路线文本，提示玩家该去面包台、蔬菜区、切菜板、煎锅/灶台、装盘区还是出餐区；沙拉会明确提示“冷菜，不用煎锅”。
- Demo 会话组件会暴露当前菜品配方卡文本，包含菜品类型、处理要求、叠盘顺序和常见错误；沙拉配方卡会说明它是冷菜，需要切菜板处理，不需要煎锅。
- Demo 会话组件会暴露阶段学习路径文本，包括当前阶段为什么解锁、还差几单进入下一阶段、下一阶段预告和整条菜单路线状态。
- Demo 会话组件会暴露本局复盘文本，包括总提交数、准确率、错误复盘、最佳连击和下一局练习重点，结算后可直接显示给玩家。
- 香煎牛排已经作为正式菜单接入，要求提交“熟牛肉”，用于教学煎锅和灶台烹饪。
- 田园沙拉已经作为正式菜单接入，要求按顺序提交“切好的生菜, 切好的番茄”，不需要煎锅。
- 套餐订单已经作为后期挑战接入：牛排沙拉套餐要求“熟牛肉, 切好的生菜, 切好的番茄”，经典汉堡沙拉套餐要求“底部面包, 熟肉饼, 顶部面包, 切好的生菜, 切好的番茄”。
- 运行时会显示中文新手提示、剩余时间、分数、完成数、错误数、当前阶段、紧张度和下一目标。
- 时间进入 45 秒内会提示“注意时间”，进入 20 秒内会提示“最后冲刺”；教程文本会随订单阶段和错误恢复动态变化。
- Demo 地图入口已经整理为 `/Game/_Project/Maps/VRKitchen_Demo`。
- 资源整理规范已经写入 `VRKitchen_ASSET_ORGANIZATION.md`，第一阶段迁移路线写入 `VRKitchen_ASSET_MIGRATION_PLAN.md`；当前剩余审计为 `7 pass / 24 warn / 0 fail`，下一批建议只 dry-run `Collections`、`Developers` 和 `food_test` 归入 `_Dev`。
- 后续迁移使用 `tools/migrate_asset_organization_via_editor.py` 先 dry-run，再小批量执行；命令行默认不执行 Fix Up Redirectors，真实迁移后需要在 Unreal Editor 的 Content Browser 中手动修复重定向器。

## 已验证项目

- `VRKitchenEditor Win64 Development` C++ 构建通过。
- `CompileAllBlueprints` 蓝图编译通过，要求保持 `0 errors / 0 warnings / 0 failed blueprints`。
- `DataValidation` 资源数据验证通过，要求保持 `Success - 0 errors / 0 warnings`。
- `BuildCookRun` Win64 Development 打包通过。
- 自动化玩法脚本 `tools/verify_demo_gameplay_loop_via_bridge.py` 已覆盖核心 Demo 规则：
- 正确订单成功加分。
- 空盘提交失败并提示“请先放上食材”。
- 生食材提交失败并提示具体原因，例如“生菜还没切”“番茄还没切”“牛肉还没煎熟”。
- 烧焦食材提交失败并提示具体原因，例如“肉饼烧焦了”“牛肉烧焦了”。
- 缺少食材、多余食材、顺序错误分别失败，并会显示具体食材名或正确顺序提示。
- 倒计时结束后不能继续加分或增加正确订单数。
- 倒计时结束后可通过重置重新开始。
- 达到目标分后会进入任务完成结算，显示评级和最佳连击。
- 结算复盘会显示准确率、错误次数解释、最佳连击和下一局重点；自动化会分别检查无提交、完美推进、三星完成和带错误通关尝试。
- 连续完成至少 3 单后订单难度递进到香煎牛排，后续还能进入田园沙拉、生菜汉堡、番茄汉堡、厚肉、双肉和套餐订单。
- 香煎牛排覆盖正确提交、生牛肉失败、烧焦牛肉失败和错误菜品失败。
- 田园沙拉覆盖正确提交、未切生菜失败、未切番茄失败、沙拉顺序错误失败和多余面包失败，并检查反馈文本。
- 牛排沙拉套餐和经典汉堡沙拉套餐覆盖正确提交、缺少配菜失败、套餐顺序错误失败和多余食材失败，并检查反馈文本。
- 煎锅离开灶台不烹饪，回到灶台后可以继续煎熟，熟肉继续受热会烧焦。
- 会话组件暴露阶段文本、紧张度、下一目标和教程提示，自动化会检查这些信息可调用且会随进度变化。
- 会话组件暴露完整菜单路线、当前菜单项和菜单进度，自动化会检查沙拉与套餐都在路线中，并检查进度会从经典汉堡推进到牛排、田园沙拉和最终套餐。
- 自动化会检查玩家目标文本包含所需食材、推荐步骤和失败修复建议；例如未煎熟会提示确认煎锅在灶台上，未切蔬菜会提示去切菜板处理，顺序错误会提示重新叠放。
- 自动化会检查工位路线文本会随菜单阶段变化：经典汉堡提示面包台和煎锅/灶台，田园沙拉提示蔬菜区、切菜板和“冷菜，不用煎锅”，套餐提示先热菜再补冷菜配菜。
- 自动化会检查配方卡文本会随菜单阶段变化：经典汉堡、香煎牛排、田园沙拉、牛排沙拉套餐和经典汉堡沙拉套餐都必须暴露菜品类型、处理要求、叠盘顺序和常见错误提醒。
- 自动化会检查阶段学习路径文本会随进度变化：开局预告香煎牛排，牛排阶段预告田园沙拉，套餐阶段预告最终菜单，最终阶段显示已到最终菜单。

## 自动化验证说明

- 最近一次增强玩法验证时间：2026-05-30。
- Unreal 命令行返回 `Success - 0 error(s)`。
- 命令行环境中可能出现 USD 插件路径、OpenXR/SteamVR Runtime 或 Steam 日志写入警告；这些属于当前无头显/无完整 SteamVR 运行环境下的环境噪声，不等同于玩法脚本失败。
- 结算阶段支持按 `R` 重新开始一局。
- 如果后续修改蓝图或地图，请至少重新运行 C++ 构建、蓝图编译、数据验证、玩法脚本和 Win64 打包。

## 交付前自检

每次完成一轮新目标、准备推送 GitHub 或上传网盘前，建议先运行：

```powershell
python C:\Users\hp\Desktop\CrazyKitchen\tools\verify_delivery_readiness.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen --code-repo-root C:\Users\hp\Desktop\VRKitchen_CodeOnly
```

脚本只做文件和配置层面的交付边界检查：完整工程是否包含 Demo 地图、源码、配置、插件和说明；代码版仓库是否没有误跟踪 `Content`、`.uasset`、`.umap`、二进制输出和大文件。它不能替代 C++ 构建、蓝图编译、DataValidation、玩法自动化、Win64 打包和真实头显测试。

资源整理审计可以运行：

```powershell
python C:\Users\hp\Desktop\CrazyKitchen\tools\verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen
```

该脚本默认只给出警告，不移动资源；等完成 Unreal Editor 内迁移和引用修复后，可加 `--strict` 作为最终项目结构门禁。

如果需要输出可读迁移清单，可运行；报告会包含 phase/risk/category 汇总、推荐下一批和 dry-run 命令：

```powershell
python C:\Users\hp\Desktop\CrazyKitchen\tools\verify_asset_organization.py --full-project-root C:\Users\hp\Desktop\CrazyKitchen\VRKitchen --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_AUDIT.md
```

如果需要先预演下一批迁移，可运行：

```powershell
$env:VRKITCHEN_ASSET_MIGRATION_PHASES='phase-1,phase-2-dev-folders,phase-2-prototypes'
$env:VRKITCHEN_ASSET_MIGRATION_DRY_RUN='1'
$env:VRKITCHEN_ASSET_MIGRATION_REPORT='C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN.json'
& 'D:\Program Files (x86)\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' 'C:\Users\hp\Desktop\CrazyKitchen\VRKitchen\VRKitchen.uproject' -run=pythonscript -script='C:\Users\hp\Desktop\CrazyKitchen\tools\migrate_asset_organization_via_editor.py' -unattended -nop4 -nosplash -NullRHI
```

dry-run 结束后必须先验证 JSON 报告，确认没有真实移动资源、没有报错，并且 phase-2 目标移动项都已经被记录：

```powershell
python C:\Users\hp\Desktop\CrazyKitchen\tools\verify_asset_migration_report.py --report C:\Users\hp\Desktop\CrazyKitchen\VRKitchen_ASSET_MIGRATION_DRYRUN.json
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
