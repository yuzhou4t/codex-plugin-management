# AO 操作约定

在派发、恢复、评审、续接和收尾时按需读对应段。命令参数以当前机器的 `ao … --help` 为准，用户指定的模型和授权持续有效。

## 模型路由

助手和所有被派活的代理禁止使用 Claude 系列模型或 Claude API，包括 `claude-*`、`sonnet`、`opus`、`haiku`、`fable` 及会落到 Claude 的 Auto/default。用户本人可以在自己的 IDE 中选择，助手不得代选或建议此类模型。实现者与 reviewer 使用同一套路由规则。

| 用户选择 | 显式启动参数 |
| --- | --- |
| Astra | `--harness codex --model gpt-6-astra --effort high` |
| Codex，未另点名模型 | `--harness codex --model gpt-6.1-sol --effort xhigh` |
| Grok Build | `--harness grok --model grok-4.7-xhigh` |
| Cursor，经 AO 或 CLI | `--harness cursor --model grok-4.7-xhigh` |
| Cloud Agent / Background Composer | `model: grok-4.7`，`model_params: {"reasoning_effort":"xhigh"}` |

Cloud 的首次启动、reply 和续跑都显式带上模型与强度。`ao review trigger` 同样显式传获授权的 harness、model 和适用的 effort。

启动后核对实际模型和强度。模型不可用时报告受阻部分，向用户确认替代选择并继续独立工作。误落到 Claude 时立即停止错误会话，在原授权内改正启动参数并核对结果，不能继续沿用错误模型。

## 项目、任务书与权限

1. 从真实仓库路径查 AO 项目。缺少注册时按授权用 `ao project add`。从当前 AO 注册记录中核对项目 id 和目录。
2. 派发前核对是否已有同票会话或 PR。任务书根据当前项目配置和远程核对结果写明实际目标仓库。
3. `ao spawn` 显式提供项目 id、中文可读 `--name`、harness、model、适用的 effort 和 `--prompt`。提示引用工人可读的任务书路径，`--prompt` 接收字符串。按帮助构造命令，不假设存在 prompt-file 参数。
4. 核对实际工作目录、worktree、分支、模型及任务书可读性，建立工单、会话和 PR 的对应。沿用 AO 的工作树分配，文件责任写入任务书。
5. 在原会话返工时使用 `ao send` 指定会话。恢复使用 `ao session restore` 并核对实际目录、分支及模型；已结束会话的恢复不授权认领其他任务。

工人执行授权内常规动作无需逐步向用户索要批准。架构师派发前核实执行环境支持本票操作，区分审批策略与沙箱范围，现有会话权限需单独核对。

用户已授权权限配置时，`ao project set-config` 会替换项目配置，必须保留其他有效字段；配置对之后的 spawn 生效。`--permission bypass-permissions` 仅在已有相应授权时使用。Codex 的 workspace-write 本身不表示免审批；已有仓库信任和允许规则可沿用。权限拒绝时定位原因，准备所需新增权限和具体动作交回，继续可做部分，禁止通过换启动方式绕过明确拒绝。

实现票显式写入 commit、推本票工作分支、开或更新 PR 的许可，目标远程须明确。新会话的文件路径必须可读，不能假设本机忽略文件自动进入新 worktree。共享任务书提交到约定位置，或用已获准的方式传入工人目录。

## 已有 PR 与在途任务

`ao session claim-pr` 和 `spawn --claim-pr` 只关联已有 PR。挂接前核对工作分支、PR 最新提交及现有负责人；它们不会创建 PR 或检出 PR 分支。有支持时使用 `--no-takeover` 保护在途负责人。

工人仍在运行时先读其进度并协调原会话。接手请求不意味着停掉工人、再派同一任务或把旧报告写成当前验收。工作树和提交发生变化时，查清哪些检查仍有效、哪些需要补验。

## 评审与交付状态

AO 的列由 PR、CI 和 AO review 状态推导。开发中表示正在实施；验证中表示检查在进行；评审中表示等待复验和评审；就绪表示已达到可合并条件；交付结束后关闭会话并归档。实际上线由部署与入口验证确认。

