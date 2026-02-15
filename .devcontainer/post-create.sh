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

# Install MesloLGM Nerd Font Mono (for Starship glyphs in terminal)
echo "Installing MesloLGM Nerd Font Mono..."
FONT_DIR="/usr/share/fonts/truetype/meslo"
if [ ! -d "$FONT_DIR" ]; then
    mkdir -p "$FONT_DIR"
    curl -fsSL -o /tmp/MesloLGM.zip \
        "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/Meslo.zip"
    unzip -qo /tmp/MesloLGM.zip -d "$FONT_DIR"
    rm -f /tmp/MesloLGM.zip
    fc-cache -f "$FONT_DIR" 2>/dev/null || true
    echo "  Font installed to $FONT_DIR"
else
    echo "  Font already installed"
fi

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
