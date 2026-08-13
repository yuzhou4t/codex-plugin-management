# Personal App Design System

## 1. Character

Use a quiet desktop utility aesthetic:

- ice-blue light environment;
- navy dark environment;
- near-white or navy glass surfaces with fine blue borders;
- compact, legible information density;
- native typography and familiar platform icons;
- saturated blue only for primary action, selection, and focus;
- cyan and warm amber only as low-opacity atmospheric light.

The interface should feel clear and capable before it feels decorative.

## 2. Semantic Color Tokens

Use semantic names. Adjust exact values only when contrast or platform rendering requires it.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| `background-start` | `#F6FBFF` | `#06111F` | Window gradient origin |
| `background-end` | `#E6F2FF` | `#0B1F38` | Window gradient destination |
| `surface` | `rgba(255,255,255,.94)` | `rgba(14,31,54,.94)` | Main cards and panels |
| `surface-raised` | `rgba(255,255,255,.97)` | `rgba(19,41,69,.96)` | Floating panels and focused cards |
| `surface-control` | `#F6FAFF` | `#1A385E` | Fields and secondary controls |
| `text-primary` | `#172033` | `#E8EFFF` | Main copy |
| `text-secondary` | `#59697D` | `#91A1C2` | Supporting copy |
| `border` | `rgba(179,209,245,.48)` | `rgba(102,166,255,.32)` | Panel border |
| `border-subtle` | `rgba(194,214,240,.44)` | `rgba(122,166,214,.30)` | Dividers and controls |
| `accent` | `#407DF5` | `#66A6FF` | Primary action and selection |
| `accent-strong` | `#2161DB` | `#4F91FA` | Pressed state and gradient end |
| `selection` | `#1487FF` | `#33ADFF` | Screenshot and direct manipulation |
| `success` | `#22B85A` | `#4BD17A` | Confirmed success |
| `warning` | `#E89113` | `#FFB84D` | Attention and pending state |
| `danger` | `#DC4C4C` | `#FF7070` | Destructive action and error |
| `ambient-cyan` | `#58DDF0` | `#496BFF` | Background glow only |
| `ambient-warm` | `#FFAC5D` | `#65E6FF` | Background glow only |

Rules:

- Use no more than one saturated functional accent in a local control group.
- Keep ambient glows below 24% opacity and away from body text.
- Use opaque or nearly opaque control fills over complex backgrounds.
- Never render primary text directly over a glow without a stable surface.

## 3. Typography

- Prefer the operating system font stack: `-apple-system`, `BlinkMacSystemFont`, `"PingFang SC"`, `"Segoe UI"`, `sans-serif`.
- Do not add a custom font dependency without an explicit brand requirement.
- Use weights sparingly: regular for body, medium for controls, semibold for primary actions and headings.

| Role | Size | Weight | Line height |
| --- | --- | --- | --- |
| Page title | 24–28 | 650 | 1.2 |
| Section title | 16–18 | 600 | 1.3 |
| Card title | 14–16 | 600 | 1.35 |
| Body | 13–14 | 400 | 1.55 |
| Control | 12–13 | 500 | 1.3 |
| Caption | 11–12 | 400 | 1.4 |

Keep Chinese labels intact. Avoid narrow fixed widths that truncate four-character actions or mixed Chinese/English model names.

## 4. Spacing And Sizing

Use a 4-point base scale:

- `4`: icon optical correction, tight internal gap;
- `8`: compact control gap;
- `12`: normal control padding;
- `16`: card padding or row gap;
- `24`: page and section gap;
- `32`: large separation only.

Desktop defaults:

- page padding: `24`;
- card padding: `16–20`;
- row height: `40–48`;
- compact button height: `32`;
- primary/form button height: `36`;
- icon button: `36×36` or `38×38`;
- toolbar text button: equal height and aligned baseline;
- navigation width: `172–232`, determined by label length and product density.

## 5. Radius And Elevation

| Role | Radius |
| --- | --- |
| Window or large shell | `20` |
| Panel/card | `16` |
| Nested card | `12` |
| Control/button | `10` |
| Compact nav/tag | `8` |

Elevation:

- standard surface: `0 3px 8px rgba(0,0,0,.05)`;
- raised surface: `0 9px 18px rgba(0,0,0,.12)`;
- primary blue glow: `0 4px 8px rgba(64,125,245,.22)`;
- dark mode shadows may increase opacity slightly but must not erase borders.

Use continuous/squircle corners when the platform supports them. Do not mix unrelated radius values on the same screen.

## 6. Composition

### Application shell

- Use one clear navigation rail and one content workspace.
- Let the background carry atmospheric light; keep navigation and content surfaces calm.
- Highlight only the active navigation item with a blue tint, blue icon/text, and clear outline.
- Align page title and primary page action on one top axis.

### Cards and forms

- Prefer one parent card with rows and fine dividers over many nested gray cards.
- Place labels above fields for narrow layouts and in aligned columns for wide desktop layouts.
- Keep the primary action at the end of the reading flow.
- Use status text near the affected control, not only in a distant toast.

### Floating utilities

- Use a raised surface, `16` radius, fine blue border, and one dominant action.
- Keep utility panels compact and content-first.
- Pin, copy, cancel, and secondary actions use consistent icon canvas and control height.

### Screenshot and annotation tools

- Use a strong blue selection border with a dark outer shadow for contrast on light and dark captures.
- Use blue handles with a white outline.
- Normalize every symbol into an `18×18` canvas.
- Keep tool buttons equal width where labels are comparable; use `36` height and center all icon/text groups on the same axis.
- Use solid blue for the selected tool and Copy; use pale-blue secondary controls for Undo and Cancel.

## 7. Interaction States

Every interactive component must define:

- default;
- hover;
- pressed;
- selected/current;
- keyboard focus;
- disabled;
- loading or pending when applicable;
- success/error feedback when applicable.

Recommended behavior:

- hover: raise by at most `1px` and strengthen the blue border;
- pressed: scale to `0.98` or reduce brightness, not both aggressively;
- focus: visible `2px` blue ring with separation from the control border;
- disabled: retain readable text and shape at roughly 45–60% emphasis;
- selected: pair blue color with a fill, checkmark, label, or icon state.

## 8. Motion

- fast feedback: `120ms`;
- normal control transition: `180ms`;
- panel/state transition: `260ms`;
- use ease-out for entrance and standard ease for hover;
- respect Reduce Motion and remove transforms/parallax when enabled;
- avoid continuous decorative motion in productivity views.

## 9. Common Failure Modes

Avoid:

- gray native grouped forms inside a white-blue shell;
- blur or material on every nested container;
- unrelated cyan, violet, and orange primary buttons competing on one screen;
- decorative starfields behind dense text;
- inconsistent icon intrinsic sizes and baselines;
- low-contrast disabled controls that look broken;
- different spacing/radius systems in settings, floating panels, and toolbars;
- visual changes that merge previously independent product workflows.
