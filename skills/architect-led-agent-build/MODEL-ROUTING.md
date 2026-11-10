# 模型硬禁令与路由

**启动前必读**（派 `ao spawn` / Cloud / review trigger 之前）。工人任务书只写本票指定的 harness/model/effort，不附本文件全文。

## 硬禁令（Claude）

不论何种路径、默认或 Auto，编排助手与一切被派活代理**不得使用 Claude 系列模型或 Claude API**（含 `claude-*`、`sonnet`、`opus`、`haiku`、`fable`，以及会落到 Claude 的 `default`/`auto`）。

- **只有用户本人**可在其自己的 IDE/账号界面选用 Claude；助手不得代开、不得建议、不得因「列表默认 / 省事 / 任务难」改用 Claude。
- **用户点名优先，禁止擅自换模。** 每次 `ao spawn` / `ao review trigger` / Cloud 启动都显式传 harness、model、适用的 effort；启动后核对实际值。模型不可用时报告阻塞并继续独立工作，**不要**静默改用相近模型或 Auto。
- 误落到禁用模型时立即停止该执行。指定模型未启动时，先按公开帮助核实模型 id、参数表达与版本，进行已有授权内的小范围修复；确需换模型、新权限或用户账号操作时才问。启动失败本身不能证明模型不可用；不得静默换模型或 Auto，其余独立任务继续。

## 路由表（实现者与 reviewer 同一套）

| 用户意图 | 参数 |
| --- | --- |
| **Astra** | `--harness codex --model gpt-6-astra --effort high`（不要换成 Sol，也不沿用旧 xhigh） |
| Codex 且未另点名模型 | `--harness codex --model gpt-6.1-sol --effort xhigh` |
| **Grok Build** | `--harness grok --model grok-4.7-xhigh` |
| **Cursor**（AO / CLI） | `--harness cursor --model grok-4.7-xhigh` |
| **Cloud Agent / Background Composer** | `model: grok-4.7` 且 `model_params: {"reasoning_effort":"xhigh"}`。**禁止省略 `model`**（省略即 Auto，历史上会落到 Sonnet）。`reply` / 续跑同一 Cloud Agent 时同样显式带上上述参数。 |

`ao review trigger` 会启动独立 reviewer，也必须显式传获授权的 harness/model/effort，不能继承未经核实的默认配置。

## 视觉 / 指定实现者交接

用户指定某模型或某前端负责人做视觉返工时：

1. 停止旧写入者对同一页面的继续写入；交接单写清唯一树/分支、文件、契约、未提交状态。
2. 新任务书写明指定 harness/model，禁止静默换成「相近可用」模型。
3. 指定变更范围（如只改 owner 视觉/交互）；不改未授权的后端数据、权限或公众面，除非票面另写。

相关协调失败见 [`FAIL-COORDINATION.md`](FAIL-COORDINATION.md)。
