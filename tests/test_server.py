"""Tests for Flask server.

v1.0: conceptual.yml in project root, gold-only scanning.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
import yaml

from dbt_conceptual.server import (
    _read_conceptual_yml,
    _serialize_state,
    _write_conceptual_yml,
    create_app,
)
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    ProjectState,
    RelationshipState,
)


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


@pytest.fixture
def rich_project():
    """Create a project with relationships and multiple concepts for broader coverage."""
    with TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        dbt_project_data = {
            "name": "test_project",
            "version": "1.0.0",
            "config-version": 2,
        }
        with open(project_dir / "dbt_project.yml", "w") as f:
            yaml.dump(dbt_project_data, f)

        conceptual_data = {
            "version": 1,
            "config": {
                "scan": {"gold": ["models/marts/**/*.yml"]},
                "validation": {"defaults": {"orphan_models": "warn"}},
            },
            "domains": {
                "customer": {"name": "customer", "color": "#4a9eff"},
                "product": {"name": "product", "color": "#ff4a4a"},
            },
            "concepts": {
                "customer": {
                    "name": "Customer",
                    "domain": "customer",
                    "definition": "A person who purchases products",
                },
                "order": {
                    "name": "Order",
                    "domain": "customer",
                    "definition": "A purchase transaction",
                },
                "product": {
                    "name": "Product",
                    "domain": "product",
                    "definition": "An item for sale",
                },
            },
            "relationships": [
                {
                    "from": "customer",
                    "to": "order",
                    "verb": "places",
                    "cardinality": "1:N",
                },
                {
                    "from": "order",
                    "to": "product",
                    "verb": "contains",
                    "cardinality": "1:N",
                },
            ],
        }
        with open(project_dir / "conceptual.yml", "w") as f:
            yaml.dump(conceptual_data, f)

        layout_data = {
            "version": 1,
            "positions": {
                "customer": {"x": 100, "y": 100},
                "order": {"x": 300, "y": 100},
            },
        }
        with open(project_dir / "conceptual_layout.json", "w") as f:
            json.dump(layout_data, f)

        yield project_dir


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestSerializeState:
    """Tests for the _serialize_state helper."""

    def test_serialize_empty_state(self):
        """Empty state produces empty containers."""
        state = ProjectState()
        result = _serialize_state(state)
        assert result == {"domains": {}, "concepts": {}, "relationships": {}}

    def test_serialize_state_with_concepts(self):
        """Concepts are serialized with all expected fields."""
        state = ProjectState()
        state.domains["sales"] = DomainState(
            name="sales", display_name="Sales", color="#abc"
        )
        state.concepts["customer"] = ConceptState(
            name="Customer",
            domain="sales",
            owner="team-a",
            definition="A buyer",
            color="#fff",
            models=["dim_customer"],
        )
        result = _serialize_state(state)

        assert "sales" in result["domains"]
        assert result["domains"]["sales"]["name"] == "sales"
        assert result["domains"]["sales"]["display_name"] == "Sales"
        assert result["domains"]["sales"]["color"] == "#abc"

        concept = result["concepts"]["customer"]
        assert concept["name"] == "Customer"
        assert concept["domain"] == "sales"
        assert concept["owner"] == "team-a"
        assert concept["status"] == "complete"
        assert concept["models"] == ["dim_customer"]
        assert concept["isGhost"] is False
        assert concept["validationStatus"] == "valid"

    def test_serialize_state_with_relationships(self):
        """Relationships are serialized with derived status."""
        state = ProjectState()
        state.concepts["a"] = ConceptState(name="A", domain="d")
        state.concepts["b"] = ConceptState(name="B", domain="d")
        state.relationships["a:links:b"] = RelationshipState(
            verb="links", from_concept="a", to_concept="b", cardinality="1:1"
        )
        result = _serialize_state(state)

        rel = result["relationships"]["a:links:b"]
        assert rel["verb"] == "links"
        assert rel["from_concept"] == "a"
        assert rel["to_concept"] == "b"
        assert rel["cardinality"] == "1:1"
        assert rel["status"] == "complete"


class TestReadWriteConceptualYml:
    """Tests for _read_conceptual_yml and _write_conceptual_yml helpers."""

    def test_read_conceptual_yml_valid(self):
        """Reading a valid YAML file returns parsed data."""
        with TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "conceptual.yml"
            f.write_text("domains:\n  sales:\n    name: Sales\n")
            result = _read_conceptual_yml(f)
            assert result == {"domains": {"sales": {"name": "Sales"}}}

    def test_read_conceptual_yml_empty(self):
        """Reading an empty YAML file returns empty dict."""
        with TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "conceptual.yml"
            f.write_text("")
            result = _read_conceptual_yml(f)
            assert result == {}

    def test_read_conceptual_yml_missing(self):
        """Reading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            _read_conceptual_yml(Path("/nonexistent/conceptual.yml"))

    def test_read_conceptual_yml_invalid_yaml(self):
        """Reading invalid YAML raises yaml.YAMLError."""
        with TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "conceptual.yml"
            f.write_text("invalid: [\nyaml: {")
            with pytest.raises(yaml.YAMLError):
                _read_conceptual_yml(f)

    def test_write_conceptual_yml(self):
        """Writing data creates a valid YAML file."""
        with TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "conceptual.yml"
            data = {"domains": {"sales": {"name": "Sales"}}}
            _write_conceptual_yml(f, data)
            result = yaml.safe_load(f.read_text())
            assert result == data

    def test_write_conceptual_yml_preserves_order(self):
        """Writing data preserves key order (sort_keys=False)."""
        with TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "conceptual.yml"
            data = {"concepts": {}, "domains": {}, "config": {}}
            _write_conceptual_yml(f, data)
            content = f.read_text()
            # concepts should appear before domains since sort_keys=False
            assert content.index("concepts") < content.index("domains")


