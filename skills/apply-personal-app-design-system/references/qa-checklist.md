# Visual And Interaction QA Checklist

## Evidence

- Capture the actual built interface, not only a mockup or source code.
- Save and inspect each accepted screenshot before using it as evidence.
- Name any surface that could not be opened or captured.
- Separate source/build validation from live visual validation.

## Required Desktop Sizes

- Check a wide desktop state around `1440×1024`.
- Check a compact desktop state around `1000×720`.
- Check the product's documented minimum window size.
- Confirm navigation, page actions, forms, and long Chinese labels do not clip.

## Light And Dark

- Verify both modes on the same representative content.
- Confirm dark mode is navy rather than flat black.
- Confirm surfaces remain distinguishable without excessive borders.
- Confirm ambient glows do not reduce text contrast.
- Confirm native window chrome and embedded web/native surfaces do not clash.

## Hierarchy And Consistency

- One primary action is visually dominant per local task.
- Active navigation, selected rows, primary buttons, and focus rings use the same accent family.
- Cards, controls, and windows use the documented radius scale.
- Toolbars use equal control heights and aligned icon/text baselines.
- Fields and buttons do not fall back to unrelated gray system styling.
- Loading, empty, success, warning, error, and disabled states remain recognizable.

## Accessibility

- Verify primary and secondary text contrast against the actual rendered background.
- Confirm status is not communicated through color alone.
- Check keyboard order, visible focus, Escape/Return behavior, and global shortcut conflicts.
- Give icon-only buttons an accessible name and tooltip where appropriate.
- Keep pointer targets at least `36×36` on desktop unless a dense native toolbar has a documented exception.
- Test increased text size or zoom for clipping and reflow.
- Respect Reduce Motion and Increase Contrast when the platform exposes them.
- Do not claim full accessibility compliance from screenshots alone; test semantics and keyboard behavior.

## Product Flow Preservation

- Re-run the core flows touched by the visual work.
- Confirm styling did not merge, reroute, or silently alter independent operations.
- Verify copy, cancel, save, undo, pin, selection, and destructive actions retain their previous behavior.
- Run the repository's existing build, test, lint, and regression commands.

## Handoff Evidence

Provide:

- screenshots for the representative light, dark, wide, and compact states;
- the semantic token source;
- the shared component source;
- checks run and their results;
- remaining live QA gaps;
- one next screen or component to inspect.
