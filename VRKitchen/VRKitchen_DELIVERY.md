# VRKitchen SteamVR 演示交付说明

## 项目定位

本版本是 UE 5.5.4 的 VRKitchen 演示可交付版，目标运行环境是 Windows PCVR + SteamVR/OpenXR。当前重点是展示完整玩法闭环：接订单、处理食材、煎锅烹饪、叠盘、提交订单、正确/错误反馈和连续订单流程。

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
- Demo 地图入口已经整理为 `/Game/_Project/Maps/VRKitchen_Demo`。

## 已验证项目

- `VRKitchenEditor Win64 Development` C++ 构建。
- `CompileAllBlueprints` 蓝图编译。
- `DataValidation` 资源数据验证。
- `BuildCookRun` Win64 Development 打包。
- 基础玩法流程：正确订单、错误订单、缺少/多余食材、生食材失败、连续订单、灶台烹饪状态。

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
