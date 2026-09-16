#!/bin/bash
# QA Test Script for Portfolio + Experiments Lab

echo "=== QA Testing Portfolio & Experiments Lab ==="
echo ""

# Colors
GREEN='\033[0.32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Start servers
echo "1. Starting servers..."
./start_server.sh > /tmp/qa_startup.log 2>&1 &
STARTUP_PID=$!

# Wait for servers to start
sleep 5

# Test 1: Frontend Server
echo -n "2. Testing frontend server (port 8000)... "
if curl -s http://localhost:8000/ | grep -q "Binoy Chemmagate"; then
    echo -e "${GREEN}✓ PASSED${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

# Test 2: Flask API Health
echo -n "3. Testing Flask API health endpoint... "
if curl -s http://localhost:5000/api/health | grep -q "ok"; then
    echo -e "${GREEN}✓ PASSED${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "   Check /tmp/flask_api.log for errors"
fi

# Test 3: Experiments Page
echo -n "4. Testing experiments page... "
if curl -s http://localhost:8000/experiments.html | grep -q "ASR Benchmarking"; then
    echo -e "${GREEN}✓ PASSED${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

# Test 4: Profile Page
echo -n "5. Testing profile page... "
if curl -s http://localhost:8000/profile.html | grep -q "My Profile"; then
    echo -e "${GREEN}✓ PASSED${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

echo ""
echo "=== QA Tests Complete ==="
echo ""
echo "Servers are still running. Press Ctrl+C to stop them or run:"
echo "  pkill -f 'server.py'"
