# Penguin Home Journey 工程说明

原生 XGo/spx 工程，舞台 480×360。`project/` 是 XBuilder 导入包的根目录；最新包为 `Penguin-Home-Journey-v0.3.3.xbp`。

## 工程结构

- `project/main.spx`：格子运动、状态、输入和音频切换。
- `project/Penguin.spx`：企鹅移动及落水缩小。
- `project/*Button.spx`：独立按钮显示与悬停；命中通过 按钮当前位置和造型尺寸 获取。
- `project/assets/sprites/`：各独立素材、造型及位置配置。
- `project/assets/sounds/`：7 个独立声音及配置。
- `levels/level-01.json` 至 `level-05.json`：五关数据；最短解分别为 5、3、4、5、6 步。
- `platform-text.json`：中文项目名称、描述及操作说明。
- `ui-source/`：可编辑 SVG；渲染结果作为独立 PNG 造型。

## 复现命令

在仓库根目录执行，需要 Python 3、Node.js、sharp 0.35.5 和 Go：

```sh
npm install
python3 game/tools/build_project.py
node game/tools/render_ui.cjs
python3 game/tools/check_logic.py --go /absolute/path/to/go
python3 game/tools/package_project.py
python3 game/tools/package_project.py --check
```

生成器会重建精灵目录和生成脚本，保留 main.spx 与 Penguin.spx；修改生成的 UI 时应同步修改生成器，否则重建会覆盖修改。下载和处理后的声音已归档，重建不需要联网。

## 编辑、验证与发布

[素材编辑指南](ASSETS.md) · [音频来源](AUDIO-CREDITS.md) · [试玩记录](PLAYTEST.md)

先本地修改与打包，再导入自己的 XBuilder 项目验证。GitHub 与平台不会自动同步。平台运行后的最终版本需另行导出回存，得到发布确认后再发布。

核心函数的 Go 测试不能代替 XGo 编译和实际音画试玩。v0.3.3 已在 XBuilder 完成导入与试玩验收；正式发布仍需另行授权。
