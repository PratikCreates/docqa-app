@echo off
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          Document Intelligence Platform - Full Stack         ║
echo ║                    Backend + Frontend                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo Starting backend server...
start "Backend Server" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo Starting frontend server...
start "Frontend Server" cmd /k "cd frontend && npm start"

echo.
echo ✅ Both servers are starting...
echo.
echo 📱 Application URLs:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window...
pause > nul