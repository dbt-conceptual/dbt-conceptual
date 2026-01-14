# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release
- CLI commands: `init`, `sync`, `status`, `validate`, `enrich`, `serve`, `export`
- Conceptual model definition in `model.yml`
- dbt model tagging via `meta.concept` and `meta.realizes`
- Visual editor with Excalidraw-style aesthetic
- Export formats: Excalidraw, Mermaid, Coverage Report, Bus Matrix
- CI validation support
- Bottom-up adoption via `--create-stubs`
- Configurable silver/gold paths

## [0.1.0] - YYYY-MM-DD

### Added
- Initial public release

---

[Unreleased]: https://github.com/YOUR_USERNAME/dbt-conceptual/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YOUR_USERNAME/dbt-conceptual/releases/tag/v0.1.0
