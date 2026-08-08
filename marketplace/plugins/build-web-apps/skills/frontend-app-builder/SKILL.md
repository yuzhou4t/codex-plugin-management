---
name: frontend-app-builder
description: Design and implement a visually distinctive frontend when the user explicitly asks for a greenfield website, landing page, product interface, dashboard, game surface, or a substantial visual redesign/restyle. Do not use for routine feature work, isolated CSS fixes, frontend debugging, backend changes, or implementation inside an already-settled design system.
---

# Frontend App Builder

Build the requested visual surface with the smallest process that produces a coherent, usable result. Treat an existing repository, supplied reference, or approved design as stronger than this skill's defaults.

## Establish the route

Inspect the live project and choose one route:

- **Direct implementation** — Use when the user supplied clear requirements or the repository already has a usable design system.
- **Reference-led implementation** — Use when screenshots, a Figma file, an existing page, or brand assets define the direction.
- **Concept-led implementation** — Use when the visual direction is genuinely open and exploring a concept would materially reduce uncertainty.

Do not create a concept or approval checkpoint merely because the task involves a frontend. If the user asks to review concepts before implementation, pause after presenting them. Otherwise proceed with explicit, low-risk design assumptions.

## Use visual generation selectively

Image generation is optional. Use the installed image-generation or product-design capability only when custom imagery, art direction, or a visual concept materially improves the result.

- Do not generate an image for every section.
- Do not use generated screenshots as the shipped interface.
- Keep navigation, controls, forms, tables, labels, and other functional UI code-native.
- Reuse supplied brand assets and repository assets before generating replacements.
- Generate focused assets or an additional detail concept only when a material visual question remains unresolved.

When using Image Gen for a website concept, read [references/imagegen-website-concepts.md](references/imagegen-website-concepts.md).

## Design before implementation

Record only the decisions needed to build:

- information architecture and visible copy
- layout and responsive behavior
- typography, color, spacing, radius, border, and elevation tokens
- reusable component families and interaction states
- required imagery or media

Preserve the user's content and product story. Do not invent claims, metrics, sections, or complex interactions to make the page look fuller.

## Implement surgically

- Follow the repository's framework, routing, styling, component, accessibility, and asset conventions.
- Prefer shared tokens and components for repeated patterns, without introducing abstractions used only once.
- Build the real requested surface rather than a decorative shell around missing functionality.
- Make required controls and primary interactions work.
- Keep responsive behavior intentional at the viewports that matter to the request.
- Respect `prefers-reduced-motion` and use motion only when it clarifies hierarchy or state.

For React, Next.js, shadcn/ui, or provider-specific concerns, use the currently installed specialist skill rather than duplicating its rules here.

## Verify proportionately

Run the narrowest relevant build, type check, lint, or test command. For material visual work:

1. Open the implementation in the available browser.
2. Exercise the primary interaction path.
3. Check the main desktop viewport and at least one narrower viewport when responsive behavior is in scope.
4. Compare against supplied or accepted references when they exist.
5. Fix material issues such as clipping, overflow, unreadable text, broken assets, inert controls, or clear reference drift.

Completion means the requested experience works, the relevant checks pass, and no material visual defect remains. Do not impose a numeric fidelity score or continue subjective iteration without new evidence.

## Handoff

Report:

- the surface implemented or redesigned
- the visual route used and whether generated assets were needed
- verification performed
- any intentional deviation or unresolved blocker
