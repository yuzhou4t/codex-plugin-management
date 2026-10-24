---
name: architect-led-agent-build
description: >-
  架构师带编码代理交付：定目标与一份 SPEC、拆工单、经 Agent Orchestrator（AO）派活并自验合并。
  仅当用户要你当架构师、且有比赛/答辩/演示/上线截止日期时用。已收到写好工单的编码代理不要用本
  skill。不用于普通单人小改。
---
# 架构师带 AI 代理交付

本 skill 只给**编排助手**用：用户明确要求通过 Codex 或 Cursor 委派实现、并由你统筹交付时。不因单独出现 SPEC、acceptance、architect 等词就启动整套流程。

你是编排者：定目标、写 SPEC、拆工单、准备执行环境、经 AO 派活、协调与集成验收、推进评审与汇报上线。被派活的编码代理是执行者：只做所分配任务的理解、实现、验证和交付；除非明确授权，不继续委派、不接管其它任务。

**进度以 Agent Orchestrator（AO / Orchestrator.inc）看板为准**（项目「新工作坊」、项目 id `project`，经 `ao spawn`）。

可配合 Matt Pocock 的 to-spec / to-tickets 写 SPEC 与拆票；那些是通用工程流程，本 skill 管整条交付顺序、AO 派活与验收。

## 你若是被派到的编码代理

停用本 skill 的架构师流程。不要再拆工单、不要再派活、不要开新对话。

只做工单里的事：在写明的仓库、分支和路径里实现；按验收标准自测；回复分支名、改动文件、跑过的命令和退出码、没验证的部分。

- **不要** merge、部署、扩大权限。
- **不要**自行 `ao report --done` / `--checkpoint` 等；架构师验收后再报。
- 工单没写「提交」就不要 commit；实现票任务书须写明是否允许本地 commit，以及为开 PR 推送**本票工作分支**是否允许（默认：允许推本票分支并开/更新 PR，禁止 merge 到基线分支）。
- 实现票须以真实 PR 交付；`ao session claim-pr` / `spawn --claim-pr` 只挂接已有 PR，**不能创建 PR**，也不检出 PR 分支。
- 缺了会改变行为的决定时，写一条阻塞，不要猜。

## 什么时候用

- 用户明确要你当架构师，并有截止日期与受众（评委、客户、上线），或明确说「让 Codex/Cursor 做、你统筹」。
- 实现主要交给编码代理。
- 不用于普通单人小改，也不用于「只评审 SPEC」这类只读请求。

## 整体顺序

1. **先定目标与验收，再写 SPEC。** 一句话写清目标、适用的截止日期、受众。有正式外部标准就引用原文；没有就依据用户目标与项目约定定义可检查验收条件，不虚构标准，也不把「缺外部标准」当成全局停工——只标出因此受影响的决策，继续做独立部分。有演示需要时，写 3–5 个画面及每个画面要显示的数字，并分清「截止前必做 / 以后」。
2. **只留一份权威 SPEC。** 推翻决定时当场改受影响段落或写「取代 §X」；通知相关执行者，并判断进行中的工单要不要改。每轮最多 2–3 个问题。若已安装 to-spec / to-tickets，用它们；工单必须可检查。
3. **规格 / 待派。** SPEC 定稿后、正式 `ao spawn` 前：把工单写成任务书文件；每张卡写清验收点（可勾选检查项）。「规格/待派」是逻辑阶段，**不是** AO 新增列；未派发前不要假装已在「开发中」。
4. **尽早验证关键真实依赖。** 凭据、配额、数据或外部环境不可用时，写清：哪些已用替代验证、哪些真实集成待验、哪些确实受阻；继续完成独立部分。不要把「假实现通过」说成交付完成。
5. **经 AO 派活（见下一节）。** 每张工单至少含：目标与非目标、工作目录、分支或 worktree、负责文件、关联 SPEC 段落、依赖、允许的动作（含 commit/推本票分支/开 PR）、验收点、交付物。实现类须要求开真实 PR。
6. **自己验收，代理自报不算数。** 重跑测试、走主流程、读 diff；报告逐项写条件、结果、证据、未完成原因。验收通过后再由架构师做评审/报告，不要让工人抢先 `--done`。
7. **合并纪律。** 改前看清 Git 与已有修改。并行写入用独立 worktree（AO spawn 默认即 worktree）并明确文件责任。合并前确认基线与回滚方式；是否打 tag 按风险与项目约定。用户自己的改动只合并不覆盖。**不自动 merge/推送基线/部署**，除非用户已明确授权该动作。可用 git-finish、stabilize-local-agent-project。

## AO 看板与列推进

AO 列固定，**不能手拖当第二套账本**；实现票的列由 PR、CI 与 AO review 状态推导：

| 列 | 约定含义 |
| --- | --- |
| 开发中 | 工人在做；尚无合格 PR 时常停于此 |
| 验证中 | 已有 PR，检查进行中 |
| 评审中 | 待架构师复验与 AO 评审 |
| 就绪 | 验收勾完、可合并（≠ 已上线） |
| 归档 | 会话已终止；调研/探测验收后归档 |

**实现类工单**（以持久仓库改动交付；不限于「上线功能」字样）：

1. `ao spawn`；任务书要求工人开真实 PR（仅当 PR 已存在时用 `claim-pr` / `spawn --claim-pr` 挂接——**不创建 PR、不检出分支**，挂接前核对工作分支与 PR head）。
2. 架构师自验后走 `ao review`：`trigger`，再 `submit --session <工人会话> --verdict approved`（另需 `--run` 等，以 `ao review submit --help` 为准）。**AO approval 不等于 GitHub/GitLab approval，也不授予 merge / push 基线 / deploy 权限。** 就绪 = 验收勾完且可合并。
3. 在**已有明确授权**内合并并验证实际上线；缺授权时只就新增动作问用户。架构师向用户汇报「已上线」。
4. **上线后卡留在「就绪」；不要 `ao session kill` 收尾**，以便历史可见。列行为是项目约定，不是 CLI 帮助里保证的渲染承诺。

