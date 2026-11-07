# Quick Start Guide

Get the Document Intelligence Platform running in 2 minutes!

## 🚀 Fastest Way to Start

### Windows Users
```bash
# Double-click or run:
start_full_app.bat
```

### All Platforms
```bash
# Terminal 1 - Backend
python start_backend_venv.py

# Terminal 2 - Frontend  
python start_frontend_npm.py
```

## 📱 Access Your App

Once both servers are running:

- **Main App**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## ⚡ First Time Setup

### 1. Install Prerequisites
- Python 3.8+ 
- Node.js 16+
- npm

### 2. Setup Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Setup Frontend
```bash
cd frontend
npm install
```

### 4. Configure Environment
- Copy `backend/.env.example` to `backend/.env`
- Add your API keys

## 🧪 Test Everything Works

```bash
python test_port_8000.py
```

## 🎯 What You Get

- ✅ Upload documents (PDF, DOCX, images, code files)
- ✅ Ask AI questions about your documents
- ✅ Multiple AI models (Llama, DeepSeek, Qwen)
- ✅ Dark/light mode interface
- ✅ Real-time processing
- ✅ Model performance analytics

## 🆘 Need Help?

1. **Backend won't start**: Check virtual environment and API keys
2. **Frontend won't start**: Run `npm install` in frontend directory
3. **Port conflicts**: Kill processes on ports 3000/8000
4. **API errors**: Verify backend is running on port 8000

See `LOCAL_SETUP.md` for detailed troubleshooting.

---

**That's it!** Your Document Intelligence Platform is ready to use! 🎉