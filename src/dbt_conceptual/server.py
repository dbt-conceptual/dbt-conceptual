"""Flask web server for conceptual model UI."""

from pathlib import Path
from typing import Any, Union

from flask import Flask, Response, jsonify, request, send_from_directory  # type: ignore

from dbt_conceptual.config import Config
from dbt_conceptual.exporter.bus_matrix import export_bus_matrix
from dbt_conceptual.exporter.coverage import export_coverage
from dbt_conceptual.parser import StateBuilder


def create_app(project_dir: Path) -> Flask:
    """Create and configure Flask app.

    Args:
        project_dir: Path to dbt project directory

    Returns:
        Configured Flask app
    """
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config["PROJECT_DIR"] = project_dir

    # Load config
    config = Config.load(project_dir=project_dir)

    @app.route("/")
    def index() -> Union[str, Response]:
        """Serve the main UI page."""
        static_dir = Path(__file__).parent / "static"
        if (static_dir / "index.html").exists():
            return send_from_directory(static_dir, "index.html")
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
            <p>Frontend is building... Check back soon!</p>
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
                        "status": concept.status,
                        "silver_models": concept.silver_models or [],
                        "gold_models": concept.gold_models or [],
                    }
                    for concept_id, concept in state.concepts.items()
                },
                "relationships": {
                    rel_id: {
                        "name": rel.name,
                        "from_concept": rel.from_concept,
                        "to_concept": rel.to_concept,
                        "cardinality": rel.cardinality,
                        "realized_by": rel.realized_by or [],
                    }
                    for rel_id, rel in state.relationships.items()
                },
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
                yaml_data["concepts"] = {
                    concept_id: {
                        k: v
                        for k, v in concept.items()
                        if v is not None
                        and k not in ["display_name", "silver_models", "gold_models"]
                    }
                    for concept_id, concept in data["concepts"].items()
                }

            # Relationships
            if data.get("relationships"):
                yaml_data["relationships"] = [
                    {
                        k: v
                        for k, v in rel.items()
                        if v is not None and k != "realized_by"
                    }
                    for rel in data["relationships"].values()
                ]

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

    return app


def run_server(project_dir: Path, host: str = "127.0.0.1", port: int = 5000) -> None:
    """Run the Flask development server.

    Args:
        project_dir: Path to dbt project directory
        host: Host to bind to
        port: Port to bind to
    """
    app = create_app(project_dir)
    app.run(host=host, port=port, debug=True)
