#!/bin/bash
# ==============================================================================
# Helper Script to Launch the Short Video Maker Server Locally
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$DIR/short-video-maker-repo"

# Load environment variables from .env if present
if [ -f "$DIR/.env" ]; then
    export $(grep -v '^#' "$DIR/.env" | xargs)
fi

echo "========================================================"
echo "🚀 Launching Short Video Maker Server (Port 3123)"
echo "========================================================"

if [ -z "$PEXELS_API_KEY" ]; then
    echo "⚠️  WARNING: PEXELS_API_KEY is not set in environment or .env."
    echo "   Stock video downloads will use fallback clips."
    echo "   Get a free key at https://www.pexels.com/api/"
fi

# Option 1: If Docker is installed and running
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "🐳 Starting with Docker container (latest-tiny)..."
    docker run -it --rm \
        --name short-video-maker \
        -p 3123:3123 \
        -e LOG_LEVEL=info \
        -e PEXELS_API_KEY="$PEXELS_API_KEY" \
        gyoridavid/short-video-maker:latest-tiny
    exit 0
fi

# Option 2: Run natively via Node.js
if command -v node &> /dev/null; then
    echo "📦 Starting natively with Node.js in $REPO_DIR..."
    cd "$REPO_DIR" || exit 1
    
    if [ ! -d "node_modules" ]; then
        echo "Installing Node dependencies (this only happens once)..."
        npm install
    fi
    
    export PORT=3123
    export LOG_LEVEL=info
    export PEXELS_API_KEY="$PEXELS_API_KEY"
    
    npm run dev
    exit 0
fi

echo "❌ Neither Docker nor Node.js were found on this system."
echo "   Please install Node.js (v20+) or Docker Desktop."
exit 1
