# 视觉升级 Review 与路线图

记录日期：2026-06-10

## 一句话结论

当前项目已经能用，而且主线方案 A（内置 Windows Terminal 宿主 + Textual/Rich）路线是成立的。但现在的视觉系统仍主要围绕“组件面板 + 文本内容 + 少量字符装饰”组织，所以观感容易回到“框里放字”。下一阶段不应该只是继续增加模板，而应该把“字符像素画布、位图处理、轮廓剪影、装饰图层”升级成一等能力。

建议目标：从“赛博朋克 TUI 仪表盘”升级为“字符像素副屏视觉装置”。

## 当前优势

- 主入口已经收敛到 `dist/DecoScreenBeautifier.exe`，内置 Windows Terminal 宿主的方向清晰。
- Textual 主显示页已经读取布局文件，用户编辑后的布局能真实生效。
- 图片组件已经有 `ascii / pixel` 两种渲染模式，其中 `pixel` 使用半块字符 `▀` 加前景/背景色实现彩色伪像素。
- 轻框视觉层已经开始成型，已有 `variant-rail / corner / ribbon / hero`。
- 模板、字体预设、样式 token、布局数据已经打通，后续扩展不会从零开始。

## 核心问题

### 1. 点阵能力还只是图片组件的一个模式

当前 `ImageProcessor` 的主分支只有 `ascii / pixel`：

- `src/core/layout_config.py` 中 `IMAGE_RENDER_MODES = ("ascii", "pixel")`
- `src/processors/image.py` 中 `render_mode == "pixel"` 时只走半块字符渲染

这意味着用户上传图片以后，系统只能把整张图压进字符格里，还没有“剪影、描边、双色海报化、抖动、透明背景、局部主体提取”等更像视觉设计工具的能力。

建议把图片处理拆成清晰流水线：

1. 读取与方向修正
2. 裁剪/适配目标字符画布
3. 主体 mask 或边缘 mask
4. 风格处理：剪影、边缘、双色、抖动、低色阶、扫描线
5. 字符栅格化：ASCII、半块像素、Braille、quadrant block
6. Rich Text 输出与缓存

### 2. 轻框 chrome 还只是 header/footer，不是完整图形语言

`src/components/chrome.py` 现在主要生成标题 chip、横线、footer。它能减少重边框，但还不能做更强的图形组织，例如：

- 角标坐标
- 断裂线框
- 斜切轨道
- 十字准星
- 背景网格
- 模块之间的连接线
- 主视觉旁的扫描标尺

下一步应该新增“装饰组件/图形层”，而不是继续把所有装饰塞进每个业务组件内部。

### 3. 当前平铺网格天然限制惊艳程度

主显示页会按网格逐格挂载组件，并跳过重叠组件。这个模型稳定，但限制了：

- 大图作为背景，数据块覆盖其上
- 半透明/留空式装饰
- 组件之间跨区域连接
- 图片剪影穿插到信息栏背后

建议演进为三层模型：

- `Backdrop Layer`：全屏点阵背景、扫描线、噪声、用户图像轮廓
- `Decoration Layer`：角标、轨道、标尺、准星、分隔线、信号流
- `Widget Layer`：CPU、网络、时钟、音频等真实信息组件

短期可以先用“一个全屏装饰组件 + 现有网格组件”的方式验证，不必一次性重写渲染器。

### 4. 装饰内容太随机，缺少可命名的视觉资产

`DataStreamWidget` 目前每帧生成随机字符流。它有动态氛围，但缺少可控的设计意图。建议增加可命名资产：

- `DotMatrixWidget`：可配置密度、方向、脉冲、空洞形状
- `ScanGridWidget`：背景网格/标尺/坐标轴
- `CrosshairWidget`：十字准星/扫描窗口
- `CircuitTraceWidget`：电路走线式装饰
- `SilhouetteWidget`：人物/物体剪影点阵海报
- `GlyphLogoWidget`：内置 logo / 标记 / 文字锁定图形

这样模板可以组合“视觉资产”，而不是只组合“信息组件”。

### 5. 用户上传人物剪影需要 mask 能力

“上传一张图，提取人物剪影，生成像素画轮廓”可以分三档实现：

- 轻量版：OpenCV 灰度阈值、边缘检测、GrabCut，适合背景干净的图片。
- 实用版：新增可选 `rembg` / ONNX U2Net，用本地模型自动抠主体，适合普通照片。
- 高级版：用户可在编辑器里调 threshold、edge、dilate/erode、反相、双色调，并实时预览。

