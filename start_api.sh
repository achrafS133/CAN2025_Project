#!/bin/bash

# CAN 2025 Guardian API - Startup Script

echo "🛡️  CAN 2025 Guardian API"
echo "=========================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠ Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "⚠ Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "⚠ Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Create necessary directories
mkdir -p logs data

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠ Warning: .env file not found. Using defaults."
    echo "  Create .env file from .env.example for production."
fi

# Start the API server
echo ""
echo "🚀 Starting FastAPI server..."
echo "📍 API will be available at: http://localhost:8888"
echo "📖 API Documentation: http://localhost:8888/api/docs"
echo "📊 Health Check: http://localhost:8888/health"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================="
echo ""

# Start uvicorn with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8888
