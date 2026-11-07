# 阶段 2 验证记录

日期：2026-11-07。此记录严格区分逻辑验证和实际引擎运行。

## 已通过

1. TestAllCellsDirectionsAndFrameRates：遍历所有可站立格子、四方向及 5 种时间步长，与逐格扫描结果比较。
2. TestDocumentedSolution：按文档 5 步到家，终局拒绝继续移动。
3. TestBusyResetHomeAndInvalidInput：滑动中锁定输入，无效方向不计步，重试/首页清除运动状态。
4. TestWaterAndGoalStopBeforeFurtherCells：不跳过水格或终点格。
5. TestShortestSolutionByBFS：按生产移动函数求最短解，确认 5 步。
6. package_project.py：18 个 sprite、132 个文件，配置尺寸与 PNG 一致，资源路径与层级完整，所有 ZIP 文件与源文件逐字节一致。

## 规范依据

- https://github.com/goplus/builder/blob/dev/gui/src/utils/spx/skills/spx-project/SKILL.md
- https://github.com/goplus/builder/blob/dev/gui/src/models/spx/project.ts
- https://github.com/goplus/builder/blob/dev/gui/src/components/project/runner/ProjectRunner.vue

核对重点：main.spx、精灵脚本、assets/index.json、各精灵 index.json、builder-meta.json、builder-thumbnail.png 和 ZIP 根目录布局；关闭物理模拟，以格子规则控制碰撞。

## 未完成的引擎验收

Safari 正式站能读取已登录账号的项目列表，但创建窗口无法稳定操作，页面反复为空白。没有成功创建/覆盖线上项目。尚未确认：

- `.xbp` 在生产站导入是否接受；
- 当前生产版 XGo 编译是否通过；
- spx 实际尺寸、层级、坐标和输入是否按预期运行；
- 首页、完整 5 步通关、落水和重试的真实游戏截图。

因此当前交付是待引擎适配的本地最小版本，不应称为已在线验收或已发布。

## 用户导入反馈与修复

用户导入后，生产站报 main.spx:7:5 Board conflicts with class name，随后出现索引及赋值类型错误。根因是舞台数组 Board 与 Board 精灵类同名。

本地将数组统一改为 LevelCells，同步更新生成器和测试，并在打包器新增舞台字段与精灵类名称冲突检查。本次仅修复该编译冲突；实际引擎复测和独立素材拆分仍待完成。
