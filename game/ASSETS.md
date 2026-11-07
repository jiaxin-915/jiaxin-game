# 素材结构与编辑指南

所有运行图片均位于 `project/assets/`，不存在把整张玩法预览当关卡背景的做法。

| 对象 | 编辑位置 | 说明 |
|---|---|---|
| 海面背景 | assets/ocean.png | 只含海面和远景，无棋盘、按钮或玩家 |
| 首页插画 | sprites/HomeCover | 原封面移除 Start 后的装饰插画 |
| 开始按钮 | sprites/StartButton | 使用独立透明原图，悬停放大 6% |
| 冰面 / 水洞 | sprites/IceTile* / WaterTile* | 每一格是独立对象和造型 |
| 企鹅 | sprites/Penguin | 单独透明素材，按规则移动 |
| 冰岩 / 雪屋 | sprites/Rock* / Igloo | 独立对象 |
| 方向 / 重试 / 首页按钮 | sprites/*Button | 单独造型，点击跟随精灵当前位置和尺寸 |
| 标题、提示、步数 | GameTitle / *Hint / MoveDigit* | 与背景分离，计步从运行数据读取 |
| 结果页面 | ResultShade / ResultPanel / *Message | 遮罩、面板、提示、按钮分离 |
| 声音开关 | SoundOnButton / SoundOffButton | 根据静音状态切换显示 |
| 声音 | assets/sounds | 每个声音独立目录和配置 |

## 修改方式

在 XBuilder 中替换任一精灵的造型，其他对象不受影响。按钮可在编辑器中移动，点击不依赖舞台写死的矩形坐标；悬停根据精灵当前位置和初始显示尺寸检测，缩放基准取自对象初始大小。

关卡不是一张背景图。改变障碍布局时，应同时修改 `game/levels/level-01.json` 并重新生成，以保持格子规则和画面一致；只在编辑器拖动冰岩会改变外观，但不会自动改写格子逻辑。原始图片始终保留在 `assets/source/`。

首页插画中的企鹅、雪屋和树是装饰图案；实际游戏中的角色、终点和障碍使用各自独立素材。首页 Start 已完全从插画中移除。
