# Platform Mapping

## SwiftUI

Create a small semantic token namespace and reusable modifiers/styles. Keep raw values in one design file.

Map roles as follows:

- window background → `LinearGradient` plus one low-opacity `RadialGradient`;
- surface → semantic `Color` plus `RoundedRectangle` border and restrained shadow;
- primary/secondary action → shared `ButtonStyle`;
- light/dark values → dynamic `NSColor` bridged into `Color`;
- continuous corners → `.continuous` rounded rectangles;
- reduced motion → inspect `accessibilityReduceMotion` before transforms.

Do not use `Form(.grouped)` or default gray `List` containers as the final visual shell. Build explicit cards and rows when the default platform background conflicts with the system.

## AppKit

Map the same semantics rather than copying SwiftUI internals:

- panel surface → layer-backed `NSView` with dynamic `NSColor` background and border;
- toolbar control → custom `NSButton` appearance while preserving AppKit targeting, keyboard, and accessibility behavior;
- symbols → SF Symbols with one point-size/weight configuration and a fixed `18×18` template canvas;
- selection border → dark outer stroke plus bright blue inner stroke;
- appearance changes → refresh colors in `viewDidChangeEffectiveAppearance()`.

Avoid mixing default gray AppKit bezels with custom white-blue controls in the same toolbar.

## React, Tauri, And CSS

Define semantic CSS variables at `:root` and override the same names under `[data-theme="dark"]`.

```css
:root {
  color-scheme: light;
  --app-bg-start: 246 251 255;
  --app-bg-end: 230 242 255;
  --surface: 255 255 255;
  --surface-control: 246 250 255;
  --text: 23 32 51;
  --muted: 89 105 125;
  --border: 179 209 245;
  --accent: 64 125 245;
  --accent-strong: 33 97 219;
}

:root[data-theme="dark"] {
  color-scheme: dark;
  --app-bg-start: 6 17 31;
  --app-bg-end: 11 31 56;
  --surface: 14 31 54;
  --surface-control: 26 56 94;
  --text: 232 239 255;
  --muted: 145 161 194;
  --border: 102 166 255;
  --accent: 102 166 255;
  --accent-strong: 79 145 250;
}
```

Use shared component classes or primitives for:

- app shell and sidebar;
- page header;
- surface/card;
- primary, secondary, icon, and destructive button;
- field, select, and segmented control;
- badge/status;
- dialog and toast.

Use Lucide icons consistently in React surfaces. Set a shared size and stroke width rather than styling each icon independently.

## Tailwind

Expose semantic CSS variables through Tailwind instead of hard-coded palette names:

```ts
colors: {
  background: "rgb(var(--app-bg-start) / <alpha-value>)",
  surface: "rgb(var(--surface) / <alpha-value>)",
  text: "rgb(var(--text) / <alpha-value>)",
  muted: "rgb(var(--muted) / <alpha-value>)",
  border: "rgb(var(--border) / <alpha-value>)",
  accent: "rgb(var(--accent) / <alpha-value>)"
}
```

Keep spacing, radius, shadow, and motion tokens centralized in the theme package when multiple apps share them.

## Other Desktop Frameworks

For Electron, Flutter, HarmonyOS, or another desktop framework:

1. Preserve semantic names and token values.
2. Use the platform's native font and accessibility APIs.
3. Select one consistent icon family.
4. Rebuild component states in native controls rather than importing web-only behavior blindly.
5. Verify the platform's dark mode, scaling, keyboard navigation, and window chrome separately.
