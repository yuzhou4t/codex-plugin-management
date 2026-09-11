# Task contract

Create a UTF-8 JSON file. Relative `cwd` values resolve from the task file's directory. Paths in `allowed_paths` are always relative to `cwd`.

```json
{
  "id": "unique-task-id",
  "mode": "engineering",
  "cwd": "/absolute/project/subdirectory",
  "goal": "Implement the agreed behavior and keep existing unrelated changes.",
  "allowed_paths": ["src/feature.py", "tests/test_feature.py"],
  "workspace_write": false,
  "allowed_commands": [
    {"argv": ["python3", "-m", "pytest", "tests/test_feature.py"], "timeout_seconds": 180}
  ],
  "checks": [
    {"argv": ["python3", "-m", "pytest", "tests/test_feature.py"], "timeout_seconds": 180}
  ],
  "acceptance": [
    "The requested behavior is implemented.",
    "The focused regression test passes.",
    "No file outside allowed_paths changes."
  ],
  "web": false,
  "model": null,
  "reasoning_effort": null,
  "timeout_seconds": 1800,
  "max_turns": 40
}
```

## Fields

- `id`: unique identifier containing letters, numbers, `_`, or `-`.
- `mode`: `research`, `engineering`, `frontend`, or `review`.
- `cwd`: the smallest useful workspace. It must already exist.
- `goal`: the complete result Grok should produce. Do not include secrets or unrelated private context.
- `allowed_paths`: exact files or directories Grok may create, edit, or delete. Use this for narrow tasks and research deliverables.
- `workspace_write`: set true when the user wants Grok to work like Codex across the task workspace without enumerating every normal source file. It permits ordinary files below `cwd` while `.git`, `.codex`, `.agents`, `.grok`, `.env`, and `.env.*` remain protected and any change there fails scope verification. Keep `cwd` at the smallest useful project root.
- `allowed_commands`: exact argument arrays Grok may run while implementing. Declare dependency installation here only when already authorized.
- `checks`: argument arrays the adapter reruns independently after Grok exits. Each check is also made available to Grok.
- `acceptance`: observable requirements, as a string or list of strings.
- `web`: enables Grok web search and fetch. It defaults to true for research and false otherwise.
- `model` and `reasoning_effort`: optional. Omit them to preserve the user's Grok defaults.
- `timeout_seconds`: 30 to 3600; default 1800.
- `max_turns`: 1 to 80; default 40.

Commands are executed without a shell during host verification. Shell operators such as `&&`, `|`, redirects, substitutions, and glob expansion do not work. Split compound checks into separate entries.

For a planned engineering task that may create or reorganize several files, use `workspace_write: true`, keep `allowed_paths: []`, and declare the required implementation and check commands. This is the project-level write mode. For a one-file fix or a research report, prefer explicit `allowed_paths`.

## Research example

```json
{
  "id": "research-example",
  "mode": "research",
  "cwd": "/absolute/project/reports/topic",
  "goal": "Research the specified topic using current primary sources. Write a Chinese report with inline source links, dates, disagreements, and evidence limits.",
  "allowed_paths": ["research.md"],
  "allowed_commands": [],
  "checks": [],
  "acceptance": [
    "The report exists and answers the requested questions.",
    "Material claims link to opened primary sources.",
    "Unverified claims and missing evidence are explicit."
  ],
  "web": true
}
```

After the adapter returns `needs_source_review`, Codex opens the central sources, checks that they support the report, and distinguishes current verification from Grok's claims.

## Frontend example

Use `mode: "frontend"`, list only the UI files that may change, and provide a host check that launches the trusted local page and records non-empty screenshots. After checks pass, Codex must inspect the actual desktop and mobile interface and exercise the changed interaction before accepting it.
