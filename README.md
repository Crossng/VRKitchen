<div align="center">

# VRKitchen

### Unreal Engine 5.5.4 · Windows PCVR 厨房交互演示项目

<p>
  <a href="https://github.com/Crossng/VRKitchen"><img src="https://img.shields.io/badge/%E9%A1%B9%E7%9B%AE%E7%8A%B6%E6%80%81-%E5%B7%B2%E7%BB%93%E9%A1%B9-2ea44f?style=flat-square" alt="项目状态：已结项"></a>
  <a href="https://www.unrealengine.com/"><img src="https://img.shields.io/badge/Unreal%20Engine-5.5.4-313131?style=flat-square&logo=unrealengine" alt="Unreal Engine 5.5.4"></a>
  <a href="https://github.com/Crossng/VRKitchen"><img src="https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0-Windows%20PCVR-0078D4?style=flat-square" alt="平台：Windows PCVR"></a>
  <a href="https://github.com/Crossng/VRKitchen/actions/workflows/maintenance.yml"><img src="https://github.com/Crossng/VRKitchen/actions/workflows/maintenance.yml/badge.svg" alt="仓库检查"></a>
</p>

<p>
  <strong>接收订单 → 处理食材 → 烹饪 → 按序装盘 → 出餐结算</strong>
</p>

<p>
  <strong>简体中文</strong>
  ·
  <a href="README.en.md">English</a>
</p>

</div>

---

## 项目简介

VRKitchen 是一个面向 Windows PCVR 的厨房交互演示项目。玩家需要根据订单完成食材处理、烹饪、装盘和出餐，在限定时间内完成尽可能多的正确订单。

项目已完成既定目标并正式结项。本仓库作为结项版本的代码归档，保留源代码、配置、插件源码、验证工具和项目文档；完整工程资源通过百度网盘单独提供。

## 项目一览

| 项目 | 内容 |
| --- | --- |
| 项目状态 | 已结项 / 归档版本 |
| 开发引擎 | Unreal Engine 5.5.4 |
| 运行平台 | Windows PCVR |
| VR 运行时 | SteamVR / OpenXR |
| Demo 地图 | `/Game/_Project/Maps/VRKitchen_Demo` |
| 主要技术 | C++、Blueprint、Python 工具 |

## 完整工程下载

> [!IMPORTANT]
> GitHub 只保存代码和小型工具，完整 Unreal 工程资源请从百度网盘下载。

完整工程源文件（`VRCrazyKitchen.zip` 等 2 个文件）：

<div align="center">

### [⬇️ 下载完整工程](https://pan.baidu.com/s/1FlrQ5vl0GHLvo42fHb5gmA?pwd=rdnf)

**提取码：`rdnf`**

</div>

## 演示内容

### 核心玩法

- 中文订单板、订单反馈和出餐结果
- 食材拿取、切配、烹饪、装盘与提交
- 生菜、番茄的切配，以及生肉、生肉饼的煎制
- 沙拉酱添加和冷菜制作流程
- 严格的食材状态、数量和装盘顺序校验
- 生食材、未切食材、烧焦食材和错误顺序的失败反馈
- 盘面清理与食材回收

### 菜单路线

```text
经典汉堡
   ↓
香煎牛排
   ↓
田园沙拉
   ↓
生菜汉堡 · 番茄汉堡
   ↓
厚肉生菜堡 · 豪华双肉堡
   ↓
牛排沙拉套餐 · 经典汉堡沙拉套餐
```

### 回合与结算

- 3 分钟演示回合
- 正确订单加分，错误订单扣分
- 连续完成订单可获得连击奖励
- 根据分数进行一星、二星和三星结算
- 结算界面提供完成数、错误数、准确率、最佳连击和练习建议

## 快速开始

1. 从上面的百度网盘链接下载完整工程并解压。
2. 如需使用 GitHub 中的最新代码，将仓库内的 `VRKitchen/` 文件夹合并到完整工程根目录。
3. 保留完整工程的 `Content/` 资源，不要将资源目录或构建产物提交回 GitHub。
4. 使用 Unreal Engine 5.5.4 打开 `VRKitchen/VRKitchen.uproject`。
5. 使用 SteamVR 时，将 SteamVR 设置为 OpenXR Runtime，并连接 PCVR 头显。
6. 运行地图 `/Game/_Project/Maps/VRKitchen_Demo`。

没有头显时，可以进行代码编译、蓝图编译、数据验证和 Win64 打包验证，但无法替代真实 VR 操作体验测试。

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

<details>
<summary>查看仓库轻量级检查命令</summary>

这些检查不需要下载 `Content/`，用于确认 Python 工具语法、仓库边界和基础回归测试：

```bash
python3 -m compileall -q tools
python3 -m unittest discover -s tools/tests -p 'test_*.py'
python3 tools/verify_delivery_readiness.py --skip-full-project --code-repo-root .
```

完整工程验证请参考 [`VRKitchen_DELIVERY.md`](VRKitchen_DELIVERY.md)。

</details>

## 资源提交边界

GitHub 仓库只保存代码、配置、插件源码、说明文档和小型工具。以下内容保留在完整工程或网盘中：

- `Content/`
- `Binaries/`
- `Intermediate/`
- `Saved/`
- `DerivedDataCache/`
- `.uasset`、`.umap`、`.fbx`、`.zip`、`.pdb`、`.exe` 等大型资源和构建产物

资源目录规范和迁移说明：

- [`VRKitchen_ASSET_ORGANIZATION.md`](VRKitchen_ASSET_ORGANIZATION.md)
- [`VRKitchen_ASSET_MIGRATION_PLAN.md`](VRKitchen_ASSET_MIGRATION_PLAN.md)

## 相关文档

- [`VRKitchen_DELIVERY.md`](VRKitchen_DELIVERY.md)：运行环境、交付内容和验证记录
- [`VRKitchen_ASSET_ORGANIZATION.md`](VRKitchen_ASSET_ORGANIZATION.md)：资源目录与命名规范
- [`VRKitchen_ASSET_MIGRATION_PLAN.md`](VRKitchen_ASSET_MIGRATION_PLAN.md)：资源迁移计划与注意事项

## 许可说明

当前仓库未附带独立的 `LICENSE` 文件。如需复制、修改或再发布项目内容，请联系仓库所有者确认授权范围。
