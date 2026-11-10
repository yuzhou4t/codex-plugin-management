# AO 操作：派活、看板、权限、会话收尾

**启动前必读**。项目名与 id 以当前仓库已注册的 AO 项目为准；**不要**把某一历史项目 id 写成全局默认。

## 派活硬边界

- 默认必须经 **`ao spawn`**。项目须已注册（`ao project add --path … --name …`）。
- AO 不可用时：先定位并恢复 daemon/项目；恢复不了就标明「派活/可见性受阻」，继续独立工作。**仅当用户明确授权本次采用非 AO 路径**才用 CLI 兜底；不得未授权绕开。
- 每次 spawn 显式：项目、`--name`（**中文可读标题**，可保留工单号前缀）、harness、model（及适用 effort）、`--prompt`。
- `--prompt` 引用工人可读的任务书路径；只含本票基本要求与验收，**不**整包粘贴架构师参考库。
- spawn 后核对：AO 项目、会话 ID、实际目录、分支/worktree、harness/model/effort；建立工单—会话—PR 对应。错配先纠正。
- Cloud Agent 启动后核对返回的 model；若不是授权模型则立刻停并用正确参数重开（或问用户）。

### 权限

- 常规票内动作由架构师按已有授权配置与接续，避免重复向用户请示。平台强制人工确认仍交用户，不由架构师代批或绕过。「不弹日常审批」不等于授予 bypass-permissions 或扩大 merge/deploy 权。
- 已有授权直接沿用；新增权限只处理新增范围。不得通过更换启动方式绕过明确拒绝。
- 项目配置改动（如 `ao project set-config … --permission …`）会替换项目配置——改前保留其余字段；配置在**之后**的 spawn 生效，既有会话另行核实。
- spawn 提示写明：工人不要跑 `ao report --done`；checkpoint 仅进度，不代表验收。

### CLI 兜底（仅用户明确授权本次非 AO）

事先说明原因。仍禁止 merge/部署；仍由架构师验收；进度仍尽量记到 AO。若授权用 `implement` / `implement-spec` 代替 AO，须在当次说明。仍禁止 Claude；模型参数见 [`MODEL-ROUTING.md`](MODEL-ROUTING.md)。

- Cursor：任务书放文件，提示词指向路径，不要把整份任务书从 stdin 灌进 `-p`；显式 `--model`；返工用 chat id `--resume`；多工单不要用 `--continue`。
- Codex：`exec --json`；按路由表传 model/effort；调查 read-only，改代码 workspace-write；返工 resume 明确会话 ID。

## 看板与列

AO 列固定，**不能手拖当第二套账本**；实现票的列由 PR、CI 与 AO review 状态推导：

| 列 | 约定含义 |
| --- | --- |
| 开发中 | 工人在做；尚无合格 PR 时常停于此 |
| 验证中 | 已有 PR，检查进行中 |
| 评审中 | 待架构师复验与 AO 评审 |
| 就绪 | 验收勾完、可合并（≠ 已上线）；列可留，进程是否关见下文 |
| 归档 | 会话已终止；仅当项目允许且交付已闭环 |

`ao report` 是向 orchestrator **汇报进度**的接口，**不是**手动设列。可用 `ao send --session <id>` 向工人会话发指示。

**实现类**：`ao spawn` → 工人开真实 PR → 架构师自验 → `ao review`（`trigger` 再 `submit … approved`）。**AO approval ≠ 托管平台 approval，也不授予 merge/push 基线/deploy。** 在已有明确授权内合并并验证上线；缺授权只就新增动作问用户。

**调研/探测类（无 PR）**：按实际交付物验收；不为追看板列强开空 PR。若转为实现，改交付要求并开 PR。

配置示例：仅获授权时使用 `ao project set-config … --permission bypass-permissions`，保留其余配置字段；Cursor/Codex 的权限、信任与沙箱分别核实，不把 workspace-write 当作免审批。

常用命令以本机 `ao … --help` 为准：`spawn`、`session ls|get|kill|restore|claim-pr|top|cleanup`、`send`、`report`、`review trigger|submit|ls`、`project add|set-config`、`pr merge`（仅已授权时）。

## 会话收尾（条件化）

按当前项目授权和交付事实决定收尾；最新明确的保留要求优先：

1. **可关**：架构师完成本票约定验收、必要的 PR/AO review 与交付记录，**且**无在途依赖，**且**项目/用户未要求保留该会话——立刻 `ao session kill`（或本机等价结束），停本票创建且不再需要的辅助进程。只做 `exit-agent` ≠ 已终止。汇报「关闭了什么、仍保留什么及原因」。
2. **必须留/须接续**：用户或项目明确「保留 / 不要归档 / 未完成继续」时，**保留要求优先**。看板 idle 但票未完成 → **接续**，不是收尾。
3. **历史怎么留**：靠 Git PR、`.architect/` 验收笔记、已终止会话记录；需要时 `ao session restore`。不要为保留看板外观而维持空闲 agent；也不要在未完成时为「清内存」杀掉唯一执行会话。
4. **保护范围**：不要按进程名批量 kill；不要把停止整个 AO daemon 当本票收尾；工作区 `cleanup`、删日志/数据库/备份不属于本规则。保护用户仍在使用的服务、其他任务及生产常驻进程。
5. **顺手清旧债**：仅对**已验收交付且无在途依赖**、且项目允许收尾的空闲旧会话/辅助进程一并关掉。
6. **只读/禁 kill 票**：仅交回报告和待收尾事项，由有权限的架构师完成关闭。

**不要**在本 skill 写入「全局每 N 分钟巡检」或「永不收尾」硬规则；监督频率写在**项目约定 / 例程**，不写进全局模板。

停滞与假开工处置见 [`FAIL-EXECUTION.md`](FAIL-EXECUTION.md)。
