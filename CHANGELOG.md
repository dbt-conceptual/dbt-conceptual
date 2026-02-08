# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.5] - 2026-01-21

### Fixed

- Include correct index.html in package (0.5.4 had placeholder index.html)

## [0.5.4] - 2026-01-21

### Fixed

- Actually include rebuilt frontend assets in PyPI package (0.5.2/0.5.3 had stale assets)

## [0.5.3] - 2026-01-21

### Fixed

- Include rebuilt frontend in package (fixes missing integrity error UI in 0.5.2)

## [0.5.2] - 2026-01-21

### Fixed

- Canvas shows blocked state with error message when conceptual.yml has integrity issues (relationships referencing undefined concepts)
- Prevents React Flow crash on initial load when edges reference missing nodes
- Added `hasIntegrityErrors` flag to API response for frontend to detect invalid state

## [0.5.1] - 2026-01-21

### Added

- Warning badge on stub concepts in canvas UI
- "What's Persisted vs Transient" section in validation guide
- Draft and Stub states to concept states documentation

### Changed

- Updated README taglines and added whiteboard photo quote
- Concept states screenshot now shows 6 states in 3x2 grid layout

## [0.5.0] - 2026-01-21

### Added

- Validation messages panel with collapsible bar and expanded view
- Error/warning/info filter toggles for validation messages
- Ghost concept support for undefined relationship targets
- Click-to-navigate from validation messages to related elements
- Visual indicators for validation states on concept nodes and relationship edges
- Status indicators in property panel for ghost concepts and validation issues
- Sync button to trigger validation and refresh state
- Unit tests for validate_and_sync method in parser.py

### Changed

- React Flow no longer crashes when edges reference non-existent nodes
- Relationships referencing undefined concepts now show as invalid with red dashed lines
- Property panel now shows ghost concept editing with "Save as Concept" button

### Fixed

- Blank page issue when relationships referenced non-existent concepts
- Removed broken mermaid/excalidraw export tests that referenced non-existent functions

## [0.4.0] - 2026-01-19

### Added

- Complete React + TypeScript UI rebuild using React Flow for interactive canvas
- Zustand state management for application state
- 12 new React components for comprehensive UI experience
- Design tokens CSS system (977 lines) for consistent styling
- Property panel with tabs for editing concepts and viewing model associations
- Settings modal for managing domains and layer path configuration
- Comprehensive test suite for Flask server (13 tests)
- Static file serving from Flask for production deployment

### Changed

- Redesigned UI architecture from basic React to full React Flow canvas
- Improved Flask server to serve production React build
- Enhanced test coverage with server-specific tests
- Updated all CI workflows to include Flask dependencies

### Fixed

- Flask server now properly serves frontend build with fallback support
- Coverage reporting integrated with Codecov app

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
- Interactive web UI with `dbc serve` command
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

[Unreleased]: https://github.com/dbt-conceptual/dbt-conceptual/compare/v0.5.1...HEAD
[0.5.1]: https://github.com/dbt-conceptual/dbt-conceptual/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/dbt-conceptual/dbt-conceptual/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/dbt-conceptual/dbt-conceptual/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/dbt-conceptual/dbt-conceptual/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/dbt-conceptual/dbt-conceptual/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/dbt-conceptual/dbt-conceptual/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/dbt-conceptual/dbt-conceptual/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dbt-conceptual/dbt-conceptual/releases/tag/v0.1.0
