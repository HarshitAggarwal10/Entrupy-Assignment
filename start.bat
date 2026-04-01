@echo off
REM Product Price Monitoring System - Windows Startup Script

echo.
echo ========================================
echo Product Price Monitoring System
echo ========================================
echo.

REM Check if running from correct directory
if not exist "backend" (
    echo Error: backend directory not found
    echo Please run this script from the project root directory
    exit /b 1
)

REM Start Backend
echo Starting backend server...
start cmd /k "cd backend && python -m venv venv && call venv\Scripts\activate && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000"

REM Wait for backend to start
timeout /t 5

REM Start Frontend
echo Starting frontend development server...
start cmd /k "cd frontend && npm install && npm run dev"

echo.
echo ========================================
echo Servers Starting...
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window...
pause
