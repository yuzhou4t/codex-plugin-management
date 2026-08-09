---
name: obsidian-study-vault-workflow
description: obsidain 中文学习库沉淀工作流。用于 /Users/yuzhou4tc/Documents/obsidain 的 IMA/公众号资料入库、来源记录、解释页、概念卡、计量经济学公式推导、MOC/README/处理日志更新和安全 Git 发布。
---

# Obsidian Study Vault Workflow

Use this skill when the user mentions `/Users/yuzhou4tc/Documents/obsidain`, obsidain, Obsidian 学习库, IMA 公众号知识库入库, 来源记录, 解释页, 概念卡, 计量经济学笔记, 公式推导, Claudian, or publishing the vault to GitHub.

Use `ima-skill` together with this skill when the task needs IMA OpenAPI calls. This skill defines the vault workflow and file-shape conventions.

## First Checks

1. Work from `/Users/yuzhou4tc/Documents/obsidain`.
2. Read the real vault state before answering or editing:
   - `MOC - 总首页.md`
   - relevant MOC/rule files under `90_系统/`
   - relevant source/chapter/concept notes
   - `git status --short`
3. Default to Simplified Chinese for vault content.
4. Keep changes additive and scoped. Do not delete existing notes or create broad speculative taxonomies.

## Source-To-Study Pattern

For IMA, public-account, article, and paper-reading ingestion, use this landing pattern:

1. `来源记录` or source/article page: source metadata, traceable quote or retrieval note, attachment/source pointer, and unresolved verification notes.
2. `解释页` or reading note: user-friendly explanation in readable Markdown, not a raw paste.
3. `概念卡`: short reusable concept page when a method or term will recur.
4. MOC entry and processing log: link the new notes from the relevant index and record what changed.

Keep source boundaries explicit. Do not copy a full third-party article into the vault when a source pointer plus transformed study note is enough.

## Econometrics Pattern

- Chapter learning notes live under `01_学习知识库/计量经济学/`.
- Source notes live under `04_资料源/计量经济学/`.
- Generic concepts and derivations live under `03_通用知识库/计量经济学/`.
- Long derivations belong in `03_通用知识库/计量经济学/公式推导/` and should be linked from chapter notes instead of duplicated there.
- When adding a durable derivation or concept, update the relevant MOC, README, and `90_系统/处理日志/处理日志.md`.

## Git Safety

Before any vault publish or commit:

1. Inspect `.gitignore`.
2. Inspect `git status --short` and `git diff --stat`.
3. Protect private/local state such as `.claudian/`, `00_收集箱/`, `.obsidian/plugins/`, private HFT drafts, caches, and raw attachment folders.
4. For the existing `origin https://github.com/yuzhou4t/obsidian-study.git` remote, do not force-push unless the user explicitly asks and understands the history rewrite.
5. If unrelated remote history appears, prefer the established safe path: fetch remote, merge with `-s ours --allow-unrelated-histories`, then push.

## Response Shape

For vault work, report:

- source and target note paths
- whether content is source record, explanation, concept, or derivation
- index/log files updated
- git safety checks if publishing is involved
- any source access or verification gaps
