---
name: paper-terminology-translation-explanation
description: 中文论文精读中的术语翻译与解释规范。用于讲解论文术语、比较论文版本或架构、统一中英文译名时；尤其适用于 AI Scientist v1/v2 精读。要求首次出现给出英文原词、统一中文译名和语境功能，并严格区分论文原词、解释性概括、我们的设计与领域扩展。
---

# Paper Terminology Translation & Explanation Skill

## Purpose

Use this skill when the user asks to explain, translate, compare, or closely read terminology in an academic paper.

Default language: Simplified Chinese.

Core rule:

> Do not present a translation without explaining its function in the paper, and do not present an interpretation or proposed design as if it were the paper's own terminology.

## First-Occurrence Format

The first time an important term appears, use:

```text
English term（统一中文译名）：结合本文语境说明它实际负责什么、作用边界是什么。
```

Example:

```text
Experiment Progress Manager（实验进度管理器）：
负责实验阶段推进、停止条件、节点选择、检查点和重复实验；它是实验流程管理模块，不等同于完整的科学研究管理器。
```

After the first explanation, use the confirmed Chinese name. Retain the English term when the Chinese translation may be ambiguous.

## Mandatory Source Categories

Every architectural concept or substantive interpretation must belong to one of these categories:

1. **论文原始术语**: a name or module explicitly used by the authors.
2. **解释性概括**: wording introduced only to make the paper easier to understand.
3. **我们的架构设计**: a design proposed during discussion, not implemented by the paper.
4. **领域扩展**: a domain-specific addition, such as a green-finance constraint.

Recommended presentation:

```text
Agentic Tree Search（智能体树搜索）【论文原始术语】
实验状态搜索【解释性概括】
Hypothesis Tree–Experiment Tree（假设树—实验树）【我们的架构设计】
Causal Identification Gate（因果识别门控）【绿色金融扩展】
```

Never write “the paper uses/proposes...” for a concept that belongs to categories 2–4.

## Translation Method

Translate according to the term's function in the full paper, not by mechanical word substitution.

For a new or ambiguous term, present:

```text
原词：
候选译名 A：
候选译名 B：
本文语境中的功能：
建议译名及理由：
```

If multiple translations remain reasonable, ask the user to choose before adding one to the stable terminology table. Do not silently fix a disputed translation.

## Stable AI Scientist Terminology

| English term | Unified Chinese name | Boundary |
|---|---|---|
| The AI Scientist-v1 | AI Scientist-v1 / 第一代 AI Scientist | Lu 等 2024 系统 |
| The AI Scientist-v2 | AI Scientist-v2 / 第二代 AI Scientist | Yamada 等 2025 系统 |
| Agentic Tree Search | 智能体树搜索 | 论文的实验节点搜索方法；不是完整假设推理树 |
| Experiment Progress Manager | 实验进度管理器 | 管理实验阶段与节点；不是科学研究总管理器 |
| Preliminary Investigation | 初步调查 / 初步可行性验证 | 建立最小可运行原型 |
| Hyperparameter Tuning | 超参数调优 | 不泛化为所有研究规格选择 |
| Research Agenda Execution | 研究议程执行 | 执行核心实验方案 |
| Ablation Studies | 消融研究 | 检查组件或假设的重要性；不等于因果机制证明 |
| Experiment Node | 实验节点 | 保存代码、计划、日志、指标、图表和反馈等实验状态 |
| Debug Node | 调试节点 | 修复运行错误 |
| Refinement Node | 改进节点 | 改进可运行实验 |
| Replication Node | 复现节点 / 重复实验节点 | 论文主要指用不同随机种子重复父实验；不等于完整独立复现 |
| Aggregation Node | 聚合节点 | 汇总已有重复实验并生成统计与图表；不运行新实验 |
| Best-first Search | 最佳优先搜索 | 由 LLM 依据指标、训练动态和图表等选择节点 |
| best-performing node | 表现最佳节点 | 不自动等同于科学价值最高节点 |
| buggy node | 有运行错误的节点 | 不等同于科学上无效 |
| non-buggy node | 无运行错误的节点 | 不等同于科学上有效 |
| Automated Reviewer | 自动审稿器 | 主要评价最终论文 |
| Node Evaluator | 节点评价器 | 在研究过程中评价实验节点 |
| Hypothesis Tree | 假设树 | 我们提出的上层设计；不是 v2 原始模块 |
| Experiment Tree | 实验树 | 对 v2 实验搜索结构的概括，或我们的下层设计 |
| Evidence Verifier | 证据验证器 | 我们原有架构模块；不是 v2 原始模块 |

## Version-Comparison Explanation Order

When comparing a new paper or system version with an earlier one, explain in this order:

1. English term and unified Chinese translation;
2. what the earlier version did;
3. what the new version changed;
4. which earlier limitation it addresses;
5. what limitation remains;
6. candidate implications for our architecture;
7. candidate domain mapping, if relevant;
8. wait for user discussion and correction.

For AI Scientist-v2, compare with v1 whenever the comparison is material.

## Evidence and Interpretation

- Use paper evidence for claims about methods, data, experiments, and limitations.
- Keep quotations short and purposeful.
- State explicitly when a conclusion is an interpretation rather than an author claim.
- Do not equate execution success with scientific validity.
- Do not equate model performance with scientific value.
- Do not expand a term beyond the role documented in the paper.

## Output Check

Before answering, verify:

- important terms were explained at first occurrence;
- the Chinese translation is stable or explicitly pending confirmation;
- paper facts and our proposals are visibly separated;
- version comparison is included when required;
- no domain extension is described as a paper contribution.
