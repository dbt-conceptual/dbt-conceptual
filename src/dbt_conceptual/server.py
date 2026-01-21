"""Flask web server for conceptual model UI."""

from pathlib import Path
from typing import Any, Union

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

            # Load positions from conceptual.layout.json
            layout_file = config.layout_file
            positions = {}
            if layout_file.exists():
                import json

                with open(layout_file) as f:
                    layout_data = json.load(f) or {}
                    positions = layout_data.get("positions", {})

            # Convert state to JSON-serializable format
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
                        "replaced_by": concept.replaced_by,
                        "bronze_models": concept.bronze_models or [],
                        "silver_models": concept.silver_models or [],
                        "gold_models": concept.gold_models or [],
                        # Validation fields
                        "isGhost": concept.is_ghost,
                        "validationStatus": concept.validation_status,
                        "validationMessages": concept.validation_messages,
                    }
                    for concept_id, concept in state.concepts.items()
                },
                "relationships": {
                    rel_id: {
                        "name": rel.name,  # Derived or custom
                        "verb": rel.verb,
                        "custom_name": rel.custom_name,
                        "from_concept": rel.from_concept,
                        "to_concept": rel.to_concept,
                        "cardinality": rel.cardinality,
                        "domains": rel.domains,
                        "owner": rel.owner,
                        "definition": rel.definition,
                        "status": rel.status,  # Derived at runtime
                        "realized_by": rel.realized_by or [],
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

            # Convert from API format to YAML format
            yaml_data: dict[str, Any] = {"version": 1}

            # Domains
            if data.get("domains"):
                yaml_data["domains"] = {
                    domain_id: {
                        k: v
                        for k, v in domain.items()
                        if v is not None and k != "display_name"
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
                            "bronze_models",  # Derived from manifest
                            "silver_models",  # Derived from meta.concept
                            "gold_models",  # Derived from meta.concept
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
                            "realized_by",
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
            import yaml

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
        """Get layout positions from conceptual.layout.json."""
        try:
            layout_file = config.layout_file
            if not layout_file.exists():
                return jsonify({"positions": {}})

            import json

            with open(layout_file) as f:
                layout_data = json.load(f) or {}

            return jsonify(layout_data.get("positions", {}))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/layout", methods=["POST"])
    def save_layout() -> Any:
        """Save layout positions to conceptual.layout.json."""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400

            layout_file = config.layout_file

            # Prepare layout data
            layout_data = {"version": 1, "positions": data.get("positions", {})}

            # Write to file
            import json

            with open(layout_file, "w") as f:
                json.dump(layout_data, f, indent=2)

            return jsonify({"success": True, "message": "Layout saved"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/models", methods=["GET"])
    def get_models() -> Any:
        """Get available dbt models from silver and gold layers."""
        try:
            scanner = DbtProjectScanner(config)
            models = scanner.find_model_files()
            return jsonify(models)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/sync", methods=["POST"])
    def sync_from_dbt() -> Any:
        """Trigger sync from dbt project.

        Scans dbt models for meta.concept and meta.realizes tags,
        creates ghost concepts for undefined references,
        runs validation, and returns messages.
        """
        try:
            # Rebuild state from current dbt project
            builder = StateBuilder(config)
            state = builder.build()

            # Run validation and create ghosts
            validation = builder.validate_and_sync(state)

            # Load positions from conceptual.layout.json
            layout_file = config.layout_file
            positions: dict[str, Any] = {}
            if layout_file.exists():
                import json as json_lib

                with open(layout_file) as f:
                    layout_data = json_lib.load(f) or {}
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
                        "replaced_by": concept.replaced_by,
                        "bronze_models": concept.bronze_models or [],
                        "silver_models": concept.silver_models or [],
                        "gold_models": concept.gold_models or [],
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
                        "custom_name": rel.custom_name,
                        "from_concept": rel.from_concept,
                        "to_concept": rel.to_concept,
                        "cardinality": rel.cardinality,
                        "domains": rel.domains,
                        "owner": rel.owner,
                        "definition": rel.definition,
                        "status": rel.status,
                        "realized_by": rel.realized_by or [],
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
        """Get configuration (domains, layer paths)."""
        try:
            # Read domains from conceptual.yml
            conceptual_file = config.conceptual_file
            domains_data = {}

            if conceptual_file.exists():
                import yaml

                with open(conceptual_file) as f:
                    data = yaml.safe_load(f) or {}
                    if "domains" in data:
                        domains_data = data["domains"]

            # Get paths from config
            paths = {
                "gold_paths": config.gold_paths,
                "silver_paths": config.silver_paths,
                "bronze_paths": getattr(config, "bronze_paths", []),
            }

            return jsonify(
                {
                    "domains": domains_data,
                    "paths": paths,
                    "conceptual_path": str(
                        config.conceptual_file.relative_to(config.project_dir)
                    ),
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/settings", methods=["POST"])
    def save_settings() -> Any:
        """Update configuration (domains, layer paths).

        Note: This saves domains to conceptual.yml and paths to dbt_project.yml.
        """
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Update domains in conceptual.yml
            if "domains" in data:
                conceptual_file = config.conceptual_file
                if conceptual_file.exists():
                    import yaml

                    with open(conceptual_file) as f:
                        conceptual_data = yaml.safe_load(f) or {}

                    conceptual_data["domains"] = data["domains"]

                    with open(conceptual_file, "w") as f:
                        yaml.dump(
                            conceptual_data,
                            f,
                            sort_keys=False,
                            default_flow_style=False,
                        )

            # Update paths in dbt_project.yml (under vars.dbt_conceptual)
            if "paths" in data:
                dbt_project_file = config.project_dir / "dbt_project.yml"
                if dbt_project_file.exists():
                    import yaml

                    with open(dbt_project_file) as f:
                        project_data = yaml.safe_load(f) or {}

                    # Ensure vars.dbt_conceptual exists
                    if "vars" not in project_data:
                        project_data["vars"] = {}
                    if "dbt_conceptual" not in project_data["vars"]:
                        project_data["vars"]["dbt_conceptual"] = {}

                    # Update paths
                    paths = data["paths"]
                    if "gold_paths" in paths:
                        project_data["vars"]["dbt_conceptual"]["gold_paths"] = paths[
                            "gold_paths"
                        ]
                    if "silver_paths" in paths:
                        project_data["vars"]["dbt_conceptual"]["silver_paths"] = paths[
                            "silver_paths"
                        ]
                    if "bronze_paths" in paths:
                        project_data["vars"]["dbt_conceptual"]["bronze_paths"] = paths[
                            "bronze_paths"
                        ]

                    with open(dbt_project_file, "w") as f:
                        yaml.dump(
                            project_data, f, sort_keys=False, default_flow_style=False
                        )

            return jsonify({"success": True, "message": "Settings saved"})
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
    """Run the Flask development server.

    Args:
        project_dir: Path to dbt project directory
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8050)
        demo_mode: Whether running in demo mode (default: False)
    """
    app = create_app(project_dir, demo_mode=demo_mode)
    app.run(host=host, port=port, debug=True)
