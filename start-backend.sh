#!/bin/bash
echo "Starting Smart Document Q&A Backend..."
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000