# hyperframes

OpenAI Codex plugin for [HyperFrames](https://hyperframes.heygen.com) — an open-source video rendering framework where HTML is the source of truth for video.

## What's included

Four skills for authoring and rendering video:

- **hyperframes** — framework-specific composition, timing, timeline, media, and deterministic-capture contracts, with optional visual references
- **hyperframes-cli** — CLI operation using the installed release's live `--help` and `doctor` output
- **hyperframes-registry** — `hyperframes add` to install reusable blocks and components (social overlays, shader transitions, data viz, effects)
- **website-to-hyperframes** — explicitly requested website-to-video work, routed to a quick or narrated/full production path

General GSAP guidance comes from the standalone official GSAP skills rather than a duplicate skill in this plugin.

## Requirements

The skills invoke the `hyperframes` CLI via `npx hyperframes`, which needs:

- Node.js ≥ 22
- FFmpeg on `PATH`

Use `npx hyperframes --help` and `npx hyperframes doctor` for the installed command surface and environment checks. See [hyperframes.heygen.com/quickstart](https://hyperframes.heygen.com/quickstart) for setup context.

## Source and local policy

The framework material comes from [`heygen-com/hyperframes`](https://github.com/heygen-com/hyperframes). This repository is the deployment source for the local plugin and intentionally narrows triggers, treats visual direction as optional, and delegates general GSAP guidance to the standalone official GSAP skills. Review those local policy differences before syncing future upstream changes.
