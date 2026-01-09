# Themes Feature

Theme customization and management module for visualization styling.

## Structure

```
themes/
└── (Currently a placeholder page)
```

## Current Status

The themes page (`app/[locale]/themes/page.tsx`) is currently a placeholder showing "Under Construction".

## Current Theme System

The application uses:
- **next-themes** for dark/light mode switching
- **Tailwind CSS** with CSS variables for theming
- **Design tokens** defined in `src/shared/design-system/tokens.ts`

## Planned Features

- [ ] Custom theme creation
- [ ] Color palette customization
- [ ] Chart color schemes
- [ ] Font selection
- [ ] Theme preview
- [ ] Theme export/import
- [ ] Preset themes library
- [ ] Apply themes to generated visualizations

## Future API

```typescript
// Example future hooks
const { themes, activeTheme, setActiveTheme, createTheme } = useThemes();

const { colors, updateColors } = useThemeColors();
```

## Design Tokens

Current design tokens are defined in `src/shared/design-system/tokens.ts`:

- Colors (primary, secondary, destructive, etc.)
- Typography (font sizes, line heights)
- Spacing (xs, sm, md, lg, xl, 2xl)
- Border radius
- Shadows
