# Local Setup Guide

This guide will help you set up the Document Intelligence Platform locally using virtual environment and npm.

## Quick Start (Recommended)

### Option 1: Windows Batch Files
```bash
# Start both servers automatically
start_full_app.bat

# Or start individually
start_backend.bat    # Backend on port 8000
start_frontend.bat   # Frontend on port 3000
```

### Option 2: Python Scripts (Cross-platform)
```bash
# Start backend with virtual environment
python start_backend_venv.py

# Start frontend with npm (in another terminal)
python start_frontend_npm.py
```

### Option 3: Manual Commands
```bash
# Backend
cd backend
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac
python -m uvicorn main:app --reload

# Frontend (in another terminal)
cd frontend
npm start
```

## Access Points

- **React Frontend**: http://localhost:3000
- **Simple Frontend**: http://localhost:3000/simple_frontend.html (if using static server)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Prerequisites

### Required
- Python 3.8+
- Node.js 16+
- npm

### Setup Virtual Environment (First Time)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Setup Frontend Dependencies (First Time)
```bash
cd frontend
npm install
```

## Environment Configuration

1. **Backend Environment**:
   - Copy `backend/.env.example` to `backend/.env`
   - Add your API keys (NEBIUS_API_KEY, etc.)

2. **Frontend Proxy**:
   - Already configured in `frontend/package.json`
   - Proxies API calls to `http://localhost:8000`

## Features

- ✅ Document upload and processing
- ✅ AI-powered question answering
- ✅ Multiple AI model support
- ✅ Dark mode interface
- ✅ Real-time processing
- ✅ Model performance metrics
- ✅ React frontend with TypeScript
- ✅ Virtual environment isolation

## Testing

### Test Backend
```bash
python test_port_8000.py  # Test backend on port 8000
python test_fixes.py      # Test all applied fixes
```

## Troubleshooting

### Backend Issues
- Ensure virtual environment is activated
- Check if port 8000 is available
- Verify API keys in `.env` file
- Check Python dependencies are installed

### Frontend Issues
- Ensure npm dependencies are installed (`npm install`)
- Check if port 3000 is available
- Verify backend is running on port 8000
- Check browser console for errors

### Common Solutions
- **Port conflicts**: Kill processes using ports 3000/8000
- **Dependencies**: Run `pip install -r requirements.txt` and `npm install`
- **Environment**: Ensure `.env` file exists with valid API keys
- **Virtual environment**: Make sure it's activated before starting backend

## Development Workflow

1. **First time setup**:
   ```bash
   # Setup backend
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   
   # Setup frontend
   cd ../frontend
   npm install
   ```

2. **Daily development**:
   ```bash
   # Quick start
   start_full_app.bat
   
   # Or manual
   python start_backend_venv.py  # Terminal 1
   python start_frontend_npm.py  # Terminal 2
   ```

## Architecture

- **Backend**: FastAPI with uvicorn (port 8000)
- **Frontend**: React with TypeScript (port 3000)
- **Proxy**: React dev server proxies `/api/*` to backend
- **AI**: Multiple model support with fallback
- **Storage**: File upload with multiple format support