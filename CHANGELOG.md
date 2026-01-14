# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-01-14

### Added
- Interactive graph editor with redesigned box-based layout
- Orthogonal (Visio-style) routing for relationship lines with crow's foot notation
- Right-click context menus for creating concepts, relationships, and domains
- Model management panel with checkboxes to assign models to concepts
- Drag-and-drop model assignment from panel to concept boxes
- Domain and owner dropdowns with auto-completion
- Markdown description fields for concepts and relationships
- Status indicator circles in top-right corner of concept boxes
- Authentic Databricks layered brick logo for medallion architecture badges
- Bronze layer support with auto-discovery from dbt sources
- All three medallion badges (bronze, silver, gold) always visible with counts
- Persistent layout saving and loading via REST API

### Changed
- Replaced force-directed graph with fixed box layout for better control
- Moved medallion badges inside concept boxes
- Replaced medal emojis with official Databricks SVG logo
- Status now shown as color-coded circles instead of text badges
- Improved visual hierarchy and information density

### Fixed
- Model count duplicates in assignment panel
- Layout persistence across browser sessions

## [0.2.2] - 2026-01-14

### Fixed
- Static file serving path - assets now load correctly in browser

## [0.2.1] - 2026-01-14

### Added
- PNG export format for static diagram images
- Built frontend static files now included in distribution
- Frontend build script (build-frontend.sh)

### Fixed
- Interactive UI now works out of the box without building frontend
- Static files properly included in package distribution

## [0.2.0] - 2026-01-14

### Added
- Interactive web UI with `dbt-conceptual serve` command
- Visual graph editor with drag-and-drop D3.js force-directed layout
- Real-time editing and saving to `conceptual.yml`
- Integrated coverage report view
- Integrated bus matrix view
- Flask backend with REST API endpoints
- React + TypeScript + Vite frontend
- Export command for Excalidraw diagrams
- Export command for coverage HTML reports
- Export command for bus matrix HTML reports
- Comprehensive PR workflow with test visualization and coverage reporting
- Feature branch CI workflow
- Documentation for interactive UI features

### Changed
- Updated README with interactive UI documentation
- Quick Start now uses jaffle-shop as demo example

## [0.1.0] - 2026-01-14

### Added
- Initial public release
- CLI commands: `init`, `status`, `validate`
- Conceptual model definition in `conceptual.yml`
- dbt model tagging via `meta.concept` and `meta.realizes`
- Relationship groups for multi-table facts
- Validation with error/warning/info levels
- 93% test coverage
- CI/CD with GitHub Actions

---

[Unreleased]: https://github.com/feriksen-personal/dbt-conceptual/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/feriksen-personal/dbt-conceptual/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/feriksen-personal/dbt-conceptual/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/feriksen-personal/dbt-conceptual/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/feriksen-personal/dbt-conceptual/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/feriksen-personal/dbt-conceptual/releases/tag/v0.1.0
