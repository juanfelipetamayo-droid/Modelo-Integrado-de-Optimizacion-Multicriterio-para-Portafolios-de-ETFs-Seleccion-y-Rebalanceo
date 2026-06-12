# DESIGN

## Design register
Product UI. Design serves the research task.

## Theme scene
A researcher alternates between a bright desk during analysis and a dim office during long pilot runs, so the dashboard ships with intentional Light and Dark modes.

## Visual direction
Apple-inspired local software: restrained surfaces, soft neutral layers, precise typography, calm density, and clear command affordances. Light mode should feel like a polished macOS analytics panel. Dark mode should feel focused, not theatrical.

## Color strategy
Restrained. Use tinted OKLCH neutrals with a blue accent only for primary actions, current state, and status emphasis.

## Typography
Use native system fonts: `-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`. Keep product labels compact, data readable, and prose capped around 65 to 75 characters.

## Layout
- Sidebar navigation plus main workspace.
- Overview first: run readiness, core metrics, strategy comparison, funnel.
- Workflows use progressive disclosure with command previews before execution.
- Results and artifacts are dense but readable.

## Interaction principles
- Never run local commands without explicit confirmation.
- Show the exact command before execution.
- Prefer inline status, empty, and error states over modals.
- Preserve keyboard and touch target usability.
