# 阶段工作流与 Matt 衔接

## 与 Matt Pocock Skill 的衔接

统一情境表见同库 `ask-matt` 的 `AO-SITUATION-TABLE.md`（ask-matt 技能目录内）。本 skill 只保留阶段执行规则与 AO 硬边界，不另维护第二份总表。硬规则（假触发 / 双轨 / 工人抢活）以该表文末三条为准。

### 加载约定

1. 先确认当前 harness 能按名用 Skill 工具加载该 skill；加载失败就明说「未加载」，不要把「提到了名字 / 读了文件」当成已触发。
2. 每一阶段只加载**一个主流程**入口，并写明输入与预期产物。
3. 已有统筹授权且阶段明确时直接继续，不必每步再请用户敲一遍 slash。
4. 上游插件里部分 skill 带 `disable-model-invocation`（只能人敲）；那是另一套 harness。本助手目录下可用 Skill 工具加载的，按本表显式加载即可。
5. 回合结束前若检查清单勾了 grill/to-spec/to-tickets，须能指出本回合 Skill 工具成功返回；否则勾「跳过」并写原因，禁止空勾。

### 按动作分类

| 类别 | Skill | 用法 |
| --- | --- | --- |
| 规划（阶段点名） | `grill-with-docs` / `grill-me`、`to-spec`、`to-tickets`、`triage`、`wayfinder` | 架构师在对应阶段加载；小改与决定已清则跳过 |
| 派活（本 skill） | 任务书 + `ao spawn` | **唯一默认派活路径** |
| 窄情境方法 | `tdd`、`diagnosing-bugs`、`pr`、`git-finish`、`domain-modeling`、`codebase-design` | description 可自动挂；任务书可点名 |
| 会开子代理 / 重动作 | `research`、`code-review`、`prototype`、`wizard` | **不要**当静默自动纪律；AO 模式下经架构师决定是否 spawn 适配，或跳过其内嵌子代理路径 |
| 环境 / 会话 | `setup-matt-pocock-skills`、`retro`、`handoff` | setup：先读已有 docs/agents，缺再配；handoff 仅跨目录/harness/同事；retro 非上线门禁 |
| 迷路 | `ask-matt` | 只选路；选完仍按本 skill / 情境表执行 |

### 阶段完成条件

| 阶段 | 完成条件 | 主加载 |
| --- | --- | --- |
| 澄清 | 目标、验收、非目标清楚；必要时词表/ADR 已落盘（仅当允许沉淀） | `grill-with-docs` 或 `grill-me` |
| SPEC | 一份权威 SPEC；跨多会话时已合成 | `to-spec`（可跳过：单窗可完成则直接任务书） |
| 工单 | 可检查票 + 阻塞边；再补目录/权限/模型/验收命令 | `to-tickets` → 任务书 |
| 派活 | `ao spawn` 会话与任务书对齐 | 本 skill + [`AO-OPERATIONS.md`](AO-OPERATIONS.md) |
| 验收 | 架构师自验 + `ao review`；工人自报不算；本地通过 ≠ 整票闭环 | 可选受控 `code-review`；细则 [`FAIL-ACCEPTANCE.md`](FAIL-ACCEPTANCE.md) |
| 大雾 | 决策地图清晰后再进 SPEC；限探索范围/时间 | `wayfinder` → `to-spec` |
| 收尾 | 按 [`AO-OPERATIONS.md`](AO-OPERATIONS.md) 条件化关会话 | 本 skill |

Issue/`ready-for-agent` 只表示规格就绪，**执行会话状态以 AO 为准**。加载 Matt skill 不增加 merge、部署或权限。

## 整体顺序

