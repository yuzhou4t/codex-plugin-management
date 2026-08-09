---
name: ltci-public-data-engineering
description: Long-term care insurance public data engineering workflow. Use when working on 长护险, 长期护理保险政府侧智能资源配置模型, LTCI official public data, source_registry.csv, policy source coverage, raw/interim/processed CSV pipelines, quality audits, or 49 pilot city resource and policy data.
---

# LTCI Public Data Engineering

## Overview

Use this skill for the long-term care insurance official public data workspace. The project turns registered official sources into standardized research CSVs with traceable raw files, intermediate extracts, processed tables, logs, and quality reports.

## Hard Boundaries

- Use official public sources only.
- Every real source must be registered in `source_registry/source_registry.csv` before ingestion.
- Do not invent, infer, or backfill undisclosed values. Keep unavailable fields as `null`.
- Do not put personal phone numbers, ID numbers, emails, or other sensitive personal details into `processed/`.
- Preserve English directory names because scripts depend on them.
- Geographic API calls stay dry-run or queue-only unless the user provides and authorizes an API key.
- `knowledge_base/`, `benchmark/`, and `model_inputs/` are paused unless the user explicitly restarts that phase.

## Orientation

1. Confirm whether the active root is the top-level data folder or `ltci-gov-resource-allocation`.
2. Read these first when present:
   - `README.md`
   - `00_数据资产导航.md`
   - `reports/data_inventory_current.md`
   - `reports/current_official_data_ingest_status.md`
   - `reports/data_quality_audit_current.md`
   - `scripts/README.md`
3. Inspect the exact source registry, schema, script, or report relevant to the user's requested city, table, or data category.

## Data Flow

Use the established flow:

```text
source_registry/source_registry.csv
  -> raw/
  -> interim/
  -> processed/
  -> reports/ and logs/
```

When adding or repairing data:

1. Register the source with enough metadata to re-fetch or audit it.
2. Save the official original file or HTML into `raw/`.
3. Extract text, tables, or queues into `interim/`.
4. Standardize research-ready rows into the relevant `processed/` table.
5. Refresh indexes, inventory, and quality reports.
6. Explain coverage changes using reports rather than memory.

## Common Commands

Use the project README as the source of truth, but these are common verification and refresh scripts in the main workspace:

```bash
python scripts/49_build_chinese_file_aliases.py
python scripts/88_refresh_structure_inventory.py
python scripts/54_build_49_pilot_resource_indicator_coverage.py
python scripts/45_run_data_quality_audit.py
python scripts/43_build_geocode_queue.py
```

Run only the scripts relevant to the change. If a parser or registry script has a numbered local workflow, preserve that numbering convention.

## Output Shape

For data work, report:

- Which source registry rows, raw files, interim files, processed tables, reports, or logs changed.
- Coverage before and after when available.
- Which audit or refresh scripts ran.
- Any missing cities, blocked sources, null-heavy fields, or manual follow-ups.
- Whether the result is ready for research analysis.

## Pitfalls

- Do not search the web and ingest a source just because it looks useful; the registry gate comes first.
- Do not overwrite raw official files with cleaned data.
- Do not rename directories to Chinese names. Use the Chinese index files instead.
- Do not treat policy text extraction as the same thing as structured model input unless the current phase says so.
- Do not use a browser-visible table as evidence of readiness until the saved raw/interim/processed trail exists.
