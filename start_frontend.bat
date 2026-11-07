@echo off
echo Starting Document Intelligence Platform Frontend...
echo.

cd frontend

echo Installing/updating dependencies...
call npm install

echo Starting React development server...
call npm start

pause