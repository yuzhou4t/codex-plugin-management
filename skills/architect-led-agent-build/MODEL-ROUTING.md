# 模型选择

启动执行者或独立 reviewer 时显式指定 harness、model 和适用的 effort，并核对实际启动值。用户点名优先，以下是未另行指定时的约定。

| 用户选择 | 参数 |
| --- | --- |
| Astra | `--harness codex --model gpt-6-astra --effort high` |
| Codex，未点名模型 | `--harness codex --model gpt-6.1-sol --effort xhigh` |
| Grok Build | `--harness grok --model grok-4.7-xhigh` |
| Cursor AO / CLI | `--harness cursor --model grok-4.7-xhigh` |
| Cloud Agent / Background Composer | `model: grok-4.7`，`model_params: {"reasoning_effort":"xhigh"}`；续跑或 reply 同样显式传参 |

保留用户的模型限制：助手及被委派者不使用 Claude 系列或 Claude API，包括 Sonnet、Opus、Haiku、Fable，以及可能落到 Claude 的 default / auto。用户本人在自己 IDE 里的选择不代表授权助手代开或推荐。Cloud 省略模型曾落到 Sonnet，不能省略。

参数以当前工具帮助核实。启动失败先查模型 ID、参数和版本并在授权内修复，不立即断言模型不可用；实际用了错误模型就停止该执行并纠正。确需更换用户指定模型时询问，独立工作继续。`ao review trigger` 也适用，不能依赖未经核实的默认 reviewer。

视觉或指定实现者变更时，先按 [分工交接](FAIL-COORDINATION.md) 移交写入范围，任务只覆盖约定的视觉、交互或其他部分。
