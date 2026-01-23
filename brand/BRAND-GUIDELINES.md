# dbt-conceptual Brand Guidelines

## Overview

dbt-conceptual bridges conceptual data models to dbt. The brand identity reflects this connection through the infinity mark — representing the continuous cycle between conceptual design and physical implementation.

---

## Logo

### The Mark

The logo consists of two elements:
1. **Infinity loop** — Two interlocking loops representing the connection between conceptual (orange) and physical (gray)
2. **Flow bar** — A horizontal line beneath symbolizing forward momentum and data flow

### Logo Versions

| Version | Use Case |
|---------|----------|
| **Standalone mark** | Headers, UI, larger applications |
| **Contained mark** | Favicons, app icons, small sizes |
| **Full lockup** | Primary branding, documentation headers |

### Clear Space

Maintain clear space around the logo equal to the height of the infinity loop (excluding the bar).

### Minimum Size

- Standalone mark: 24px minimum
- Contained mark: 16px minimum (optimized for small sizes)
- Full lockup: 120px width minimum

---

## Color Palette

### Primary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Orange** | `#e67e22` | 230, 126, 34 | Primary brand color, "conceptual" in wordmark, left loop |
| **Orange Dark** | `#d35400` | 211, 84, 0 | Gradient end, hover states |
| **Gray** | `#888888` | 136, 136, 136 | "dbt" in wordmark, right loop, secondary elements |

### Dark Mode Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Orange Light** | `#f5a854` | 245, 168, 84 | Primary brand color in dark mode |
| **Gray Muted** | `#777777` | 119, 119, 119 | "dbt" in wordmark (dark mode) |
| **Gray Dark** | `#555555` | 85, 85, 85 | Dash in wordmark (dark mode) |

### UI Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Background Light** | `#fafaf9` | Light mode backgrounds |
| **Background Dark** | `#1a1a1a` | Dark mode backgrounds |
| **Text Primary** | `#333333` | Primary text (light mode) |
| **Text Secondary** | `#888888` | Secondary text |
| **Text Muted** | `#cccccc` | Muted text, separators |
| **Border** | `#e8e6e3` | Borders, dividers |

### Gradient

Primary gradient for contained mark and accent elements:
```css
background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
```

Dark mode gradient:
```css
background: linear-gradient(135deg, #f5a854 0%, #e67e22 100%);
```

---

## Typography

### Primary Font

**Inter** — Used for all text

- Available from Google Fonts: `https://fonts.google.com/specimen/Inter`
- Fallback: `-apple-system, BlinkMacSystemFont, sans-serif`

### Wordmark Specifications

```css
font-family: 'Inter', -apple-system, sans-serif;
font-weight: 600;
letter-spacing: -0.02em;
```

### Text Colors in Wordmark

**Light Mode:**
- "dbt": `#888888`
- "-": `#cccccc`
- "conceptual": `#e67e22`

**Dark Mode:**
- "dbt": `#777777`
- "-": `#555555`
- "conceptual": `#f5a854`

---

## Logo Construction

### Standalone Mark (viewBox: 0 0 80 80)

```svg
<!-- Left loop (conceptual) -->
<path d="M12 32 C12 16 24 12 40 32 C24 52 12 48 12 32" 
      stroke="#e67e22" stroke-width="6" fill="none" stroke-linecap="round"/>

<!-- Right loop (physical) -->
<path d="M40 32 C56 52 68 48 68 32 C68 16 56 12 40 32" 
      stroke="#888888" stroke-width="6" fill="none" stroke-linecap="round"/>

<!-- Flow bar -->
<path d="M12 58 L68 58" 
      stroke="#e67e22" stroke-width="5" stroke-linecap="round"/>
```

### Contained Mark (viewBox: 0 0 80 80)

```svg
<!-- Container -->
<rect width="80" height="80" rx="16" fill="url(#gradient)"/>

<!-- Left loop -->
<path d="M14 30 C14 18 24 14 40 30 C24 46 14 42 14 30" 
      stroke="white" stroke-width="5" fill="none" stroke-linecap="round"/>

<!-- Right loop (faded) -->
<path d="M40 30 C56 46 66 42 66 30 C66 18 56 14 40 30" 
      stroke="white" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.6"/>

<!-- Flow bar -->
<path d="M14 54 L66 54" 
      stroke="white" stroke-width="4" stroke-linecap="round"/>
```

---

## Usage Guidelines

### Do

- ✓ Use the contained mark for favicons and small applications
- ✓ Use the standalone mark for headers and larger contexts
- ✓ Maintain proper clear space around the logo
- ✓ Use approved color combinations
- ✓ Apply optical alignment correction for standalone mark + text lockup

### Don't

- ✗ Rotate or skew the logo
- ✗ Change the proportions of the mark
- ✗ Use unapproved colors
- ✗ Add effects like drop shadows or glows
- ✗ Place the logo on busy backgrounds without sufficient contrast

---

## File Formats

### Provided Assets

| File | Format | Purpose |
|------|--------|---------|
| `favicon.svg` | SVG | Browser favicon |
| `mark-light.svg` | SVG | Standalone mark, light mode |
| `mark-dark.svg` | SVG | Standalone mark, dark mode |
| `mark-contained-light.svg` | SVG | Contained mark, light mode |
| `mark-contained-dark.svg` | SVG | Contained mark, dark mode |
| `logo-full-light.svg` | SVG | Full lockup, light mode |
| `logo-full-dark.svg` | SVG | Full lockup, dark mode |
| `github-avatar.svg` | SVG | GitHub organization avatar |
| `github-banner-light.svg` | SVG | GitHub repo banner, light |
| `github-banner-dark.svg` | SVG | GitHub repo banner, dark |
| `og-image.svg` | SVG | Social sharing / Open Graph |

### Converting to Other Formats

SVGs can be converted to PNG/ICO as needed:
- Favicon: Export at 16x16, 32x32, 48x48
- App icons: Export at 512x512
- Social: Export at native resolution (1280x640 for banner, 1200x630 for OG)

---

## Contact

For brand questions or asset requests, open an issue in the dbt-conceptual repository.
