# FRONTEND VISUAL CONSISTENCY CHECKLIST (MANDATORY)

## Global
- [ ] No shadows anywhere
- [ ] No gradients
- [ ] No pastel or semantic colors
- [ ] Only approved color tokens used
- [ ] Borders visible and consistent (2px default)

## Typography
- [ ] IBM Plex Sans only
- [ ] No italics
- [ ] Labels small and restrained (text-xs font-medium uppercase tracking-wide)
- [ ] Headings bold and blunt (font-bold)
- [ ] Numbers visually emphasized

## Layout
- [ ] Every section is boxed
- [ ] No floating elements without containers
- [ ] Spacing uses approved scale only (p-1, p-2, p-3, p-4, p-6)
- [ ] Density prioritized over airiness

## Components
- [ ] Panels use borders, not elevation
- [ ] Buttons invert on hover
- [ ] Inputs always boxed
- [ ] Tables are grid-like and dense
- [ ] Navigation uses inversion or rules for active state

## Interaction
- [ ] No easing-heavy animations
- [ ] No hover glow
- [ ] State changes are instant and mechanical
- [ ] transition-none used for interactive elements

## SaaS Smell Test

If any of the following are true, stop and fix:
- [ ] Looks "friendly"
- [ ] Looks like a startup dashboard
- [ ] Uses pills, chips, or rounded badges
- [ ] Uses color where layout could work

## New Page Checklist

Before shipping a new page:
- [ ] Uses only existing primitives
- [ ] Matches border thickness (2px)
- [ ] Matches typography scale
- [ ] Passes the SaaS smell test

## Rule

If a component cannot be built from existing primitives, extend the system first, do not improvise.
