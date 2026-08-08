---
name: hyperframes
description: Create or edit HyperFrames HTML video compositions, including timed clips, registered GSAP timelines, media playback, captions, voiceovers, audio-reactive visuals, and scene transitions. Use when the user explicitly asks to author or modify a HyperFrames composition. For CLI commands, environment checks, preview, or rendering, also use the hyperframes-cli skill.
---

# HyperFrames

HyperFrames uses HTML as the video source of truth. A composition combines timed `data-*` clip attributes, CSS layout, and a synchronously registered GSAP timeline. Preserve those framework contracts; treat visual style and animation density as creative choices.

## Workflow

1. Read the existing composition and project guidance before editing. Reuse an existing `DESIGN.md`, `visual-style.md`, palette, typography, and motion language when present.
2. For a new composition, decide the dimensions, clips, tracks, durations, and media before animation.
3. Build the most informative static frame first. Verify layout, hierarchy, and readable contrast.
4. Add only the motion that serves the content. Register a paused timeline for each composition.
5. Run the supported lint and visual-inspection commands described in `hyperframes-cli`. Preview before rendering; render only when the user asks for an exported video.

For a small edit, skip planning artifacts and change only the requested property or timing.

## Clip Attributes

### All timed clips

| Attribute | Requirement | Notes |
| --- | --- | --- |
| `id` | Required | Unique in the document |
| `data-start` | Required | Seconds or a clip reference such as `"intro + 2"` |
| `data-duration` | Required for images, divs, and compositions | Video/audio may use media duration |
| `data-track-index` | Required | Clips on the same track cannot overlap |
| `data-media-start` | Optional | Trim offset in seconds |
| `data-volume` | Optional | `0`–`1`, default `1` |

`data-track-index` controls timeline tracks, not visual stacking. Use CSS `z-index` for stacking.

### Composition clips

| Attribute | Requirement | Notes |
| --- | --- | --- |
| `data-composition-id` | Required | Unique composition identifier |
| `data-start` | Required | Root compositions normally start at `"0"` |
| `data-duration` | Required | Authoritative duration |
| `data-width` / `data-height` | Required | For example `1920x1080` or `1080x1920` |
| `data-composition-src` | Optional | External sub-composition HTML |

## Composition Structure

A standalone `index.html` places its `data-composition-id` element directly in `<body>`. Do not wrap a standalone composition in `<template>`, because the browser will not render template content.

An external sub-composition uses a template:

```html
<template id="title-card-template">
  <div
    data-composition-id="title-card"
    data-start="0"
    data-duration="6"
    data-width="1920"
    data-height="1080"
  >
    <div class="scene-content">
      <h1>Title</h1>
    </div>
    <style>
      [data-composition-id="title-card"] {
        position: relative;
        overflow: hidden;
      }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      tl.from(".scene-content", { opacity: 0, y: 40, duration: 0.5 });
      window.__timelines["title-card"] = tl;
    </script>
  </div>
</template>
```

Reference it from the root composition with a timed clip:

```html
<div
  id="title-card-clip"
  data-composition-id="title-card"
  data-composition-src="compositions/title-card.html"
  data-start="0"
  data-duration="6"
  data-track-index="1"
></div>
```

## Timeline Contract

- Create timelines with `{ paused: true }`; the HyperFrames player controls playback.
- Register every timeline as `window.__timelines["<composition-id>"] = tl`.
- Construct and register timelines synchronously. Do not use `async`, promises, or `setTimeout`.
- Let the framework nest sub-composition timelines. Do not add them to a parent GSAP timeline manually.
- `data-duration` is authoritative. Do not add empty tweens to manufacture duration.
- Use finite repeat counts. `repeat: -1` prevents deterministic capture.
- Do not animate the same property on the same element from competing timelines.
- For a clip that appears later, schedule `tl.set(selector, vars, timePosition)` at or after its `data-start`; a top-level `gsap.set()` may run before the clip exists.
- Use seeded values instead of `Math.random()`, `Date.now()`, or wall-clock-dependent logic.

Use standard GSAP skills for general tween, timeline, easing, and performance guidance. HyperFrames-specific constraints in this file take precedence.

## Media Contract

Video is muted and inline. Put its audio on a separate track:

```html
<video
  id="visual"
  src="clip.mp4"
  data-start="0"
  data-duration="30"
  data-track-index="0"
  muted
  playsinline
></video>
<audio
  id="sound"
  src="clip.mp4"
  data-start="0"
  data-duration="30"
  data-track-index="2"
  data-volume="1"
></audio>
```

- Do not call `play()`, `pause()`, or seek media; the framework owns playback.
- Do not animate video dimensions directly. Animate a wrapper.
- Do not put a timed video inside another timed clip.
- Add `crossorigin="anonymous"` to external media.

## Layout and Choreography

- Build the visible end state in CSS, then animate from or to it.
- Prefer normal layout, flexbox, or grid for content. Reserve absolute positioning for intentional layers and decoration.
- Avoid CSS transform-based centering on elements whose transforms GSAP will animate; use a wrapper or flex/grid centering.
- Transitions, jump cuts, entrances, exits, and holds are editorial choices. Use the treatment that fits the pacing; every element does not need an animation.
- Preserve intentional stillness. Ambient motion is optional, not a framework requirement.
- For dynamic text, use `window.__hyperframes.fitTextFontSize(...)` when the copy length is not known in advance.

## Verification

Discover the installed CLI surface before relying on remembered flags:

```bash
npx hyperframes --help
npx hyperframes lint
npx hyperframes inspect
```

Run `npx hyperframes validate` only when `npx hyperframes validate --help` confirms that command exists in the installed version. Use `npx hyperframes doctor` when the environment or render pipeline fails.

For significant animation work, run the bundled map using the actual directory that contains this `SKILL.md`:

```bash
node <hyperframes-skill-root>/scripts/animation-map.mjs <composition-dir> \
  --out <composition-dir>/.hyperframes/anim-map
```

Skip the animation map for a narrow color, copy, or duration edit. Report which checks ran and any unsupported command explicitly.

## References

Load only what the task needs:

- [references/captions.md](references/captions.md) — captions, lyrics, and audio-synced text.
- [references/tts.md](references/tts.md) — narration and voice generation.
- [references/audio-reactive.md](references/audio-reactive.md) — precomputed audio-driven motion.
- [references/css-patterns.md](references/css-patterns.md) — marker, circle, burst, scribble, and sketch effects.
- [references/typography.md](references/typography.md) — font support and text fitting.
- [references/motion-principles.md](references/motion-principles.md) — optional choreography guidance.
- [references/transitions.md](references/transitions.md) — transition selection and implementation.
- [references/transcript-guide.md](references/transcript-guide.md) — transcription formats and troubleshooting.
- [references/dynamic-techniques.md](references/dynamic-techniques.md) — advanced animation techniques.
- [visual-styles.md](visual-styles.md), [house-style.md](house-style.md), and `palettes/` — optional starting points when the user has not supplied a style.
- [patterns.md](patterns.md) — common composition patterns.
- [data-in-motion.md](data-in-motion.md) — data and infographic patterns.
