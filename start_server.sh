#!/bin/bash
# Start local server for portfolio and experiments
# This starts both the frontend (port 8000) and Flask API (port 5000)

# Get the directory where this script is located (must be first!)
DIR="$(cd "$(dirname "$0")" && pwd)"

PORT=8000
API_PORT=5000

echo "Starting Portfolio & Experiments Lab..."
echo ""

# Kill any existing servers on our ports to prevent conflicts
echo "Cleaning up old servers..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null
lsof -ti:$API_PORT | xargs kill -9 2>/dev/null
sleep 1


# Check and install Flask dependencies if needed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask API dependencies..."
    pip3 install -q -r "$DIR/api/requirements.txt"
fi

# Start Flask API server in background
echo "Starting API server at http://localhost:$API_PORT"
(cd "$DIR/api" && python3 server.py) > /tmp/flask_api.log 2>&1 &
API_PID=$!

# Give API a moment to start
sleep 2

# Check if API started successfully
if ! curl -s http://localhost:$API_PORT/api/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Flask API may not have started. Check /tmp/flask_api.log for errors."
fi


# Start frontend server
echo "Starting frontend server at http://localhost:$PORT"
echo ""
echo "✅ Portfolio is now running!"
echo ""
echo "  🌐 Frontend:    http://localhost:$PORT"
echo "  🔧 API Server:  http://localhost:$API_PORT"
echo "  🧪 Experiments: http://localhost:$PORT/experiments.html"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Open browser after a slight delay
(sleep 1 && open "http://localhost:$PORT/") &

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $API_PID 2>/dev/null
    exit 0
}


trap cleanup INT

# Start the custom frontend server (auto-serves index.html)
cd "$DIR" && python3 server.py
