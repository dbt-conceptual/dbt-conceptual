# dbt-conceptual Brand Assets

## Logo: Entity Seed

The logo represents a conceptual entity — the atomic building block from which data models grow.

### Design Elements

- **Outer shape**: Rounded rectangle with gradient fill
- **Header bar**: Highlighted section representing the entity name
- **Indicator dot**: Centered in header, representing active state
- **Attribute lines**: Subtle lines suggesting entity structure

### Specifications

| Element | Value |
| ------- | ----- |
| Background gradient | `#1e3a5f` → `#112235` (150°) |
| Border | 2px solid `#4a7fb3` |
| Header gradient | `#5ba3f5` → `#3d8ae0` (90°) |
| Indicator dot | White, 85% opacity |

### Sizes

| Size | Dimensions | Files | Use |
| ---- | ---------- | ----- | --- |
| Large | 56×63px | `logos/logo-large.svg`, `logos/logo-large.png` | Hero, documentation |
| Medium | 40×45px | `logos/logo-medium.svg`, `logos/logo-medium.png` | App header, banners |
| Small | 26×30px | `logos/logo-small.svg`, `logos/logo-small.png` | Favicon, compact UI |

### Wordmark

- **Font**: JetBrains Mono, 500 weight
- **Text**: `dbt-conceptual`
- **Color**: `#1a1a2e` (light bg), `#ffffff` (dark bg)

### Tagline

**"Continuous conceptual alignment for dbt projects"**

- **Font**: Inter or Source Sans 3, 400 weight
- **Color**: `#666666`

## Social Banner

The GitHub social preview banner is 1280×640px and includes:

- Logo (scaled 4x)
- Wordmark and tagline
- Example concept graph visualization
- Grid pattern background

**Files**:
- `social-banner.svg` - Vector version
- `social-banner.png` - PNG version for GitHub (48KB)

## Usage

### GitHub Repository

Upload `social-banner.png` as the repository's social preview image:
1. Go to repository Settings
2. General → Social preview
3. Upload `social-banner.png`

### Favicon

Multiple formats available:

- `favicon.svg` - Modern browsers (vector)
- `favicon-32x32.png` - Standard favicon size
- `favicon-16x16.png` - Small favicon size

For `favicon.ico`, use online converter with `favicon-32x32.png` and `favicon-16x16.png`.

### Documentation

Use `logos/logo-medium.svg` in documentation headers and `logos/logo-large.svg` for hero sections.

## Color Palette

### Brand

| Token | Hex | Usage |
| ----- | --- | ----- |
| Primary | `#4a9eff` | Interactive elements, selection |
| Primary Light | `#e8f4ff` | Hover, light backgrounds |
| Primary Dark | `#3a8eef` | Active states |

### Logo

| Token | Hex | Usage |
| ----- | --- | ----- |
| Background Start | `#1e3a5f` | Logo gradient start |
| Background End | `#112235` | Logo gradient end |
| Border | `#4a7fb3` | Logo border |
| Header Start | `#5ba3f5` | Header gradient start |
| Header End | `#3d8ae0` | Header gradient end |

### UI

| Token | Hex | Usage |
| ----- | --- | ----- |
| Text Primary | `#1a1a2e` | Main text |
| Text Secondary | `#666666` | Secondary text |
| Text Muted | `#888888` | Muted text, labels |
| Background | `#f5f6f8` | Page background |
| Surface | `#ffffff` | Cards, panels |
| Border | `#e5e7eb` | Standard borders |

## License

All brand assets are part of dbt-conceptual and are licensed under the MIT License.