实现票先交真实 PR，架构师自验后进行 AO review。先查看 `ao review ls <worker-session-id>` 及现有结果，再按当前帮助启动或提交评审。提交指定 worker session、run 和 verdict，输出与实际检查相符的结论。已有 approved 记录或 `REVIEW_INVALID` 时核对会话、run 与提交，避免盲目重复 submit。PR head 更新后重新判断评审覆盖范围。

要求托管平台 review 时，取得实际 GitHub/GitLab review 结果，再完成 AO 记录。AO approved、平台 approval、合并授权和部署授权分别核对。AO review 不可用且本票允许替代时，架构师自验并检查 PR 状态，在现有交付记录或 `.architect/` 中记下替代原因和实际结果。

`ao report` 汇报当前工人上下文的进度，调用前确认归属。工人可按任务书报告 checkpoint、阻塞和产物，禁止自行 `--done` 或宣称架构师验收完成。该命令没有任意指定 worker 的 `--session` 参数，以当前帮助为准。研究和无代码改动任务按报告或产物验收，完成后收尾。

## 完成通知与续接

任务书明确谁接收结果以及是否要求架构师持续监控。用户要求派发后结束时，在核对工人真实启动后交回会话和续接点。持续监控任务则跟进到约定完成条件，处理可恢复失败并复验。

用户要求完成后自动唤醒时，核对接收方属于 AO orchestrator、独立 Codex 对话还是其他宿主。采用该宿主实际提供的事件或续接工具，验证接收方存在、任务归属明确、结果可读。

- AO `report --checkpoint` 可交回工作进度和产物；是否触发目标会话继续执行需要核实。
- 当前 `ao send --steer` 支持向指定 AO Chat 会话发送指示，并在其空闲时启动下一轮。它的适用范围是目标 AO 会话。
- 独立 Codex 对话需要对应宿主的真实续接能力。只有观察到目标接收并继续执行，才说明自动唤醒已验证。
- 恢复时先核对该票最新状态和已有处理结果，已处理的完成事件不再次派活或重复评审。重试消息时，宿主支持稳定消息 id 则复用同一 id。

通知内容包含工单或会话、产物或 PR、提交、验证及未验项、下一步。将结果落到可读的交付记录后再结束工人，保护接收端和在途依赖。通道受阻时保留记录并明确下一次恢复入口。

## 会话收尾

本票约定的验收、评审和交付记录完成后，用 `ao session kill` 或当前等价方式结束工人及 reviewer。仅 `exit-agent` 不代表 AO 会话已终止。核对会话及相关进程退出，停止本票创建且已无用途的预览、隧道和 watcher。

派活或验收时发现已交付完、确认为空闲的旧会话或辅助进程，一并收尾。用户明确保留、正在跟票、已被重新认领或仍有依赖的会话继续保留。只读任务交回待收尾项。

按明确会话与进程归属停止。禁止按名称批量 kill、停止整个 AO daemon，或把 workspace cleanup、删除日志、数据库、备份混入会话收尾。保留用户正在用的服务及其他任务。历史靠 Git、PR、交付记录和已终止会话保存，需要时再恢复。报告关闭对象及仍保留对象的原因。

## 已授权的非 AO 路径

AO 不可用时先定位并恢复 daemon 或项目，独立工作继续。仅当用户明确授权本次非 AO 执行，采用以下已有方式，并由架构师验收及记录实际交付。

- Cursor CLI 使用文件任务书、显式 `--model grok-4.7-xhigh`，按已授权权限使用 `-p --force --trust`。提示指向文件，返工指定 chat id 和 `--resume`，多工单不共用 `--continue`。只读调查可用 `--mode=ask`。
- Codex CLI 使用 `exec --json` 及模型表对应的 model/effort，按任务选择 read-only 或 workspace-write，返工恢复明确会话。
- 用户本次明确选择 Matt `implement` / `implement-spec` 时采用该方式，执行前落实同样的模型与授权边界。