1. **先定目标与验收，再写 SPEC。** 一句话写清目标、适用的截止日期、受众。有正式外部标准就引用原文；没有就依据用户目标与项目约定定义可检查验收条件，不虚构标准，也不把「缺外部标准」当成全局停工——只标出因此受影响的决策，继续做独立部分。有演示需要时，写 3–5 个画面及每个画面要显示的数字，并分清「截止前必做 / 以后」。思路未清时先加载 grill。
2. **只留一份权威 SPEC。** 推翻决定时当场改受影响段落或写「取代 §X」；通知相关执行者，并判断进行中的工单要不要改。每轮最多 2–3 个问题。跨多会话用 `to-spec` 再 `to-tickets`；单窗可完成则直接任务书。新明确指令覆盖冲突的旧约定；一次任务例外不自动变成长期默认。专项 SPEC/ADR 可分文件，但须注明覆盖范围与替代旧段落。
3. **规格 / 待派。** SPEC 定稿后、正式 spawn 前写成任务书；「规格/待派」是逻辑阶段，不是 AO 新增列。
4. **尽早验证关键真实依赖。** 凭据、配额、数据或外部环境不可用时，写清：哪些已用替代验证、哪些真实集成待验、哪些确实受阻；继续完成独立部分。不要把「假实现通过」说成交付完成。
5. **经 AO 派活。** 见 [`AO-OPERATIONS.md`](AO-OPERATIONS.md) 与主入口最小工单字段。任务书可提醒工人按需使用 `tdd` / `code-review` / `pr` / `git-finish`。
6. **架构师负责验收。** 亲读关键产物、diff 与原始证据；具体测试/构建/Git 按项目分工交独立工人执行，架构师作最终判断。详见 [`FAIL-ACCEPTANCE.md`](FAIL-ACCEPTANCE.md)。
7. **合并纪律。** 改前看清 Git 与已有修改。并行写入用独立 worktree 并明确文件责任。合并前确认基线与回滚；是否打 tag 按风险与项目约定。用户自己的改动只合并不覆盖。**不自动 merge/推送基线/部署**，除非用户已明确授权该动作。可用 `git-finish`、`stabilize-local-agent-project`。
8. **收尾。** 按 [`AO-OPERATIONS.md`](AO-OPERATIONS.md) 条件化关会话。

## 任务书与密钥

任务书至少含主入口所列字段。示例约束要标成示例。

内部笔记放已 gitignore 的目录（如 `.architect/`）或私有仓；**`.gitignore` 不会移除已跟踪文件**。密钥走环境变量/本机 secret，不进仓库、不进聊天、不进工具输出/命令回显/日志/截图/PR/验收报告；核对配置只记「已设置/未设置」、来源和非敏感模型名。

浏览器：编码代理用自己的浏览器工具验页面；编排助手操作 AO/本机 GUI 时再处理系统自动化权限。

## 若你是被派到的编码代理

停用架构师流程。不要再拆工单、不要再派活、不要开新对话。

只做工单里的事：在写明的仓库、分支和路径里实现；按验收标准自测；回复分支名、改动文件、跑过的命令和退出码、没验证的部分。

- **不要** merge、部署、扩大权限。
- **不要**自行 `ao report --done`，不得自行宣布架构师验收完成。可按任务书汇报进度、阻塞和 checkpoint；**checkpoint 不代表验收通过或可合并**。
- 工单没写「提交」就不要 commit；实现票须写明是否允许本地 commit，以及为开 PR 推送本票工作分支是否允许（默认：允许推本票分支并开/更新 PR，禁止 merge 到基线分支）。
- 实现票须以真实 PR 交付；`claim-pr` / `spawn --claim-pr` 只挂接已有 PR，**不能创建 PR**，也不检出 PR 分支。
- 缺了会改变行为的决定时，写一条阻塞，不要猜。
- **不要**改用或请求 Claude；模型以任务书 / 派活参数为准。
- 单窗内用 `tdd` 等窄方法不等于获得再次委派权限；架构师要核实对应 setup 是否已完成，缺则按授权补齐或记录知情跳过。

架构师写入工人 `--prompt` 时，只摘本节约束与本票字段，**不要**附带 FAIL-* / 维护全文。
