#!/bin/bash
set -e

echo "🔨 Building dbt-conceptual frontend..."

# Check if nvm is available
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    export NVM_DIR="$HOME/.nvm"
    \. "$NVM_DIR/nvm.sh"
fi

# Check if node is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ first."
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install npm first."
    exit 1
fi

echo "📦 Node version: $(node --version)"
echo "📦 npm version: $(npm --version)"

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Install dependencies
echo "📥 Installing dependencies..."
npm install

# Build
echo "🏗️  Building frontend..."
npm run build

echo "✅ Frontend built successfully!"
echo "📂 Static files available at: src/dbt_conceptual/static/"
