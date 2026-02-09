"""Flask web server for conceptual model UI.

v1.0: Simplified API with flat models[], no realized_by.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml
from flask import Flask, Response, jsonify, request, send_from_directory

from dbt_conceptual.config import Config
from dbt_conceptual.exporter.bus_matrix import export_bus_matrix
from dbt_conceptual.exporter.coverage import export_coverage
from dbt_conceptual.parser import StateBuilder
from dbt_conceptual.scanner import DbtProjectScanner
from dbt_conceptual.state import ProjectState

logger = logging.getLogger(__name__)

# Module-level cache for ProjectState
_state_cache: ProjectState | None = None


def _invalidate_cache() -> None:
    """Invalidate the cached state."""
    global _state_cache
    _state_cache = None


def _serialize_state(state: ProjectState) -> dict[str, Any]:
    """Serialize ProjectState to a JSON-compatible dictionary.

    Converts domain, concept, and relationship dataclasses into plain dicts
    suitable for JSON responses. Status fields are derived at serialization time.

    Args:
        state: The project state to serialize.

    Returns:
        Dictionary with 'domains', 'concepts', and 'relationships' keys.
    """
    return {
        "domains": {
            domain_id: {
                "name": domain.name,
                "display_name": domain.display_name,
                "color": domain.color,
            }
            for domain_id, domain in state.domains.items()
        },
        "concepts": {
            concept_id: {
                "name": concept.name,
                "definition": concept.definition,
                "domain": concept.domain,
                "owner": concept.owner,
                "status": concept.status,  # Derived at runtime
                "color": concept.color,
                "models": concept.models,  # Flat list
                # Validation fields
                "isGhost": concept.is_ghost,
                "validationStatus": concept.validation_status.value,
                "validationMessages": concept.validation_messages,
            }
            for concept_id, concept in state.concepts.items()
        },
        "relationships": {
            rel_id: {
                "name": rel.name,  # Derived
                "verb": rel.verb,
                "from_concept": rel.from_concept,
                "to_concept": rel.to_concept,
                "cardinality": rel.cardinality,
                "owner": rel.owner,
                "definition": rel.definition,
                "status": rel.get_status(state.concepts),  # Derived
                # Validation fields
                "validationStatus": rel.validation_status.value,
                "validationMessages": rel.validation_messages,
            }
            for rel_id, rel in state.relationships.items()
        },
    }


def _atomic_write(file_path: Path, content: str) -> None:
    """Atomically write content to a file using temp file + rename.

    Args:
        file_path: Target file path to write to.
        content: Content to write.

    Raises:
        OSError: If the file cannot be written due to permission or I/O errors.
    """
    # Create temp file in same directory for atomic rename
    temp_fd, temp_path_str = tempfile.mkstemp(
        dir=file_path.parent, prefix=f".{file_path.name}.", suffix=".tmp"
    )
    temp_path = Path(temp_path_str)

    try:
        # Write content to temp file
        os.write(temp_fd, content.encode("utf-8"))
        os.close(temp_fd)

        # Atomic rename
        os.rename(temp_path, file_path)
    except Exception:
        # Clean up temp file on error
        try:
            os.close(temp_fd)
        except OSError:
            pass
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise


def _read_conceptual_yml(conceptual_file: Path) -> dict[str, Any]:
    """Read and parse the conceptual.yml file.

    Args:
        conceptual_file: Path to conceptual.yml.

    Returns:
        Parsed YAML data as a dictionary, or empty dict if file is empty.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
        OSError: If the file cannot be read due to permission or I/O errors.
    """
    with open(conceptual_file) as f:
        return yaml.safe_load(f) or {}


def _write_conceptual_yml(conceptual_file: Path, data: dict[str, Any]) -> None:
    """Write data to the conceptual.yml file atomically.

    Args:
        conceptual_file: Path to conceptual.yml.
        data: Dictionary to serialize as YAML.

    Raises:
        OSError: If the file cannot be written due to permission or I/O errors.
        yaml.YAMLError: If the data cannot be serialized.
    """
    from io import StringIO

    output = StringIO()
    yaml.dump(data, output, sort_keys=False, default_flow_style=False)
    _atomic_write(conceptual_file, output.getvalue())


def create_app(project_dir: Path, demo_mode: bool = False) -> Flask:
    """Create and configure Flask app.

    Args:
        project_dir: Path to dbt project directory
        demo_mode: Whether running in demo mode (default: False)

    Returns:
        Configured Flask app
    """
    # Look for frontend build in multiple locations
    # 1. Development: frontend/dist relative to package
    # 2. Installed: package data
    static_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if not static_dir.exists():
        static_dir = Path(__file__).parent / "static"

    app = Flask(__name__, static_folder=str(static_dir), static_url_path="")
    app.config["PROJECT_DIR"] = project_dir
    app.config["DEMO_MODE"] = demo_mode

    # Enable CORS in debug mode (for Vite dev server)
    @app.after_request
    def after_request(response: Response) -> Response:
        if app.debug:
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response

    # Load config
    config = Config.load(project_dir=project_dir)

    @app.route("/")
    def index() -> str | Response:
        """Serve the main UI page."""
        if app.static_folder and (Path(app.static_folder) / "index.html").exists():
            return send_from_directory(app.static_folder, "index.html")
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>dbt-conceptual UI</title>
            <style>
                body { font-family: system-ui; padding: 2rem; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>dbt-conceptual UI</h1>
            <p>Frontend build not found. Run: <code>cd frontend && npm run build</code></p>
            <p>API endpoints available:</p>
            <ul>
                <li><a href="/api/state">GET /api/state</a> - Get current state</li>
                <li>POST /api/state - Save state</li>
                <li><a href="/api/coverage">GET /api/coverage</a> - Coverage report HTML</li>
                <li><a href="/api/bus-matrix">GET /api/bus-matrix</a> - Bus matrix HTML</li>
            </ul>
        </body>
        </html>
        """

    @app.route("/api/state", methods=["GET"])
    def get_state() -> Response | tuple[Response, int]:
        """Get current conceptual model state as JSON."""
        try:
            global _state_cache
            if _state_cache is None:
                builder = StateBuilder(config)
                _state_cache = builder.build()
            state = _state_cache

            # Check for integrity issues (relationships referencing missing concepts)
            missing_refs = []
            for _rel_id, rel in state.relationships.items():
                if rel.from_concept not in state.concepts:
                    missing_refs.append(rel.from_concept)
                if rel.to_concept not in state.concepts:
                    missing_refs.append(rel.to_concept)
            has_integrity_errors = len(missing_refs) > 0

            # Load positions from conceptual_layout.json
            layout_file = config.layout_file
            positions: dict[str, Any] = {}
            if layout_file.exists():
                with open(layout_file) as f:
                    layout_data = json.load(f) or {}
                    positions = layout_data.get("positions", {})

            # Convert state to JSON-serializable format (v1.0 simplified)
            response = _serialize_state(state)
            response["positions"] = positions  # React Flow node positions
            response["hasIntegrityErrors"] = has_integrity_errors

            return jsonify(response)
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            logger.error("Failed to parse project files: %s", e)
            return jsonify({"error": f"Parse error: {e}"}), 500
        except (FileNotFoundError, OSError) as e:
            logger.error("File I/O error reading state: %s", e)
            return jsonify({"error": f"File error: {e}"}), 500

    @app.route("/api/state", methods=["POST"])
    def save_state() -> Response | tuple[Response, int]:
        """Save conceptual model state to conceptual.yml."""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Find conceptual.yml file
            conceptual_file = config.conceptual_file
            if not conceptual_file.exists():
                return jsonify({"error": "conceptual.yml not found"}), 404

            # Read existing file to preserve config section
            existing_data = _read_conceptual_yml(conceptual_file)

            # Start with config section preserved
            yaml_data: dict[str, Any] = {}
            if "config" in existing_data:
                yaml_data["config"] = existing_data["config"]

            # Domains
            if data.get("domains"):
                yaml_data["domains"] = {
                    domain_id: {
                        k: v
                        for k, v in domain.items()
                        if v is not None and k not in ("display_name",)
                    }
                    for domain_id, domain in data["domains"].items()
                }

            # Concepts
            skipped_ghosts: list[str] = []
            if data.get("concepts"):
                yaml_data["concepts"] = {}
                for concept_id, concept in data["concepts"].items():
                    # Skip ghost concepts that haven't been properly defined
                    if concept.get("isGhost") and not concept.get("domain"):
                        skipped_ghosts.append(concept_id)
                        logger.warning(
                            "Skipping ghost concept without domain during save: %s",
                            concept_id,
                        )
                        continue
                    # Only save fields that belong in YAML (not derived fields)
                    concept_dict = {
                        k: v
                        for k, v in concept.items()
                        if v is not None
                        and k
                        not in (
                            "status",  # Derived
                            "models",  # Derived from meta.concept
                            "isGhost",  # Validation field
                            "validationStatus",  # Validation field
                            "validationMessages",  # Validation field
                        )
                    }
                    yaml_data["concepts"][concept_id] = concept_dict

            # Relationships
            if data.get("relationships"):
                yaml_data["relationships"] = []
                for rel in data["relationships"].values():
                    rel_dict: dict[str, Any] = {}
                    for k, v in rel.items():
                        if v is None:
                            continue
                        # Skip derived and validation fields
                        if k in (
                            "name",
                            "status",
                            "validationStatus",
                            "validationMessages",
                        ):
                            continue
                        # Map API field names to YAML field names
                        if k == "from_concept":
                            rel_dict["from"] = v
                        elif k == "to_concept":
                            rel_dict["to"] = v
                        else:
                            rel_dict[k] = v
                    yaml_data["relationships"].append(rel_dict)

            # Write to file
            _write_conceptual_yml(conceptual_file, yaml_data)

            # Invalidate cache
            _invalidate_cache()

            response_data = {
                "success": True,
                "message": "Saved to conceptual.yml",
                "skipped_ghosts": skipped_ghosts,
            }
            return jsonify(response_data)

        except (yaml.YAMLError, ValueError, KeyError) as e:
            logger.error("Data error saving state: %s", e)
            return jsonify({"error": f"Data error: {e}"}), 500
        except (FileNotFoundError, OSError) as e:
            logger.error("File I/O error saving state: %s", e)
            return jsonify({"error": f"File error: {e}"}), 500

    @app.route("/api/coverage", methods=["GET"])
    def get_coverage() -> Response | tuple[Response, int]:
        """Get coverage report as HTML."""
        try:
            from io import StringIO

            builder = StateBuilder(config)
            state = builder.build()

            output = StringIO()
            export_coverage(state, output)

            return output.getvalue(), 200, {"Content-Type": "text/html"}  # type: ignore[return-value]
        except (yaml.YAMLError, FileNotFoundError, OSError) as e:
            logger.error("Error generating coverage report: %s", e)
            return jsonify({"error": f"Coverage report error: {e}"}), 500

    @app.route("/api/bus-matrix", methods=["GET"])
    def get_bus_matrix() -> Response | tuple[Response, int]:
        """Get bus matrix as HTML."""
        try:
            from io import StringIO

            builder = StateBuilder(config)
            state = builder.build()

            output = StringIO()
            export_bus_matrix(state, output)

            return output.getvalue(), 200, {"Content-Type": "text/html"}  # type: ignore[return-value]
        except (yaml.YAMLError, FileNotFoundError, OSError) as e:
            logger.error("Error generating bus matrix: %s", e)
            return jsonify({"error": f"Bus matrix error: {e}"}), 500

    @app.route("/api/layout", methods=["GET"])
    def get_layout() -> Response | tuple[Response, int]:
        """Get layout positions from conceptual_layout.json."""
        try:
            layout_file = config.layout_file
            if not layout_file.exists():
                return jsonify({"positions": {}})

            with open(layout_file) as f:
                layout_data = json.load(f) or {}

            return jsonify(layout_data.get("positions", {}))
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in layout file: %s", e)
            return jsonify({"error": f"Invalid layout JSON: {e}"}), 500
        except (FileNotFoundError, OSError) as e:
            logger.error("File I/O error reading layout: %s", e)
            return jsonify({"error": f"File error: {e}"}), 500

    @app.route("/api/layout", methods=["POST"])
    def save_layout() -> Response | tuple[Response, int]:
        """Save layout positions to conceptual_layout.json."""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400

            layout_file = config.layout_file

            # Prepare layout data
            layout_data = {"version": 1, "positions": data.get("positions", {})}

            # Write to file atomically
            _atomic_write(layout_file, json.dumps(layout_data, indent=2))

            return jsonify({"success": True, "message": "Layout saved"})
        except (ValueError, TypeError) as e:
            logger.error("Invalid data for layout save: %s", e)
            return jsonify({"error": f"Invalid layout data: {e}"}), 500
        except OSError as e:
            logger.error("File I/O error saving layout: %s", e)
            return jsonify({"error": f"File error: {e}"}), 500

    @app.route("/api/models", methods=["GET"])
    def get_models() -> Response | tuple[Response, int]:
        """Get available dbt models from gold layer."""
        try:
            scanner = DbtProjectScanner(config)
            models = scanner.scan()
            return jsonify(models)
        except (yaml.YAMLError, FileNotFoundError, OSError) as e:
            logger.error("Error scanning models: %s", e)
            return jsonify({"error": f"Model scan error: {e}"}), 500

    @app.route("/api/sync", methods=["POST"])
    def sync_from_dbt() -> Response | tuple[Response, int]:
        """Trigger sync from dbt project.

        Scans dbt models for meta.concept tags,
        creates ghost concepts for undefined references,
        runs validation, and returns messages.
        """
        try:
            # Rebuild state from current dbt project
            builder = StateBuilder(config)
            state = builder.build()

            # Run validation and create ghosts
            validation = builder.validate_and_sync(state)

            # Load positions from conceptual_layout.json
            layout_file = config.layout_file
            positions: dict[str, Any] = {}
            if layout_file.exists():
                with open(layout_file) as f:
                    layout_data = json.load(f) or {}
                    positions = layout_data.get("positions", {})

            # Identify ghost concepts
            ghost_concepts = [cid for cid, c in state.concepts.items() if c.is_ghost]

            # Build full state response (same format as GET /api/state)
            state_response = _serialize_state(state)
            state_response["positions"] = positions

            return jsonify(
                {
                    "success": True,
                    "messages": [
                        {
                            "id": msg.id,
                            "severity": msg.severity,
                            "text": msg.text,
                            "elementType": msg.element_type,
                            "elementId": msg.element_id,
                        }
                        for msg in validation.messages
                    ],
                    "counts": {
                        "error": validation.error_count,
                        "warning": validation.warning_count,
                        "info": validation.info_count,
                    },
                    "ghostConcepts": ghost_concepts,
                    "state": state_response,
                }
            )
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            logger.error("Parse error during sync: %s", e)
            return jsonify({"error": f"Parse error: {e}"}), 500
        except (FileNotFoundError, OSError) as e:
            logger.error("File I/O error during sync: %s", e)
            return jsonify({"error": f"File error: {e}"}), 500

    @app.route("/api/settings", methods=["GET"])
    def get_settings() -> Response | tuple[Response, int]:
        """Get configuration (domains, scan paths, validation)."""
        try:
            # Read full config from conceptual.yml
            conceptual_file = config.conceptual_file
            config_data: dict[str, Any] = {}
            domains_data: dict[str, Any] = {}

            if conceptual_file.exists():
                data = _read_conceptual_yml(conceptual_file)
                if "config" in data:
                    config_data = data["config"]
                if "domains" in data:
                    domains_data = data["domains"]

            return jsonify(
                {
                    "domains": domains_data,
                    "scan": config_data.get("scan", {"gold": config.gold_paths}),
                    "validation": config_data.get("validation", {}),
                }
            )
        except yaml.YAMLError as e:
            logger.error("Invalid YAML in conceptual.yml: %s", e)
            return jsonify({"error": f"YAML parse error: {e}"}), 500
        except (FileNotFoundError, OSError) as e:
            logger.error("File I/O error reading settings: %s", e)
            return jsonify({"error": f"File error: {e}"}), 500

    @app.route("/api/settings", methods=["POST"])
    def save_settings() -> Response | tuple[Response, int]:
        """Update configuration in conceptual.yml."""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400

            conceptual_file = config.conceptual_file
            if not conceptual_file.exists():
                return jsonify({"error": "conceptual.yml not found"}), 404

            # Read existing file
            conceptual_data = _read_conceptual_yml(conceptual_file)

            # Update domains
            if "domains" in data:
                conceptual_data["domains"] = data["domains"]

            # Update config section
            if "config" not in conceptual_data:
                conceptual_data["config"] = {}

            if "scan" in data:
                conceptual_data["config"]["scan"] = data["scan"]

            if "validation" in data:
                conceptual_data["config"]["validation"] = data["validation"]

            # Write back
            _write_conceptual_yml(conceptual_file, conceptual_data)

            # Invalidate cache
            _invalidate_cache()

            return jsonify({"success": True, "message": "Settings saved"})
        except (yaml.YAMLError, ValueError) as e:
            logger.error("Data error saving settings: %s", e)
            return jsonify({"error": f"Data error: {e}"}), 500
        except (FileNotFoundError, OSError) as e:
            logger.error("File I/O error saving settings: %s", e)
            return jsonify({"error": f"File error: {e}"}), 500

    @app.route("/api/config", methods=["GET"])
    def get_config() -> Response | tuple[Response, int]:
        """Get current configuration."""
        try:
            conceptual_file = config.conceptual_file
            if not conceptual_file.exists():
                return jsonify({"error": "conceptual.yml not found"}), 404

            data = _read_conceptual_yml(conceptual_file)

            return jsonify(data.get("config", {}))
        except yaml.YAMLError as e:
            logger.error("Invalid YAML in conceptual.yml: %s", e)
            return jsonify({"error": f"YAML parse error: {e}"}), 500
        except (FileNotFoundError, OSError) as e:
            logger.error("File I/O error reading config: %s", e)
            return jsonify({"error": f"File error: {e}"}), 500

    @app.route("/api/config", methods=["POST"])
    def save_config() -> Response | tuple[Response, int]:
        """Save configuration to conceptual.yml."""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400

            conceptual_file = config.conceptual_file
            if not conceptual_file.exists():
                return jsonify({"error": "conceptual.yml not found"}), 404

            conceptual_data = _read_conceptual_yml(conceptual_file)

            conceptual_data["config"] = data

            _write_conceptual_yml(conceptual_file, conceptual_data)

            # Invalidate cache
            _invalidate_cache()

            return jsonify({"success": True, "message": "Config saved"})
        except (yaml.YAMLError, ValueError) as e:
            logger.error("Data error saving config: %s", e)
            return jsonify({"error": f"Data error: {e}"}), 500
        except (FileNotFoundError, OSError) as e:
            logger.error("File I/O error saving config: %s", e)
            return jsonify({"error": f"File error: {e}"}), 500

    @app.route("/api/mode", methods=["GET"])
    def get_mode() -> Response:
        """Get current mode (demo or normal)."""
        return jsonify({"demoMode": app.config.get("DEMO_MODE", False)})

    return app


def run_server(
    project_dir: Path,
    host: str = "127.0.0.1",
    port: int = 8050,
    demo_mode: bool = False,
) -> None:
    """Run the web server using Waitress (production-ready WSGI server).

    Args:
        project_dir: Path to dbt project directory
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8050)
        demo_mode: Whether running in demo mode (default: False)
    """
    from waitress import serve

    app = create_app(project_dir, demo_mode=demo_mode)
    serve(app, host=host, port=port)
