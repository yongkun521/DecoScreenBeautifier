# Textual UI V2 实施清单

> 目标：在保留现有组件库、模板体系与字体/样式预设兼容性的前提下，为 Textual 主界面增加“轻框图形”视觉层，并重做图片组件的显示观感。

## 阶段 1：图片渲染链路

- [x] `image_render_mode` 接入布局数据与组件创建链路
- [x] 图片组件新增 `pixel` 模式
- [x] `global_scale` 改为仅影响采样密度
- [x] 编辑器新增 `Image Render`
- [x] 编辑器新增 `Visual Variant`
- [x] 单测覆盖 `ascii / pixel` 输出尺寸与布局兼容行为
- [x] 已完成 commit

## 阶段 2：轻框图形视觉层

- [x] 新增共享 chrome helper
- [x] 新增 `variant-rail / corner / ribbon / hero`
- [x] 改造核心组件的轻框渲染路径
- [x] 新增 2 套 UI V2 模板
- [x] 完成阶段 commit

## 阶段 3：收口与文档

- [ ] 补充更多回归测试
- [ ] 更新 `docs/自定义界面说明.md`
- [ ] 更新 `docs/观察但未处理的问题.md`
- [ ] 收口 `docs/Todolist.md`
- [ ] 完成阶段 commit
