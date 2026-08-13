---
name: apply-personal-app-design-system
description: Apply the shared white-blue and navy visual system distilled from the user's TTS and AI Recording desktop apps. Use when creating or redesigning the user's own macOS, desktop, or local web software; harmonizing settings, sidebars, cards, floating panels, OCR/translation windows, screenshot tools, forms, or dashboards; or translating the same design language between SwiftUI/AppKit and React/Tauri/CSS. Preserve existing business flows and platform behavior while standardizing visual tokens, components, interaction states, dark mode, and visual QA.
---

# Apply Personal App Design System

Build the user's software as one recognizable family: calm ice-blue surfaces in light mode, restrained navy surfaces in dark mode, compact information density, native typography, and clear blue actions.

## Start From Evidence

1. Inspect the current repository, its applicable `AGENTS.md`, live UI, screenshots, and existing tokens before editing.
2. Identify the exact user flow and preserve its behavior. Treat visual unification as a styling and hierarchy task unless the user explicitly changes product behavior.
3. Capture representative current surfaces when possible: navigation, dense content, settings/form, floating utility, and a transient state such as loading or selection.
4. Do not claim visual verification for a surface that could not be opened and captured. Separate code/token verification from live screenshot verification.
5. Treat credentials, private content, and user data visible during capture as sensitive. Do not place them in this skill or in design examples.

When the source projects are available, use these high-signal references without assuming they are unchanged:

- TTS: `Sources/TTS/UI/Design/TTSVisualStyle.swift` and related SwiftUI/AppKit surfaces.
- AI Recording: `packages/ui/src/tokens/theme.ts`, `apps/desktop/src/styles.css`, and `apps/desktop/src/components/app-shell.tsx`.

## Choose The Work Mode

- **New product:** establish semantic tokens and the shell first, then build one representative content page and one settings/form page.
- **Existing product:** inventory all visible surfaces, map existing values to semantic tokens, and replace inconsistent styling surgically without rewriting business logic.
- **Cross-platform port:** preserve semantic roles and interaction hierarchy; use native controls and icon libraries rather than copying framework-specific implementation.
- **Small utility or floating panel:** use the same tokens at a reduced scale. Keep one dominant action, one surface level, and compact spacing.

## Apply The System

1. Read [references/design-system.md](references/design-system.md) completely before choosing colors, spacing, radius, typography, elevation, or component states.
2. Read [references/platform-mapping.md](references/platform-mapping.md) for the implementation stack in use.
3. Create or consolidate semantic tokens before styling individual screens. Do not scatter raw colors and radii across feature files.
4. Build hierarchy in this order: window background, navigation/shell, raised surfaces, controls, primary action, status feedback.
5. Keep glass restrained. Use translucent near-white or navy surfaces with a fine blue border; avoid stacking multiple blur/material layers into gray slabs.
6. Use blue for selection and primary actions. Reserve cyan and warm amber glows for distant atmosphere, never for competing primary actions.
7. Normalize icon canvases, button heights, text baselines, and focus states across every toolbar or action row.
8. Implement light and dark mode together. Dark mode uses navy, not pure black, and retains readable surface separation.
9. Run [references/qa-checklist.md](references/qa-checklist.md) before handoff.

## Preserve Product Boundaries

- Keep screenshot capture, clipboard copy, OCR, translation, recording, storage, and AI operations as separate workflows when the product already separates them.
- Do not introduce new branding, mascots, fonts, gradients, animation systems, or features merely to fill visual space.
- Do not replace native platform affordances when their behavior matters. Wrap or tint them consistently instead.
- Do not use gray grouped forms, deeply nested cards, excessive shadows, or low-contrast disabled controls as the default hierarchy.
- Do not communicate status through color alone. Pair color with text or an icon.
- Do not embed secrets or machine-specific private paths in reusable examples.

## Handoff

Report:

1. Which surfaces were changed.
2. Which semantic tokens and shared components now control them.
3. Which user flows were intentionally preserved.
4. Which light, dark, compact, and accessibility checks passed.
5. Which visual claims are code-only and which were verified from live screenshots.

End with one concrete next action: inspect a named screen, approve the direction, or continue the same system into the next surface.