**调研 / 探测类（无 PR）**：验收后架构师 `ao session kill` → 归档；需要时 `ao session restore`。若任务转为实现，改交付要求并开 PR，不要假装无 PR 的卡进「就绪」。

`ao report` 是向 orchestrator **汇报进度**的接口，**不是**手动设列。工人禁止自行 `--done`。架构师验收后优先用 `ao review` 推进实现票；若需 `ao report`，须用已确认能归属到该工人会话的方式（该命令帮助无 `--session`，不要虚构参数），并核对归属。可用 `ao send --session <id>` 向工人会话发指示。

常用命令（以本机 `ao … --help` 为准）：`ao spawn`、`ao session ls|get|kill|restore|claim-pr`、`ao send`、`ao report`、`ao review trigger|submit|ls`、`ao project add|set-config`、`ao pr merge`（仅已授权时）。

## 派活：经 AO，权限由架构师控

默认必须经 **`ao spawn`**。项目须已注册（`ao project add --path … --name …`）。新工作坊：`--project project`。

AO 不可用时：先定位并恢复 daemon/项目；恢复不了就标明「派活/可见性受阻」，继续独立工作。**仅当用户明确授权本次采用非 AO 路径**才用 CLI 兜底。

1. **写明模型；禁止擅自换模。**
   - Codex：`--harness codex --model gpt-6.1-sol --effort xhigh`
   - Cursor：`--harness cursor --model grok-4.7-xhigh`
   - 列表无该 id 时停下来问，不要换近似模型。
2. **每次 spawn 显式**：`--project project`、`--name`、harness、model（及 Codex 的 effort）、`--prompt`。
3. **权限：工人不得向用户弹审批。** 架构师控制批准与看板。
   - 项目：`ao project set-config … --permission bypass-permissions`（帮助写明会替换项目配置——改前保留其余字段；配置在**之后**的 spawn 生效，既有会话另行核实）。
   - Cursor CLI 兜底：`-p --force --trust`；IDE allowlist / fullAutoRun 已配则沿用。
   - Codex：信任项目仓与 AO worktrees；审批策略与沙箱分开核对，workspace-write ≠「不弹审批」。
   - **spawn 提示写明：工人不要跑 `ao report --done`（及同类）**。
4. **任务书**：用 `--prompt "读取并执行 <工人可读路径>；…"` 引用文件（`--prompt` 只有字符串，无 prompt-file）；派发前确认文件在工人 worktree/可读位置。提示含验收点、禁止 merge/部署、禁止工人 report done、本票 commit/推分支约定。
5. **spawn 后核对**：AO 项目、会话 ID、实际目录、分支/worktree、harness/model/effort；建立工单—会话—PR 对应。错配先纠正。实现票长任务写明谁监控、如何看状态、如何停止；**上线后不得用 kill 收尾**。

### Cursor / Codex CLI 兜底（仅用户明确授权本次非 AO）

事先说明原因。仍禁止 merge/部署；仍由架构师验收；进度仍尽量记到 AO（能补挂则补挂）。

- Cursor：任务书放文件，提示词指向路径，**不要**把整份任务书从 stdin 灌进 `-p`；`-p --force --trust --model grok-4.7-xhigh`；返工用 chat id `--resume`；多工单不要用 `--continue`；调查可用 `--mode=ask`。
- Codex：`exec --json`；`-m gpt-6.1-sol` + `model_reasoning_effort=xhigh`；调查 read-only，改代码 workspace-write；返工 resume 明确会话 ID。

## 任务书与权限

任务书至少含：目标、仓库绝对路径、基线分支、工作分支/worktree、可改路径、硬规则、**验收点（逐条可勾）**、验收命令、commit/推本票分支/开 PR 约定、完成时交回的证据。示例约束要标成示例。

内部笔记放已 gitignore 的目录（如 `.architect/`）或私有仓；**`.gitignore` 不会移除已跟踪文件**。密钥走环境变量/本机 secret，不进仓库、不进聊天。

沿用已有授权。新增的 merge、推基线、部署、对外发送或权限扩大，在结果可审阅后只确认新增部分。不得通过更换启动方式绕过明确拒绝。

浏览器：编码代理用自己的浏览器工具验页面；编排助手操作 AO/本机 GUI 时再处理系统自动化权限。

## 检查清单

- [ ] 目标、验收条件清楚；外部标准有则引用，无则未虚构
- [ ] 只有一份 SPEC；工单含目录/分支/文件责任/验收点/交付物；有「规格/待派」再 spawn
- [ ] 真实依赖状态写清；独立部分未无故停工
- [ ] 经 `ao spawn` 派活；spawn 后已核对会话/目录/模型
- [ ] 模型固定：Codex `gpt-6.1-sol` xhigh；Cursor `grok-4.7-xhigh`；spawn 显式传参；未擅自换模
- [ ] bypass-permissions（或等价）已就绪且对新会话生效；工人提示禁止 `ao report --done`；无人被弹审批
- [ ] 实现类已开真实 PR（claim-pr 仅挂接）；架构师自验 + `ao review submit … approved`；已说明 AO approval ≠ 托管平台 approval ≠ merge 权
- [ ] 上线后卡留在就绪（不 kill）；调研/探测无 PR：kill → 归档（可 restore）
- [ ] 未擅自 merge/推基线/部署；回滚清楚
