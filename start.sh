#!/bin/bash

# Product Price Monitoring System - Unix Startup Script

echo "========================================"
echo "Product Price Monitoring System"
echo "========================================"
echo ""

# Check if running from correct directory
if [ ! -d "backend" ]; then
    echo "Error: backend directory not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Start Backend
echo "Starting backend server..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start Frontend
cd ../frontend
echo "Starting frontend development server..."
npm install
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "Servers Starting..."
echo "========================================"
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop servers..."

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
