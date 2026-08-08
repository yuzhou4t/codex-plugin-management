---
name: website-to-hyperframes
description: Turn an existing website into a HyperFrames video. Use only when the user explicitly asks to capture, adapt, or turn a named website or URL into a promo, product tour, social ad, or other video. Do not trigger merely because a URL is present.
---

# Website to HyperFrames

Capture the source website, select the smallest production route that fits the request, and build a HyperFrames composition from verified site assets and brand cues.

## Start With Live Capabilities

Before choosing commands or flags:

```bash
npx hyperframes --help
npx hyperframes doctor
```

Use `npx hyperframes <command> --help` before relying on uncommon flags. If `doctor` is unavailable, report that and check the project requirements directly.

## Choose a Route

### Quick route

Use for short, non-narrated promos, teasers, loops, or a user who asks for a fast first cut.

1. Capture the relevant page states and assets. Read [references/step-1-capture.md](references/step-1-capture.md) only for the capture mechanics needed.
2. Record a compact working brief: audience, format, duration, two or three beats, brand colors/type, and selected assets. Do not create `DESIGN.md`, `SCRIPT.md`, or `STORYBOARD.md` unless they will materially help this video.
3. Build one root composition or a small set of sub-compositions using the `hyperframes` skill. Static holds and hard cuts are valid when intentional.
4. Run the supported verification path below and hand off the Studio preview URL.

### Narrated/full route

Use when the user requests narration, a product tour, a longer campaign asset, multiple deliverable formats, or a documented production package.

1. Capture and summarize the website: [step-1-capture.md](references/step-1-capture.md).
2. Create a reusable brand brief when needed: [step-2-design.md](references/step-2-design.md).
3. Write the narration or structured beat copy: [step-3-script.md](references/step-3-script.md).
4. Plan assets, shots, and timing: [step-4-storyboard.md](references/step-4-storyboard.md).
5. If narration was requested, generate or ingest audio and map real timings: [step-5-vo.md](references/step-5-vo.md).
6. Build compositions: [step-6-build.md](references/step-6-build.md) and the `hyperframes` skill.
7. Verify and deliver: [step-7-validate.md](references/step-7-validate.md).

The reference files contain detailed techniques, not universal gates. Create only artifacts that the chosen route needs. Do not generate narration, captions, music, or a rendered MP4 unless the user requested them.

## Source Fidelity

- Use captured assets by file path instead of inlining or recreating them when the original is available.
- Preserve the source brand unless the user asks for a reinterpretation.
- Verify text and claims against the captured site; do not invent product features.
- Treat login-only, personal, or sensitive states as out of scope unless the user explicitly provides access and asks for them.
- If the site changes during the task, state which captured state the video represents.

## Verification and Delivery

Run the commands supported by the installed CLI:

```bash
npx hyperframes lint
npx hyperframes inspect
npx hyperframes preview
```

Run `npx hyperframes validate` only if `npx hyperframes validate --help` succeeds. For snapshot, render, viewport, or format flags, check that subcommand's live help first.

Fix structural errors and review representative frames. Use the active Studio URL as the primary handoff:

```text
http://localhost:<port>/#project/<project-name>
```

Render to MP4 only on explicit request. When rendering, use a predictable output name and report its absolute path.

## Formats

- Landscape: `1920x1080`
- Portrait: `1080x1920`
- Square: `1080x1080`

Use the format requested by the user; otherwise infer from the stated destination and say what you chose.

## Additional Reference

- [techniques.md](references/techniques.md) — optional visual techniques for storyboarding or implementation.
