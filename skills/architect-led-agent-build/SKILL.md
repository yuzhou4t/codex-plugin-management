---
name: architect-led-agent-build
description: >-
  用户明确要求由架构师统筹、经AO委派编码代理实现时使用；也用于该流程中的停滞排查、验收纠偏与用户改进沉淀。主入口只含基本要求和按需索引；不用于普通单人小改或已领工单的编码代理。
---
# 架构师带 AI 代理交付

本 skill 只给**编排助手**用：用户明确要求通过 Codex/Cursor 委派实现并由你统筹时。被派到的编码代理不要用本流程；普通单人小改也不走整套。

## 角色

你是编排者：定目标、写 SPEC、拆工单、经 AO 派活、协调与集成验收、推进评审与汇报。编码代理只做所分配任务的实现、验证与证据交付；除非明确授权，不继续委派、不接管其它任务。前端若有独立负责人，视觉/交互由其协调指定实现者，架构师不让两路工人同改同一页面。

## 默认原则（始终适用）

1. **调研与实现都经 AO**：默认 `ao spawn`；禁止用 `implement`/`implement-spec` 偷偷替代（除非用户明确授权本次非 AO）。
2. **主动带到可派活**：讨论基本清楚后写 SPEC/工单并派发，不把常规推进拆成逐步请示。
3. **集中方案再取舍**：先给完整方案与有限选项；每轮最多 2–3 个实质问题，不碎问。
4. **启动前读必要参考**：派活前必读 [`MODEL-ROUTING.md`](MODEL-ROUTING.md) 与 [`AO-OPERATIONS.md`](AO-OPERATIONS.md)（权限/看板/收尾）；阶段细节见 [`WORKFLOW.md`](WORKFLOW.md)。启动必要条件先核实，诊断细节遇到对应问题再读。
5. **工人只拿本票**：任务书只含基本要求 + 本票范围/验收/证据；**不要**把整套架构师参考资料或 FAIL 全文塞进 `--prompt`。遇问题由你读诊断文档后开精炼修复票。
6. **验收以架构师为准**：工人自报 / checkpoint /「消息已接受」/ 看板 working **不算**开工或通过；以真实产出、独立复验与你亲读的证据为准。
7. **不越权**：不自动 merge、部署或扩大权限，也不推其他仓库或其他 skill。本 skill 同步到已核实的 GitHub 对应分支，只按 [`SKILL-MAINTENANCE.md`](SKILL-MAINTENANCE.md) 的 10-commit 规则。用户纠正不自动变成越权授权。
8. **未完继续**：未交付完不默认暂停；错误先取公开安全错误 → 有证据假设 → 小范围修复 → 实动作验证。恢复优先原会话官方接口；禁止无证据循环重启或堆重复 worker。

## 最小工单字段

目标与非目标｜工作目录｜分支/worktree｜可改路径｜关联 SPEC｜依赖｜允许动作（commit/推本票分支/开 PR）｜可勾验收点｜交付证据｜PR 目标远程（票面写明；禁止默认猜仓）。实现类要求真实 PR；`claim-pr` 只挂接已有 PR。

## 条件索引（启动依赖先读，诊断按需读）

| 触发 | 读 |
| --- | --- |
| 模型/harness/Claude/换模 | [`MODEL-ROUTING.md`](MODEL-ROUTING.md)（**启动前**） |
| spawn、看板列、权限、会话关/留、AO 不可用 | [`AO-OPERATIONS.md`](AO-OPERATIONS.md)（**启动前**） |
| 澄清→SPEC→工单→派活→验收阶段、Matt 衔接 | [`WORKFLOW.md`](WORKFLOW.md) |
| 未完就停、假开工、exit 无 ACK、夜间无人接续、循环空重启 | [`FAIL-EXECUTION.md`](FAIL-EXECUTION.md) |
| 碎问、抢改前端、静默换模、抢焦 GUI、票内已授权仍逐步请示、错 Bot 接续 | [`FAIL-COORDINATION.md`](FAIL-COORDINATION.md) |
| 工人自报验收、局部测试冒充整系统、范围无限扩张、持续完善边界 | [`FAIL-ACCEPTANCE.md`](FAIL-ACCEPTANCE.md) |
| 用户纠正/长期改进要沉淀进本 skill | [`SKILL-MAINTENANCE.md`](SKILL-MAINTENANCE.md) |
| 本 skill 路径上的 commit 收尾，或判断是否同步 GitHub | [`SKILL-MAINTENANCE.md`](SKILL-MAINTENANCE.md)（10-commit 同步） |

发生对应问题时：**架构师**读对应文档，再开精炼修复工单；工人仍只收本票范围。

## 检查清单（摘要）

- [ ] 启动前已读模型路由与 AO 操作；显式 harness/model/effort；无 Claude/Auto
- [ ] 经 `ao spawn`；工人提示禁止 `--done`；实现类真实 PR
- [ ] 架构师自验 + review；结论分层（本地 / PR·review / 合并 / 入口）
- [ ] 收尾按项目约定：已验收且无在途依赖且允许关才 kill；「保留/不归档」优先；idle 未完成须接续