# ---------------------------------------------------------------------------
# App creation tests
# ---------------------------------------------------------------------------


def test_create_app(temp_project):
    """Test Flask app creation."""
    app = create_app(temp_project)
    assert app is not None
    assert app.config["PROJECT_DIR"] == temp_project


def test_create_app_demo_mode(temp_project):
    """Test Flask app creation with demo mode."""
    app = create_app(temp_project, demo_mode=True)
    assert app.config["DEMO_MODE"] is True


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


# ---------------------------------------------------------------------------
# Index route tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# GET /api/state tests
# ---------------------------------------------------------------------------


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


def test_api_state_get_has_integrity_errors_flag(rich_project):
    """Test GET /api/state returns hasIntegrityErrors flag."""
    app = create_app(rich_project)
    client = app.test_client()

    response = client.get("/api/state")
    data = response.get_json()
    assert "hasIntegrityErrors" in data
    assert data["hasIntegrityErrors"] is False


def test_api_state_get_with_relationships(rich_project):
    """Test GET /api/state includes relationship data."""
    app = create_app(rich_project)
    client = app.test_client()

    response = client.get("/api/state")
    data = response.get_json()
    assert len(data["relationships"]) == 2


def test_api_state_get_no_layout_file(temp_project):
    """Test GET /api/state when layout file is missing."""
    # Remove layout file
    (temp_project / "conceptual_layout.json").unlink()

    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/state")
    assert response.status_code == 200
    data = response.get_json()
    assert data["positions"] == {}


# ---------------------------------------------------------------------------
# POST /api/state tests
# ---------------------------------------------------------------------------


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


def test_api_state_post_no_data(temp_project):
    """Test POST /api/state with no JSON body returns 400."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.post("/api/state", data="", content_type="application/json")
    assert response.status_code == 400


def test_api_state_post_missing_file(temp_project):
    """Test POST /api/state when conceptual.yml is missing returns 404."""
    (temp_project / "conceptual.yml").unlink()

    app = create_app(temp_project)
    client = app.test_client()

    response = client.post("/api/state", json={"concepts": {}})
    assert response.status_code == 404


def test_api_state_post_with_relationships(rich_project):
    """Test POST /api/state saves relationship data."""
    app = create_app(rich_project)
    client = app.test_client()

    state = client.get("/api/state").get_json()

    response = client.post("/api/state", json=state)
    assert response.status_code == 200

    conceptual_file = rich_project / "conceptual.yml"
    with open(conceptual_file) as f:
        saved_data = yaml.safe_load(f)

    assert "relationships" in saved_data
    assert len(saved_data["relationships"]) == 2
    # Check that from_concept -> from mapping works
    rel = saved_data["relationships"][0]
    assert "from" in rel
    assert "to" in rel


def test_api_state_post_skips_ghost_concepts(temp_project):
    """Test POST /api/state skips ghost concepts without domains."""
    app = create_app(temp_project)
    client = app.test_client()

    state_data = {
        "domains": {"customer": {"name": "customer", "color": "#4a9eff"}},
        "concepts": {
            "customer": {
                "name": "Customer",
                "domain": "customer",
                "definition": "A buyer",
            },
            "ghost_concept": {
                "name": "Ghost",
                "isGhost": True,
                # No domain -- should be skipped
            },
        },
    }

    response = client.post("/api/state", json=state_data)
    assert response.status_code == 200

    conceptual_file = temp_project / "conceptual.yml"
    with open(conceptual_file) as f:
        saved_data = yaml.safe_load(f)

    assert "ghost_concept" not in saved_data["concepts"]


def test_api_state_post_preserves_config(rich_project):
    """Test POST /api/state preserves the config section."""
    app = create_app(rich_project)
    client = app.test_client()

    state = client.get("/api/state").get_json()
    response = client.post("/api/state", json=state)
    assert response.status_code == 200

    conceptual_file = rich_project / "conceptual.yml"
    with open(conceptual_file) as f:
        saved_data = yaml.safe_load(f)

    assert "config" in saved_data
    assert "scan" in saved_data["config"]


# ---------------------------------------------------------------------------
# GET /api/coverage tests
# ---------------------------------------------------------------------------


def test_api_coverage_get(temp_project):
    """Test GET /api/coverage returns HTML content."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/coverage")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")


