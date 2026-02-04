# Frontend Style Notes V1.5

## Design Philosophy

High-contrast editorial interface with retro-modern aesthetic. Inspired by old banking UIs, technical manuals, and zines. The visual language is print/editorial, slightly brutalist, and extremely legible.

## Color System

### Core Neutrals
- **black**: `#0B0B0B` - Primary text and borders
- **white**: `#FFFFFF` - Card backgrounds
- **paper**: `#FAFAF7` - Main page background
- **border**: `#1F1F1F` - Border color
- **muted**: `#6B6B6B` - Secondary text

### Accent Palette (Scroll-inspired)
- **accent-yellow**: `#F4E04D` - Primary accent (top bar, CTAs)
- **accent-amber**: `#F2B705` - Emphasis/hover states
- **accent-orange**: `#E36414` - Destructive/strong CTAs

### Usage Rules

**Accent color is NOT decorative** - used only for:
- Navigation zones (top bar)
- Headers and section dividers
- Primary CTAs and active states
- Progress indicators
- Cognitive separation (nav vs content vs actions)

**Strict NOs:**
- No gradients
- No translucency
- No neumorphism
- No glassmorphism

## Typography

### Primary UI Font
- **Font**: IBM Plex Sans
- **Fallback**: Inter, system-ui
- **Weights**: 400, 500, 600, 700
- **Usage**: Body text, labels, general UI

### Headings / Labels
- **Font**: Space Grotesk
- **Weights**: 500, 600, 700
- **Letter-spacing**: -0.02em
- **Usage**: Page titles, section headers, card titles

### Monospace / Meta
- **Font**: JetBrains Mono
- **Usage**: IDs, durations, difficulty tags, debug/meta text

### Typography Scale
- **Page title**: font-heading font-bold text-4xl tracking-tight
- **Section title**: font-heading font-semibold text-lg tracking-tight
- **Card title**: font-heading font-semibold text-lg tracking-tight
- **Body text**: text-sm
- **Labels**: text-sm font-medium
- **Meta**: text-xs font-mono

## Layout Rules

### Global
- **Max width**: 1280px (max-w-7xl)
- **Centered layout**: mx-auto
- **Spacing**: 8px system (p-1, p-2, p-3, p-4, p-6)
- **Borders**: 1.5px default, 2px for emphasis
- **Border radius**: Max 6px (rounded-md)

### Top Bar
- **Height**: 64px (h-16)
- **Background**: accent-yellow
- **Text**: black
- **Border**: 2px black bottom
- **Logo**: Scroll icon (black) + title
- **User actions**: Right-aligned

### Dashboard Header
- **Large title**: Space Grotesk 700
- **Subtitle**: muted color
- **Left-aligned**
- **Accent underline**: 4px yellow bar

## Component Styling

### Cards/Panels
- **Background**: white
- **Border**: 2px solid black
- **Radius**: 6px (rounded-md)
- **Padding**: 24px (p-6)
- **Hover**: border-color accent-amber

### Lesson Cards
- **Title**: Space Grotesk 600
- **Metadata**: JetBrains Mono
- **Actions**: Right-aligned
- **Play button**: accent-orange
- **Delete**: white background, black border

### Buttons
**Primary:**
- **Background**: accent-orange
- **Text**: black
- **Border**: 2px solid black
- **Hover**: background accent-amber

**Secondary:**
- **Background**: white
- **Text**: black
- **Border**: 2px solid black
- **Hover**: background accent-yellow

### Inputs
- **Background**: white
- **Border**: 2px solid black
- **Focus**: outline-none + border accent-orange
- **Placeholder**: muted

### Navigation
- **Active**: background accent-yellow + border-left 4px black
- **Inactive**: white background
- **Hover**: background accent-yellow
- **Text always visible** (no icons-only nav)

## Motion

- **Minimal**: 120-160ms duration
- **Properties**: opacity + translateY(2px) only
- **Easing**: ease-out only
- **No complex animations**

## Branding Rules

### Scroll Icon
- **Brand anchor**: Use as empty states, loading placeholders, hero illustration
- **Color**: Black only
- **Do NOT recolor**

## Component Primitives

Use these as the only building blocks:

### Panel
```tsx
<Panel title="Section Title" className="optional-classes">
  content
</Panel>
```

### ControlButton
```tsx
<ControlButton variant="primary|secondary|destructive" className="optional">
  Button text
</ControlButton>
```

### TextInput
```tsx
<TextInput placeholder="Label text" />
```

### TopBar
```tsx
<TopBar />
```

## Do / Don't List

### Do
- Use only approved colors and fonts
- Keep borders visible and consistent
- Prioritize legibility and scannability
- Use accent colors for hierarchy only
- Build from existing primitives
- Keep motion minimal and functional

### Don't
- Use gradients, shadows, or blur effects
- Add rounded corners beyond 6px
- Use semantic colors (success, warning, etc.)
- Add complex animations or easing
- Create floating elements without containers
- Use accent colors decoratively

## New Page Checklist

Before shipping a new page:
- [ ] Uses only existing primitives
- [ ] Matches border thickness (1.5px default, 2px emphasis)
- [ ] Uses correct typography hierarchy
- [ ] Follows accent color usage rules
- [ ] Uses approved spacing only
- [ ] Has no shadows or gradients
- [ ] Uses correct font assignments
- [ ] Motion is minimal (120-160ms, ease-out)

## Extension Rule

If a component cannot be built from existing primitives, extend the system first, do not improvise. All new components must follow the same visual rules and be added to this style guide.

## Hard Constraints

- Do not change routes
- Do not rename components  
- Do not touch API calls
- Do not introduce new UI libraries
- Tailwind only

## End Result

The UI should feel:
- Faster to scan
- Impossible to confuse
- Visually opinionated
- Technically serious
- Designed, not themed
