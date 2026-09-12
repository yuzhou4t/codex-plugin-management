---
name: codex-subagent-team
description: Configure, synchronize, and operate an Astra-led native Codex subagent team using Sol, Terra, and Luna. Use when the user asks to install these model-specific agents, copy them to another computer, route a confirmed plan to an executor, or run independent acceptance; do not introduce multi-agent orchestration into ordinary tasks unless the user requests it.
---

# Codex Subagent Team

Keep the main conversation responsible for the user's intent, plan, authorization, and final synthesis. Use the bundled profiles only when the user names a role or explicitly asks for the model team. Do not set a global primary model, default subagent model, or reasoning effort in `config.toml`.

## Install or synchronize the profiles

The source of truth is `assets/agents/`:

- `sol_executor`: `gpt-5.6-sol`, high reasoning, workspace write.
- `terra_executor`: `gpt-5.6-terra`, medium reasoning, workspace write.
- `terra_reviewer`: `gpt-5.6-terra`, high reasoning, read only.
- `luna_patcher`: `gpt-5.6-luna`, medium reasoning, workspace write.

When the user asks to install or update this team, run the matching bundled installer:

```bash
./scripts/install-agents.sh
```

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-agents.ps1
```

Both scripts use `CODEX_HOME` when set and otherwise install only these four files under the current user's `.codex/agents/` directory. They preserve every unrelated agent and do not edit `config.toml`, credentials, projects, or model-picker settings. An explicit install request authorizes replacing these four managed profile names with the bundled versions; it does not authorize changing any other agent.

Validate the installed filenames and compare them with the assets. If the installed Codex version does not support multi-agent operation or one of the selected model IDs, report the exact version error instead of silently substituting a model. Profiles are user-global and apply across projects. Prefer a new or reloaded conversation after installation when an already-open conversation does not recognize a newly added role.

## Route a confirmed plan

Do not spawn during exploratory discussion. Once the user says the plan is confirmed or directly asks to execute it, turn the plan into a bounded task contract with the goal, task-owned paths, protected state, expected deliverables, relevant checks, exact acceptance boundary, and any remaining human gate. Do not request confirmation again when the user's instruction already authorizes execution.

Choose one writing executor by uncertainty:

- Use `terra_executor` for clear, routine implementation, data processing, test repair, or repository work with known behavior.
- Use `sol_executor` for ambiguous or cross-layer implementation, deep root-cause work, protocols, complex document reconstruction, or work that needs substantial judgment and polish.
- Use `luna_patcher` only after the defect's cause, location, required change, impact boundary, and deterministic pass condition are all known. A small diff with an unknown cause belongs to Terra or Sol.

Let the selected executor complete the bounded read, implement, test, and repair loop before one concentrated review. Do not create planner-executor-reviewer microloops. In a shared worktree, run only one writing agent at a time. Parallelize only independent read-heavy work or isolated outputs.

## Review and repair

After implementation, start a fresh `terra_reviewer` with the original contract and requested acceptance boundary. The reviewer must inspect actual artifacts and evidence rather than relying on the executor's summary. For unusually complex architecture, protocol semantics, research evidence, or document fidelity, the main agent may instead request a fresh read-only Sol review.

Route review findings by remaining uncertainty:

- A localized, fully diagnosed mechanical defect can go to `luna_patcher`.
- An ordinary behavioral defect returns to `terra_executor`.
- An unresolved semantic, architectural, or cross-system defect returns to `sol_executor` or to the main agent for replanning.

Always re-run the relevant review after Luna changes a file. Luna is never the final acceptance step.

The subagent permission ceiling comes from the parent conversation. Select workspace-write permission before invoking a writing executor; a read-only parent correctly keeps every child read-only. Keep the reviewer profile read-only.

Finish by distinguishing implementation checks from acceptance at the requested real boundary. A development server, alternate URL, sender exit code, source document, or file existence does not prove the requested Safari page, installed application, receiving Windows device, or rendered document passed.

## Direct invocation

Use exact role names when reliability matters:

- `计划已确认，调用 sol_executor 完整实施。`
- `计划已确认，调用 terra_executor 完整实施。`
- `调用 terra_reviewer 对照原始要求独立验收。`
- `问题已经定位，调用 luna_patcher 按确定方案修复，随后让 terra_reviewer 复验。`
