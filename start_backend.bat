@echo off
echo Starting Document Intelligence Platform Backend...
echo.

cd backend

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting backend server on http://localhost:8000...
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause