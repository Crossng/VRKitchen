# VRKitchen

> 基于 Unreal Engine 5.5.4 的 PCVR 厨房交互演示项目。

[![项目状态：已结项](https://img.shields.io/badge/status-completed-2ea44f?style=flat-square)](https://github.com/Crossng/VRKitchen)
[![Unreal Engine 5.5.4](https://img.shields.io/badge/Unreal%20Engine-5.5.4-313131?style=flat-square&logo=unrealengine)](https://www.unrealengine.com/)
[![平台：Windows PCVR](https://img.shields.io/badge/platform-Windows%20PCVR-0078D4?style=flat-square)](https://github.com/Crossng/VRKitchen)
[![维护检查](https://github.com/Crossng/VRKitchen/actions/workflows/maintenance.yml/badge.svg)](https://github.com/Crossng/VRKitchen/actions/workflows/maintenance.yml)

VRKitchen 是一个面向 PCVR 的厨房交互演示项目。玩家需要接收订单、处理食材、完成烹饪和装盘，并在规定时间内提交正确菜品。项目已完成既定演示目标，当前仓库作为结项版本的源代码与交付归档使用。

## 项目状态

本项目已经结项，不再进行常规功能开发。仓库保留以下内容：

- Unreal Engine C++ 源代码
- 项目配置和插件配置
- 交付检查、内容验证和资源审计工具
- 项目运行、资源整理和交付说明

完整 Unreal 工程资源体积较大，继续通过百度网盘提供，不直接提交到 GitHub。

## 完整工程下载

完整工程源文件（`VRCrazyKitchen.zip` 等 2 个文件）：

- [百度网盘下载](https://pan.baidu.com/s/1FlrQ5vl0GHLvo42fHb5gmA?pwd=rdnf)
- 提取码：`rdnf`

下载并解压后，请按照[快速开始](#快速开始)打开项目。GitHub 中的代码可以覆盖/合并到完整工程中，以使用仓库中的最新源代码版本。

## 项目内容

- 中文订单板与订单反馈
- 食材拿取、切配、烹饪、装盘和出餐流程
- 汉堡、牛排、田园沙拉以及多种组合订单
- 生肉、生肉饼、切好蔬菜和沙拉酱的完整处理链路
- 严格的食材状态、数量和装盘顺序校验
- 生食材、未切食材、烧焦食材和错误顺序的失败反馈
- 3 分钟回合、目标分数、错误扣分、连击奖励和星级结算
- 当前目标、工位路线、配方卡、出餐检查清单和新手提示
- 盘面清理与食材回收流程

## 技术规格

| 项目 | 内容 |
| --- | --- |
| 引擎 | Unreal Engine 5.5.4 |
| 运行平台 | Windows PCVR |
| VR 运行时 | SteamVR / OpenXR |
| Demo 地图 | `/Game/_Project/Maps/VRKitchen_Demo` |
| 主要代码 | C++、Blueprint |
| 辅助工具 | Python |

## 快速开始

1. 从上面的百度网盘链接下载完整工程并解压。
2. 如需使用 GitHub 中的源代码，将仓库内的 `VRKitchen/` 文件夹合并到完整工程根目录。保留完整工程的 `Content/` 资源，不要把资源目录提交回 GitHub。
3. 使用 Unreal Engine 5.5.4 打开 `VRKitchen/VRKitchen.uproject`。
4. 使用 SteamVR 时，将 SteamVR 设置为 OpenXR Runtime，并连接 PCVR 头显。
5. 运行地图 `/Game/_Project/Maps/VRKitchen_Demo`。

没有头显时，也可以在编辑器中进行代码编译、蓝图编译、数据验证和 Win64 打包验证，但无法替代真实 VR 操作体验测试。

## 仓库结构

```text
VRKitchen/
├── Config/                         项目配置
├── Plugins/UnrealBridge/            Unreal Editor 辅助插件
├── Source/VRKitchen/               VRKitchen C++ 源代码
└── VRKitchen.uproject               Unreal 项目文件

tools/
├── verify_demo_gameplay_loop_via_bridge.py      玩法流程验证
├── verify_demo_content_design_via_bridge.py     Demo 内容验证
├── verify_demo_map_content_via_bridge.py        Demo 地图验证
├── verify_demo_menu_quality_via_bridge.py      菜单质量验证
├── verify_delivery_readiness.py                 交付边界检查
└── verify_asset_organization.py                 资源整理审计
```

## 结项验证记录

结项版本曾完成以下验证：

- `VRKitchenEditor Win64 Development` C++ 构建
- `CompileAllBlueprints` 蓝图编译
- `DataValidation` 资源数据验证
- Win64 Development 打包
- Demo 地图核心 Actor 和空间关系检查
- 九道菜菜单、沙拉、套餐和三星结算流程检查
- 烹饪、烧焦、切菜、装盘顺序和错误反馈检查

仓库本身还提供轻量级的代码检查：

```bash
python3 -m compileall -q tools
python3 -m unittest discover -s tools/tests -p 'test_*.py'
python3 tools/verify_delivery_readiness.py --skip-full-project --code-repo-root .
```

上述检查不需要下载 `Content/`，主要用于确认代码仓库边界和辅助工具没有损坏。完整工程验证请参考 [`VRKitchen_DELIVERY.md`](VRKitchen_DELIVERY.md)。

## 资源提交边界

GitHub 仓库只保存代码、配置、插件源码、说明文档和小型工具。以下内容保留在完整工程或网盘中，不应提交到 GitHub：

- `Content/`
- `Binaries/`
- `Intermediate/`
- `Saved/`
- `DerivedDataCache/`
- `.uasset`、`.umap`、`.fbx`、`.zip`、`.pdb`、`.exe` 等大型资源和构建产物

资源目录规范和迁移说明：

- [`VRKitchen_ASSET_ORGANIZATION.md`](VRKitchen_ASSET_ORGANIZATION.md)
- [`VRKitchen_ASSET_MIGRATION_PLAN.md`](VRKitchen_ASSET_MIGRATION_PLAN.md)

## 许可说明

当前仓库未附带独立的 `LICENSE` 文件。如需复制、修改或再发布项目内容，请联系仓库所有者确认授权范围。
