#!/bin/bash
# =============================================================================
# post-create.sh - Devcontainer post-create setup for dbt-conceptual
# =============================================================================
# Installs the project in development mode with all dependencies.
#
# This script is idempotent - safe to run multiple times.
# =============================================================================
set -e

echo "=== Post-create setup starting ==="

# Install project with all development dependencies
echo "Installing dbt-conceptual with all dependencies..."
pip install --no-cache-dir -e ".[all]"

# Configure Starship
echo "Configuring Starship prompt..."
mkdir -p ~/.config
cp .devcontainer/starship.toml ~/.config/starship.toml

# Verify installations
echo ""
echo "=== Verifying installations ==="
echo -n "gh: "; gh --version | head -1
echo -n "python: "; python --version
echo -n "dbt-conceptual: "; dbt-conceptual --version || echo "(installed)"
echo -n "pytest: "; pytest --version
echo -n "ruff: "; ruff --version
echo -n "black: "; black --version

echo ""
echo "=== Post-create setup complete ==="