def test_api_coverage_get_rich(rich_project):
    """Test GET /api/coverage with a richer project."""
    app = create_app(rich_project)
    client = app.test_client()

    response = client.get("/api/coverage")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/bus-matrix tests
# ---------------------------------------------------------------------------


def test_api_bus_matrix_get(temp_project):
    """Test GET /api/bus-matrix returns HTML content."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/bus-matrix")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")


def test_api_bus_matrix_get_rich(rich_project):
    """Test GET /api/bus-matrix with relationships and multiple concepts."""
    app = create_app(rich_project)
    client = app.test_client()

    response = client.get("/api/bus-matrix")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/layout tests
# ---------------------------------------------------------------------------


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


def test_api_layout_get_no_file(temp_project):
    """Test GET /api/layout when layout file does not exist."""
    (temp_project / "conceptual_layout.json").unlink()

    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/layout")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"positions": {}}


def test_api_layout_get_invalid_json(temp_project):
    """Test GET /api/layout with corrupt JSON returns 500."""
    (temp_project / "conceptual_layout.json").write_text("{invalid json")

    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/layout")
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert "Invalid layout JSON" in data["error"]


# ---------------------------------------------------------------------------
# POST /api/layout tests
# ---------------------------------------------------------------------------


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


def test_api_layout_post_no_data(temp_project):
    """Test POST /api/layout with no body returns 400."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.post("/api/layout", data="", content_type="application/json")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/models tests
# ---------------------------------------------------------------------------


def test_api_models_get(temp_project):
    """Test GET /api/models returns a list."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_api_models_get_with_schema_files(rich_project):
    """Test GET /api/models scans dbt schema files."""
    # Create a models directory with a schema file
    models_dir = rich_project / "models" / "marts"
    models_dir.mkdir(parents=True)
    schema_data = {
        "models": [
            {
                "name": "dim_customer",
                "description": "Customer dimension",
                "meta": {"concept": "customer"},
            }
        ]
    }
    with open(models_dir / "schema.yml", "w") as f:
        yaml.dump(schema_data, f)

    app = create_app(rich_project)
    client = app.test_client()

    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1
    assert any(m["name"] == "dim_customer" for m in data)


# ---------------------------------------------------------------------------
# POST /api/sync tests
# ---------------------------------------------------------------------------


def test_api_sync_post(temp_project):
    """Test POST /api/sync triggers sync and returns validation messages."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.post("/api/sync")
    assert response.status_code == 200

    data = response.get_json()
    assert data["success"] is True
    assert "messages" in data
    assert "counts" in data
    assert "ghostConcepts" in data
    assert "state" in data

    # State should be in same format as GET /api/state
    state = data["state"]
    assert "domains" in state
    assert "concepts" in state
    assert "relationships" in state
    assert "positions" in state


def test_api_sync_post_with_relationships(rich_project):
    """Test POST /api/sync with relationships."""
    app = create_app(rich_project)
    client = app.test_client()

    response = client.post("/api/sync")
    assert response.status_code == 200
    data = response.get_json()

    assert len(data["state"]["relationships"]) == 2
    assert "counts" in data
    assert "error" in data["counts"]
    assert "warning" in data["counts"]
    assert "info" in data["counts"]


def test_api_sync_post_no_layout_file(temp_project):
    """Test POST /api/sync when layout file is missing."""
    (temp_project / "conceptual_layout.json").unlink()

    app = create_app(temp_project)
    client = app.test_client()

    response = client.post("/api/sync")
    assert response.status_code == 200
    data = response.get_json()
    assert data["state"]["positions"] == {}