建议先做轻量版，保证无重依赖；再把 `rembg` 做成可选增强能力。

## 推荐路线

### 阶段 A：点阵图像管线增强

目标：让图片组件从“能显示图片”变成“能做风格化主视觉”。

建议新增：

- `image_effect_mode`
  - `none`
  - `silhouette`
  - `edge`
  - `duotone`
  - `dither`
  - `posterize`
- `image_palette`
  - 使用主题 token，例如 `primary/accent/background`
  - 或用户指定双颜色
- `image_threshold`
- `image_edge_strength`
- `image_invert`
- `image_background`
  - `transparent`
  - `solid`
  - `theme`

技术建议：

- 在 `ImageProcessor` 中拆出 `ImageRenderOptions`，避免继续把参数平铺到方法签名。
- 新增 `process_array_to_cells()` 之类的中间层，未来可服务 GIF、静态图片、装饰背景。
- 给图片处理加缓存 key：路径、mtime、目标宽高、display mode、render mode、effect options、theme palette。
- 把 GIF 帧也并入同一条处理链。

### 阶段 B：剪影/轮廓功能 MVP

目标：用户可以导入人物图，得到酷炫的像素剪影。

建议交互：

1. 用户添加 `SilhouetteWidget` 或在图片组件选择 `Effect = Silhouette`
2. 选择图片
3. 设置 `Threshold / Edge / Invert / Palette`
4. 预览
5. 保存布局

技术路线：

- MVP：OpenCV 灰度阈值 + 形态学闭运算 + 边缘描边。
- 进阶：GrabCut 自动分割，允许用户选择主体大致区域。
- 可选增强：`rembg` 本地模型，作为安装包增强项或首次使用时提示安装。

### 阶段 C：装饰图层与图形组件

目标：摆脱“框配文字”，让界面出现真正的构图。

优先新增 3 个组件：

- `BackdropPatternWidget`
  - 全屏/大跨度背景点阵、噪声、扫描线、低密度网格。
- `DotMatrixArtWidget`
  - 渲染用户图片、剪影、logo、图标，支持透明/主题色。
- `HudDecorWidget`
  - 十字准星、角标、坐标、斜切线、扫描框。

模板设计原则：

- 每套模板只保留 1 个主视觉中心。
- 大部分信息组件使用轻框或无框。
- 背景层低对比，装饰层中对比，关键数据高对比。
- 让空白参与设计，不要填满每个格子。

### 阶段 D：布局模型升级

目标：给惊艳效果留出空间。

短期：

- 支持“大跨度背景组件”。
- 模板预设里显式区分 `background / decoration / data`。
- 编辑器里用标签区分组件用途。

中期：

- 从单一平铺网格演进到 `stage + layers`。
- 允许背景/装饰组件覆盖多个普通组件下方。
- 增加 `z_index`、`opacity-like palette dimming`、`blend_mode` 的配置语义。

长期：

- 考虑统一字符画布合成器：所有组件先渲染到 cell buffer，再按图层合成。
- 这样可以真正支持重叠、透明、遮罩、局部高亮，但工程量较大。

## 优先级建议

P0：

- 为 `ImageProcessor` 增加 `silhouette / edge / dither / duotone` 的基础处理。
- 为图片组件与编辑器增加对应参数。
- 新增测试覆盖输出尺寸、阈值、奇偶高度、空图/坏路径。

P1：

- 新增 `DotMatrixArtWidget` 与 `BackdropPatternWidget`。
- 新增 2 套“无重框”的展示模板，例如 `Silhouette Deck`、`Signal Shrine`。
- GIF 帧并入静态图片的新渲染链。

P2：

- 层级布局与 cell buffer 合成器。
- 可选本地主体分割依赖。
- 模板预览缩略图与风格包系统。

## 产品方向建议

这个项目真正有辨识度的方向不是“终端里显示系统信息”，而是：

> 用户把副屏变成自己的赛博风格像素仪表/海报装置。

所以后续功能最好围绕几个用户故事组织：

- 我想把喜欢的角色/机箱照片变成副屏像素剪影。
- 我想让 CPU、网络、音频数据像 HUD 一样围绕主视觉动起来。
- 我想一键套用几套强风格模板，而不是自己手调十几个参数。
- 我想在不同副屏比例下快速得到构图合理的版本。

只要这条线立起来，项目会从“实用工具”变成“有审美记忆点的桌搭产品”。
