# 📁 Project Structure

```
docqa-app/
├── 📄 README.md                    # Main documentation
├── 📄 .gitignore                   # Git ignore rules
├── 📄 setup.py                     # Automated setup script
├── 📄 PROJECT_STRUCTURE.md         # This file
├── 
├── 🚀 Start Scripts
├── ├── start-backend.bat           # Windows backend starter
├── ├── start-backend.sh            # Unix/Linux backend starter
├── ├── start-frontend.bat          # Windows frontend starter
├── └── start-frontend.sh           # Unix/Linux frontend starter
├── 
├── 🔧 Backend (FastAPI + Python)
├── ├── 📄 main.py                  # Main FastAPI application
├── ├── 📄 requirements.txt         # Python dependencies
├── ├── 📄 .env.example             # Environment template
├── ├── 📄 .env                     # Your API keys (create this)
├── └── 📁 venv/                    # Virtual environment
├── 
└── 🎨 Frontend (React + TypeScript)
    ├── 📄 package.json             # Node.js dependencies
    ├── 📄 tsconfig.json            # TypeScript configuration
    ├── 📁 src/
    │   ├── 📄 App.tsx              # Main React component
    │   ├── 📄 App.css              # Styling
    │   └── 📄 index.tsx            # React entry point
    ├── 📁 public/                  # Static assets
    └── 📁 build/                   # Production build (generated)
```

## 🔑 Key Files

### Backend Files
- **`main.py`**: Core FastAPI application with OCR and AI integration
- **`requirements.txt`**: All Python dependencies including FastAPI, OpenCV, Tesseract, etc.
- **`.env`**: Your Nebius API key (create from `.env.example`)

### Frontend Files
- **`App.tsx`**: Main React component with file upload and Q&A interface
- **`App.css`**: Modern styling with gradients and responsive design
- **`package.json`**: React dependencies and scripts

### Setup Files
- **`setup.py`**: Automated setup script for both backend and frontend
- **`start-*.bat/sh`**: Quick start scripts for development

## 🛠️ Development Workflow

1. **Initial Setup**: Run `python setup.py`
2. **Backend Development**: Use `start-backend.bat` or modify `backend/main.py`
3. **Frontend Development**: Use `start-frontend.bat` or modify `frontend/src/App.tsx`
4. **Git Management**: All sensitive files are in `.gitignore`

## 🔒 Security Features

- Environment variables for API keys
- File size limits (10MB max)
- Input validation
- CORS configuration
- Proper error handling
- No sensitive data in git

## 📦 Dependencies

### Backend (Python)
- FastAPI: Web framework
- OpenCV: Image processing
- Tesseract: OCR engine
- PyMuPDF: PDF processing
- OpenAI: AI model client
- Pillow: Image handling

### Frontend (React)
- TypeScript: Type safety
- Modern CSS: Responsive design
- File upload: Drag & drop support
- Real-time feedback: Loading states

## 🚀 Deployment Ready

The project structure supports easy deployment to:
- **Backend**: Any Python hosting (Heroku, Railway, DigitalOcean)
- **Frontend**: Static hosting (Vercel, Netlify, GitHub Pages)
- **Docker**: Ready for containerization
- **Cloud**: AWS, GCP, Azure compatible