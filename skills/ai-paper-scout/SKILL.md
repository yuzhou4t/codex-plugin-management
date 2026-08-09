---
name: ai-paper-scout
description: Find, triage, and prepare recent AI research papers from the user's preferred CCF A-class artificial intelligence conferences and journals. Use when the user asks to search for AI papers, recent AI research, papers worth reading, CCF A AI venues, AAAI, NeurIPS, ACL, CVPR, ICCV, ICML, ICLR, AIJ, TPAMI, IJCV, JMLR, or to prepare AI papers for Zotero or reading notes.
---

# AI Paper Scout

## Overview

Use this skill to search AI papers from the user's preferred CCF A-class AI venues, then return a concise Chinese reading shortlist with source links and import-ready metadata.

Read `references/ccf-ai-venues.md` before doing venue-specific searches.

## Workflow

1. Identify the user's topic and time window. If unspecified, default to the last 12 to 18 months and the themes in the reference file.
2. Search venue-first, not keyword-only:
   - Start from official proceedings, official award pages, OpenReview, ACL Anthology, CVF, PMLR, NeurIPS, AAAI, journal issue pages, and DBLP venue pages.
   - Use arXiv, author/project pages, Semantic Scholar, or Google Scholar only to complete PDFs, abstracts, citation context, code links, or missing metadata.
3. Prefer primary sources for claims about acceptance, venue, year, awards, proceedings, DOI, and official PDFs. Browse because recent paper lists, awards, and journal issues change.
4. Score candidates by relevance to the user's topic, venue priority, recency, signal of importance, and usefulness for reading. Treat awards, oral/spotlight status, official benchmark papers, influential datasets, strong surveys, and widely discussed systems as positive signals.
5. Return a Chinese shortlist. For each paper include title, venue/year, research direction, why it matters, official/source link, PDF/arXiv link when available, and Zotero import readiness.
6. If the user asks to add papers to Zotero, use the Zotero skill/API or Zotero Connector flow. Confirm exact records and destination collection before writing. Do not manually copy PDFs into Zotero `storage`.

## Output Shape

For a broad "recent AI papers worth reading" request, group results by theme:

- reasoning and test-time compute
- agents, tools, and multi-agent systems
- multimodal models and document understanding
- long context and efficient attention
- world models, robotics, 3D, 4D, and video
- AI for science and formal/code verification
- safety, alignment, hallucination, provenance, and evaluation

For a narrow topic, use a compact table followed by a recommended reading order. Keep the list actionable rather than exhaustive.

## Guardrails

- Do not invent venue placement, awards, DOI, PDFs, code links, or Zotero import status.
- Do not rely on DBLP alone for full text; DBLP is primarily a bibliography index.
- Distinguish conference papers, journal articles, workshops, surveys, benchmarks, demos, and blog/project pages.
- When a paper is upcoming, accepted but not yet in proceedings, or only visible in a public list, say so explicitly.
