# Image Gen Website Concepts

Read this reference only after deciding that a generated concept or custom visual asset will materially help the requested frontend.

## Brief the requested surface

Ground the brief in evidence from the user, repository, screenshots, and brand assets:

- purpose, audience, and page or product scope
- required sections, states, navigation, copy, data fields, and calls to action
- supplied brand language, imagery, and visual references
- interaction and responsive requirements
- implementation constraints, including which text and controls must remain code-native
- negative constraints that prevent unrelated sections, fake metrics, invented claims, or impractical UI

Ask for a complete surface only when a complete surface is useful. A hero request needs a hero concept; a dashboard may need one primary-screen concept; a long page may benefit from an overview. Do not default to one image per section.

## Choose the minimum useful output

- Start with one concept when it can resolve the visual direction clearly.
- Request a separate state or detail only when the first concept leaves a material implementation question unanswered.
- Generate standalone production assets when the design depends on custom imagery, illustration, texture, packaging, scenery, or game art.
- Keep functional interface text, inputs, navigation, controls, tables, and status information in code.
- Prefer transparent or clean-cutout assets when they must layer into the UI.

## Keep the concept implementable

Ask for:

- a clear hierarchy and focal point
- legible typography and controls
- a coherent palette and spacing rhythm
- stable media frames and practical responsive continuation
- reusable component families rather than decorative repetition
- an intentional container model appropriate to the product

Avoid requesting visual filler, unreadable compressed screens, fake product data, excessive cards, or effects that cannot be recreated accessibly.

## Translate the result into code

Before implementation, inspect the selected concept and extract:

- layout, section or state order, and responsive implications
- visible copy and content hierarchy
- color, typography, spacing, radius, border, and shadow tokens
- repeated components and interaction states
- asset inventory and image treatment

Treat the concept as a visual reference, not permission to ignore repository conventions, accessibility, or functional requirements. If implementation must deviate, preserve the user's intent and report the material deviation.

During visual verification, compare the rendered surface with the selected concept at relevant viewports and fix concrete differences that affect hierarchy, readability, interaction, responsive behavior, or brand fidelity.
