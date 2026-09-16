#!/bin/bash
# Start the Experiments Lab (Frontend + API Server)

echo "Starting Experiments Lab..."
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask API dependencies..."
    pip3 install -r api/requirements.txt
fi

# Start Flask API server in background
echo "Starting Flask API server on port 5000..."
cd api && python3 server.py &
API_PID=$!
cd ..

# Wait a moment for API to start
sleep 2

# Start frontend server
echo "Starting frontend server on port 8000..."
python3 -m http.server 8000 &
FRONTEND_PID=$!

echo ""
echo "✅ Experiments Lab is now running!"
echo ""
echo "  Frontend:  http://localhost:8000/experiments.html"
echo "  API:       http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "kill $API_PID $FRONTEND_PID; exit" INT
wait
