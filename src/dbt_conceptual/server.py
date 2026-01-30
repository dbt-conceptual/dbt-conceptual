"""Flask web server for conceptual model UI.

v1.0: Simplified API with flat models[], no realized_by.
"""

import json
from pathlib import Path
from typing import Any, Union

import yaml
from flask import Flask, Response, jsonify, request, send_from_directory

from dbt_conceptual.config import Config
from dbt_conceptual.exporter.bus_matrix import export_bus_matrix
from dbt_conceptual.exporter.coverage import export_coverage
from dbt_conceptual.parser import StateBuilder
from dbt_conceptual.scanner import DbtProjectScanner


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
    def index() -> Union[str, Response]:
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
    def get_state() -> Any:
        """Get current conceptual model state as JSON."""
        try:
            builder = StateBuilder(config)
            state = builder.build()

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
            positions = {}
            if layout_file.exists():
                with open(layout_file) as f:
                    layout_data = json.load(f) or {}
                    positions = layout_data.get("positions", {})

            # Convert state to JSON-serializable format (v1.0 simplified)
            response = {
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
                        "validationStatus": concept.validation_status,
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
                        "validationStatus": rel.validation_status,
                        "validationMessages": rel.validation_messages,
                    }
                    for rel_id, rel in state.relationships.items()
                },
                "positions": positions,  # React Flow node positions
                "hasIntegrityErrors": has_integrity_errors,
            }

            return jsonify(response)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/state", methods=["POST"])
    def save_state() -> Any:
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
            with open(conceptual_file) as f:
                existing_data = yaml.safe_load(f) or {}

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
            if data.get("concepts"):
                yaml_data["concepts"] = {}
                for concept_id, concept in data["concepts"].items():
                    # Skip ghost concepts that haven't been properly defined
                    if concept.get("isGhost") and not concept.get("domain"):
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
                    rel_dict = {}
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
            with open(conceptual_file, "w") as f:
                yaml.dump(yaml_data, f, sort_keys=False, default_flow_style=False)

            return jsonify({"success": True, "message": "Saved to conceptual.yml"})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/coverage", methods=["GET"])
    def get_coverage() -> Any:
        """Get coverage report as HTML."""
        try:
            from io import StringIO

            builder = StateBuilder(config)
            state = builder.build()

            output = StringIO()
            export_coverage(state, output)

            return output.getvalue(), 200, {"Content-Type": "text/html"}
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/bus-matrix", methods=["GET"])
    def get_bus_matrix() -> Any:
        """Get bus matrix as HTML."""
        try:
            from io import StringIO

            builder = StateBuilder(config)
            state = builder.build()

            output = StringIO()
            export_bus_matrix(state, output)

            return output.getvalue(), 200, {"Content-Type": "text/html"}
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/layout", methods=["GET"])
    def get_layout() -> Any:
        """Get layout positions from conceptual_layout.json."""
        try:
            layout_file = config.layout_file
            if not layout_file.exists():
                return jsonify({"positions": {}})

            with open(layout_file) as f:
                layout_data = json.load(f) or {}

            return jsonify(layout_data.get("positions", {}))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/layout", methods=["POST"])
    def save_layout() -> Any:
        """Save layout positions to conceptual_layout.json."""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400

            layout_file = config.layout_file

            # Prepare layout data
            layout_data = {"version": 1, "positions": data.get("positions", {})}

            # Write to file
            with open(layout_file, "w") as f:
                json.dump(layout_data, f, indent=2)

            return jsonify({"success": True, "message": "Layout saved"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/models", methods=["GET"])
    def get_models() -> Any:
        """Get available dbt models from gold layer."""
        try:
            scanner = DbtProjectScanner(config)
            models = scanner.scan()
            return jsonify(models)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/sync", methods=["POST"])
    def sync_from_dbt() -> Any:
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
            state_response = {
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
                        "status": concept.status,
                        "color": concept.color,
                        "models": concept.models,
                        "isGhost": concept.is_ghost,
                        "validationStatus": concept.validation_status,
                        "validationMessages": concept.validation_messages,
                    }
                    for concept_id, concept in state.concepts.items()
                },
                "relationships": {
                    rel_id: {
                        "name": rel.name,
                        "verb": rel.verb,
                        "from_concept": rel.from_concept,
                        "to_concept": rel.to_concept,
                        "cardinality": rel.cardinality,
                        "owner": rel.owner,
                        "definition": rel.definition,
                        "status": rel.get_status(state.concepts),
                        "validationStatus": rel.validation_status,
                        "validationMessages": rel.validation_messages,
                    }
                    for rel_id, rel in state.relationships.items()
                },
                "positions": positions,
            }

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
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/settings", methods=["GET"])
    def get_settings() -> Any:
        """Get configuration (domains, scan paths, validation)."""
        try:
            # Read full config from conceptual.yml
            conceptual_file = config.conceptual_file
            config_data: dict[str, Any] = {}
            domains_data: dict[str, Any] = {}

            if conceptual_file.exists():
                with open(conceptual_file) as f:
                    data = yaml.safe_load(f) or {}
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
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/settings", methods=["POST"])
    def save_settings() -> Any:
        """Update configuration in conceptual.yml."""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400

            conceptual_file = config.conceptual_file
            if not conceptual_file.exists():
                return jsonify({"error": "conceptual.yml not found"}), 404

            # Read existing file
            with open(conceptual_file) as f:
                conceptual_data = yaml.safe_load(f) or {}

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
            with open(conceptual_file, "w") as f:
                yaml.dump(
                    conceptual_data,
                    f,
                    sort_keys=False,
                    default_flow_style=False,
                )

            return jsonify({"success": True, "message": "Settings saved"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/config", methods=["GET"])
    def get_config() -> Any:
        """Get current configuration."""
        try:
            conceptual_file = config.conceptual_file
            if not conceptual_file.exists():
                return jsonify({"error": "conceptual.yml not found"}), 404

            with open(conceptual_file) as f:
                data = yaml.safe_load(f) or {}

            return jsonify(data.get("config", {}))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/config", methods=["POST"])
    def save_config() -> Any:
        """Save configuration to conceptual.yml."""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400

            conceptual_file = config.conceptual_file
            if not conceptual_file.exists():
                return jsonify({"error": "conceptual.yml not found"}), 404

            with open(conceptual_file) as f:
                conceptual_data = yaml.safe_load(f) or {}

            conceptual_data["config"] = data

            with open(conceptual_file, "w") as f:
                yaml.dump(
                    conceptual_data,
                    f,
                    sort_keys=False,
                    default_flow_style=False,
                )

            return jsonify({"success": True, "message": "Config saved"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/mode", methods=["GET"])
    def get_mode() -> Any:
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
