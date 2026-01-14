# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/feriksen-personal/dbt-conceptual/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/feriksen-personal/dbt-conceptual/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/feriksen-personal/dbt-conceptual/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/feriksen-personal/dbt-conceptual/releases/tag/v0.1.0
