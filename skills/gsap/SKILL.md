---
name: gsap
description: 编写、调试或审查 GSAP 动画，包括时间线、ScrollTrigger、React/Vue/Svelte 集成、插件和性能。用于用户指定 GSAP，或当前待改动画已使用 GSAP 时；普通 CSS 动效或已选择其他动画库的任务不自动切换技术方案。
---

# GSAP

沿用项目的 GSAP 版本、框架和动画设计。根据实际问题只读取下表相关资料；无需先读全部专题。

| 当前任务 | 参考资料 |
| --- | --- |
| Tween、缓动、变换、响应式与 reduced motion | [Core](references/core.md) |
| 顺序、并行动画、position 参数与播放控制 | [Timeline](references/timeline.md) |
| 滚动绑定、scrub、pin、刷新与清理 | [ScrollTrigger](references/scrolltrigger.md) |
| React 的 useGSAP、作用域和组件卸载 | [React](references/react.md) |
| Vue、Nuxt、Svelte 等生命周期 | [Frameworks](references/frameworks.md) |
| Flip、Draggable、SVG、文字等插件 | [Plugins](references/plugins.md) |
| 插值、映射、吸附和其他辅助函数 | [Utils](references/utils.md) |
| 已观察到的卡顿、布局开销或动画资源泄漏 | [Performance](references/performance.md) |

只改请求涉及的动画，保留必要的作用域、卸载清理和无障碍行为。按变化检查实际页面的播放、交互或滚动结果；框架构建成功不能代替视觉检查。

这些资料整理自仓库固定的 GSAP 官方 Skills 快照，原有专题正文保留为参考；涉及版本、接口或许可变化时核对项目安装版本及官方资料。