# ---------------------------------------------------------------------------
# GET /api/settings tests
# ---------------------------------------------------------------------------


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


def test_api_settings_get_with_config(rich_project):
    """Test GET /api/settings returns config section data."""
    app = create_app(rich_project)
    client = app.test_client()

    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.get_json()

    assert "scan" in data
    assert "gold" in data["scan"]
    assert "validation" in data


def test_api_settings_get_no_conceptual_file(temp_project):
    """Test GET /api/settings when conceptual.yml is missing returns defaults."""
    (temp_project / "conceptual.yml").unlink()

    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.get_json()
    assert data["domains"] == {}


# ---------------------------------------------------------------------------
# POST /api/settings tests
# ---------------------------------------------------------------------------


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


def test_api_settings_post_no_data(temp_project):
    """Test POST /api/settings with no body returns 400."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.post("/api/settings", data="", content_type="application/json")
    assert response.status_code == 400


def test_api_settings_post_missing_file(temp_project):
    """Test POST /api/settings when conceptual.yml is missing returns 404."""
    (temp_project / "conceptual.yml").unlink()

    app = create_app(temp_project)
    client = app.test_client()

    response = client.post("/api/settings", json={"domains": {}})
    assert response.status_code == 404


def test_api_settings_post_scan_and_validation(rich_project):
    """Test POST /api/settings updates scan and validation sections."""
    app = create_app(rich_project)
    client = app.test_client()

    new_settings = {
        "scan": {"gold": ["models/gold/**/*.yml"]},
        "validation": {"defaults": {"orphan_models": "error"}},
    }

    response = client.post("/api/settings", json=new_settings)
    assert response.status_code == 200

    conceptual_file = rich_project / "conceptual.yml"
    with open(conceptual_file) as f:
        saved_data = yaml.safe_load(f)

    assert saved_data["config"]["scan"]["gold"] == ["models/gold/**/*.yml"]
    assert saved_data["config"]["validation"]["defaults"]["orphan_models"] == "error"


def test_api_settings_post_creates_config_section(temp_project):
    """Test POST /api/settings creates config section if missing."""
    # Rewrite conceptual.yml without config section
    conceptual_file = temp_project / "conceptual.yml"
    data = {"domains": {"customer": {"name": "customer"}}, "concepts": {}}
    with open(conceptual_file, "w") as f:
        yaml.dump(data, f)

    app = create_app(temp_project)
    client = app.test_client()

    response = client.post(
        "/api/settings",
        json={"scan": {"gold": ["models/marts/**/*.yml"]}},
    )
    assert response.status_code == 200

    with open(conceptual_file) as f:
        saved = yaml.safe_load(f)
    assert "config" in saved
    assert saved["config"]["scan"]["gold"] == ["models/marts/**/*.yml"]


# ---------------------------------------------------------------------------
# GET /api/config tests
# ---------------------------------------------------------------------------


def test_api_config_get(rich_project):
    """Test GET /api/config returns config section."""
    app = create_app(rich_project)
    client = app.test_client()

    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.get_json()
    assert "scan" in data
    assert "validation" in data


def test_api_config_get_no_config_section(temp_project):
    """Test GET /api/config returns empty dict when no config section."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {}


def test_api_config_get_missing_file(temp_project):
    """Test GET /api/config when conceptual.yml is missing returns 404."""
    (temp_project / "conceptual.yml").unlink()

    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/config")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/config tests
# ---------------------------------------------------------------------------


def test_api_config_post(rich_project):
    """Test POST /api/config saves config section."""
    app = create_app(rich_project)
    client = app.test_client()

    new_config = {
        "scan": {"gold": ["models/analytics/**/*.yml"]},
        "validation": {"defaults": {"missing_definitions": "error"}},
    }

    response = client.post("/api/config", json=new_config)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

    conceptual_file = rich_project / "conceptual.yml"
    with open(conceptual_file) as f:
        saved_data = yaml.safe_load(f)

    assert saved_data["config"]["scan"]["gold"] == ["models/analytics/**/*.yml"]


def test_api_config_post_no_data(temp_project):
    """Test POST /api/config with no body returns 400."""
    app = create_app(temp_project)
    client = app.test_client()

    response = client.post("/api/config", data="", content_type="application/json")
    assert response.status_code == 400


def test_api_config_post_missing_file(temp_project):
    """Test POST /api/config when conceptual.yml is missing returns 404."""
    (temp_project / "conceptual.yml").unlink()

    app = create_app(temp_project)
    client = app.test_client()

    response = client.post("/api/config", json={"scan": {}})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/mode tests
# ---------------------------------------------------------------------------


