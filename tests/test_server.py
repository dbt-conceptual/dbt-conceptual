"""Tests for Flask server.

v1.0: conceptual.yml in project root, gold-only scanning.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from dbt_conceptual.server import create_app


@pytest.fixture
def temp_project():
    """Create a temporary dbt project for testing."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create dbt_project.yml
        dbt_project_data = {
            "name": "test_project",
            "version": "1.0.0",
            "config-version": 2,
        }
        with open(project_dir / "dbt_project.yml", "w") as f:
            yaml.dump(dbt_project_data, f)

        # Create conceptual.yml in project root (v1.0)
        conceptual_data = {
            "version": 1,
            "domains": {
                "customer": {"name": "customer", "color": "#4a9eff"},
            },
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "customer",
                    "definition": "A person who purchases products",
                }
            },
            "relationships": [],
        }
        with open(project_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        # Create layout file in project root (v1.0)
        layout_data = {
            "version": 1,
            "positions": {
                "customer": {"x": 100, "y": 100},
            },
        }
        with open(project_dir / "conceptual_layout.json", "w") as f:
            json.dump(layout_data, f)

        yield project_dir


def test_create_app(temp_project):
    """Test Flask app creation."""
    app = create_app(temp_project)
    assert app is not None
    assert app.config["PROJECT_DIR"] == temp_project


def test_create_app_static_folder(temp_project):
    """Test static folder configuration."""
    app = create_app(temp_project)

    # Should have a static folder configured
    assert app.static_folder is not None

    # Should be either frontend/dist or static
    static_path = Path(app.static_folder)
    assert static_path.name in ("dist", "static")


def test_create_app_static_folder_fallback(temp_project, monkeypatch):
    """Test static folder falls back to 'static' when frontend/dist doesn't exist."""
    # Mock Path.exists to simulate missing frontend/dist
    original_exists = Path.exists

    def mock_exists(self):
        # Make frontend/dist appear to not exist
        if "frontend" in str(self) and "dist" in str(self):
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", mock_exists)

    app = create_app(temp_project)

    # Should fall back to static folder
    assert app.static_folder is not None
    static_path = Path(app.static_folder)
    assert static_path.name == "static"


def test_index_route_no_frontend(temp_project, monkeypatch):
    """Test index route when frontend build doesn't exist."""
    # Mock Path.exists to simulate missing frontend build
    original_exists = Path.exists

    def mock_exists(self):
        # If checking for index.html in static folder, return False
        if self.name == "index.html":
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", mock_exists)

    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 200
    assert b"dbt-conceptual UI" in response.data
    assert b"Frontend build not found" in response.data


def test_index_route_with_frontend(temp_project):
    """Test index route when frontend build exists."""
    app = create_app(temp_project)

    # Create a mock frontend build
    static_dir = Path(app.static_folder)
    static_dir.mkdir(parents=True, exist_ok=True)
    index_html = static_dir / "index.html"
    index_html.write_text("<!DOCTYPE html><html><body>React App</body></html>")

    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"React App" in response.data


def test_api_state_get(temp_project):
    """Test GET /api/state endpoint."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/state")
    assert response.status_code == 200

    data = response.get_json()
    assert "domains" in data
    assert "concepts" in data
    assert "relationships" in data
    assert "positions" in data

    # Check customer concept exists
    assert "customer" in data["concepts"]
    assert data["concepts"]["customer"]["name"] == "Customer"
    assert data["concepts"]["customer"]["domain"] == "customer"

    # Check positions
    assert "customer" in data["positions"]
    assert data["positions"]["customer"]["x"] == 100


def test_api_layout_get(temp_project):
    """Test GET /api/layout endpoint."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/layout")
    assert response.status_code == 200

    data = response.get_json()
    # API returns the positions dict directly
    assert "customer" in data
    assert data["customer"]["x"] == 100
    assert data["customer"]["y"] == 100


def test_api_layout_post(temp_project):
    """Test POST /api/layout endpoint."""
    app = create_app(temp_project)
    client = app.test_client()

    new_positions = {
        "positions": {
            "customer": {"x": 200, "y": 200},
        }
    }

    response = client.post("/api/layout", json=new_positions)
    assert response.status_code == 200

    data = response.get_json()
    assert data["success"] is True

    # Verify positions were saved to conceptual_layout.json in project root
    layout_file = temp_project / "conceptual_layout.json"
    with open(layout_file) as f:
        saved_data = json.load(f)
    assert saved_data["positions"]["customer"]["x"] == 200
    assert saved_data["positions"]["customer"]["y"] == 200


def test_api_settings_get(temp_project):
    """Test GET /api/settings endpoint."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/settings")
    assert response.status_code == 200

    data = response.get_json()
    assert "domains" in data
    assert "scan" in data
    assert "validation" in data

    # Check domains
    assert "customer" in data["domains"]


def test_api_settings_post_domains(temp_project):
    """Test POST /api/settings endpoint for domains."""
    app = create_app(temp_project)
    client = app.test_client()

    new_settings = {
        "domains": {
            "customer": {"name": "customer", "color": "#ff0000"},
            "product": {"name": "product", "color": "#00ff00"},
        }
    }

    response = client.post("/api/settings", json=new_settings)
    assert response.status_code == 200

    data = response.get_json()
    assert data["success"] is True

    # Verify domains were saved to conceptual.yml in project root
    conceptual_file = temp_project / "conceptual.yml"
    with open(conceptual_file) as f:
        saved_data = yaml.safe_load(f)
    assert "product" in saved_data["domains"]
    assert saved_data["domains"]["customer"]["color"] == "#ff0000"


def test_cors_headers_debug_mode(temp_project):
    """Test CORS headers are added in debug mode."""
    app = create_app(temp_project)
    app.debug = True
    client = app.test_client()

    response = client.get("/api/state")
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"
    assert "Content-Type" in response.headers.get("Access-Control-Allow-Headers", "")


def test_api_state_post_updates_conceptual(temp_project):
    """Test POST /api/state saves changes to conceptual.yml."""
    app = create_app(temp_project)
    client = app.test_client()

    # Get current state
    response = client.get("/api/state")
    state = response.get_json()

    # Update concept
    state["concepts"]["customer"]["definition"] = "Updated definition"
    state["concepts"]["new_concept"] = {
        "name": "New Concept",
        "domain": "customer",
        "definition": "A new concept",
        "status": "stub",  # This should not be saved (derived field)
        "models": [],  # v1.0: flat models list
    }

    response = client.post("/api/state", json=state)
    assert response.status_code == 200

    # Verify changes were saved to conceptual.yml in project root
    conceptual_file = temp_project / "conceptual.yml"
    with open(conceptual_file) as f:
        saved_data = yaml.safe_load(f)

    assert saved_data["concepts"]["customer"]["definition"] == "Updated definition"
    assert "new_concept" in saved_data["concepts"]
    # Status should not be in YAML (it's derived)
    assert "status" not in saved_data["concepts"]["new_concept"]
