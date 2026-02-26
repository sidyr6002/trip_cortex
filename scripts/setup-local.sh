#!/bin/bash
# Local Development Setup Script for Trip Cortex
# Automates one-time setup of local development environment

set -e  # Exit on error

echo "🚀 Trip Cortex - Local Development Setup"
echo "=========================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python 3.12
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 not found. Please install Python 3.12+"
    exit 1
fi
echo "✓ Python 3.12 found"

# Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo "✓ uv found"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop"
    exit 1
fi
echo "✓ Docker found"

# Check Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose"
    exit 1
fi
echo "✓ Docker Compose found"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop"
    exit 1
fi
echo "✓ Docker daemon running"

echo ""
echo "📦 Installing Python dependencies..."
uv sync

echo ""
echo "📄 Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env from .env.example"
    echo "⚠️  Please edit .env with your local configuration"
else
    echo "✓ .env already exists"
fi

echo ""
echo "🐳 Starting Docker services..."
docker compose up -d --wait

echo ""
echo "✅ Docker services are healthy!"

echo ""
echo "✅ Local development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your configuration (if needed)"
echo "  2. Run tests: uv run pytest tests/unit/ -v"
echo "  3. Start coding!"
echo ""
echo "Useful commands:"
echo "  • View logs: docker compose logs -f"
echo "  • Stop services: docker compose down"
echo "  • Restart services: docker compose restart"
echo ""