def test_api_mode_get_normal(temp_project):
    """Test GET /api/mode returns demoMode false in normal mode."""
    app = create_app(temp_project, demo_mode=False)
    client = app.test_client()

    response = client.get("/api/mode")
    assert response.status_code == 200
    data = response.get_json()
    assert data["demoMode"] is False


def test_api_mode_get_demo(temp_project):
    """Test GET /api/mode returns demoMode true in demo mode."""
    app = create_app(temp_project, demo_mode=True)
    client = app.test_client()

    response = client.get("/api/mode")
    assert response.status_code == 200
    data = response.get_json()
    assert data["demoMode"] is True


# ---------------------------------------------------------------------------
# CORS tests
# ---------------------------------------------------------------------------


def test_cors_headers_debug_mode(temp_project):
    """Test CORS headers are added in debug mode."""
    app = create_app(temp_project)
    app.debug = True
    client = app.test_client()

    response = client.get("/api/state")
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "*"
    assert "Content-Type" in response.headers.get("Access-Control-Allow-Headers", "")


def test_no_cors_headers_production(temp_project):
    """Test CORS headers are NOT added in production mode."""
    app = create_app(temp_project)
    app.debug = False
    client = app.test_client()

    response = client.get("/api/state")
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") is None


# ---------------------------------------------------------------------------
# Error handling tests (verifying specific exception types)
# ---------------------------------------------------------------------------


def test_api_state_get_yaml_error(temp_project):
    """Test GET /api/state handles invalid YAML in conceptual.yml."""
    # Create app first with valid YAML, then corrupt the file
    app = create_app(temp_project)
    client = app.test_client()

    (temp_project / "conceptual.yml").write_text("invalid: [\nyaml: {")

    response = client.get("/api/state")
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert "Parse error" in data["error"]


def test_api_sync_yaml_error(temp_project):
    """Test POST /api/sync handles invalid YAML."""
    app = create_app(temp_project)
    client = app.test_client()

    (temp_project / "conceptual.yml").write_text("invalid: [\nyaml: {")

    response = client.post("/api/sync")
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data


def test_api_settings_get_yaml_error(temp_project):
    """Test GET /api/settings handles invalid YAML."""
    app = create_app(temp_project)
    client = app.test_client()

    (temp_project / "conceptual.yml").write_text("invalid: [\nyaml: {")

    response = client.get("/api/settings")
    assert response.status_code == 500
    data = response.get_json()
    assert "error" in data
    assert "YAML parse error" in data["error"]


def test_api_config_get_yaml_error(temp_project):
    """Test GET /api/config handles invalid YAML."""
    app = create_app(temp_project)
    client = app.test_client()

    (temp_project / "conceptual.yml").write_text("invalid: [\nyaml: {")

    response = client.get("/api/config")
    assert response.status_code == 500
    data = response.get_json()
    assert "YAML parse error" in data["error"]


def test_api_models_get_file_error(temp_project, monkeypatch):
    """Test GET /api/models handles file I/O errors."""
    from dbt_conceptual.scanner import DbtProjectScanner

    def scan_raises(self):
        raise OSError("Permission denied")

    monkeypatch.setattr(DbtProjectScanner, "scan", scan_raises)

    app = create_app(temp_project)
    client = app.test_client()

    response = client.get("/api/models")
    assert response.status_code == 500
    data = response.get_json()
    assert "Model scan error" in data["error"]


# ---------------------------------------------------------------------------
# run_server test
# ---------------------------------------------------------------------------


def test_run_server_signature(temp_project):
    """Test run_server has the expected function signature."""
    import inspect

    from dbt_conceptual.server import run_server

    sig = inspect.signature(run_server)
    params = list(sig.parameters.keys())
    assert "project_dir" in params
    assert "host" in params
    assert "port" in params
    assert "demo_mode" in params


def test_run_server_calls_waitress(temp_project):
    """Test run_server creates the app and calls waitress.serve."""
    import sys
    from types import ModuleType
    from unittest.mock import MagicMock

    from dbt_conceptual.server import run_server

    # Create a mock waitress module since it may not be installed
    mock_waitress = ModuleType("waitress")
    mock_serve = MagicMock()
    mock_waitress.serve = mock_serve  # type: ignore[attr-defined]

    with patch.dict(sys.modules, {"waitress": mock_waitress}):
        run_server(temp_project, host="0.0.0.0", port=9999, demo_mode=True)

    mock_serve.assert_called_once()
    call_kwargs = mock_serve.call_args
    assert call_kwargs[1]["host"] == "0.0.0.0"
    assert call_kwargs[1]["port"] == 9999
