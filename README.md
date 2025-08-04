# 📚 DocuMind AI - Intelligent Document Analysis Platform

A comprehensive document intelligence platform powered by multiple AI models. Upload any document and get instant insights with advanced question generation, multi-format support, and intelligent model selection. Built with **Nebius AI Studio**, **Tesseract OCR**, **FastAPI**, and **React**.

![Document Q&A Demo](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18+-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)

## ✨ Features

### 🤖 **Multi-Model AI Intelligence**
- **Meta Llama 3.1**: General-purpose analysis and conversation
- **DeepSeek R1**: Complex reasoning and research analysis  
- **Qwen3 Coder**: Advanced code analysis and technical documentation
- **Smart Model Recommendation**: Automatic model selection based on content type
- **Manual Override**: Users can select any model for any document type

### 📁 **Comprehensive File Support**
- **Documents**: PDF, DOCX, TXT, MD, HTML, XML
- **Code Files**: Python, JavaScript, TypeScript, Java, C++, C, Shell, CSS, JSON
- **Jupyter Notebooks**: Full .ipynb support with enhanced cell extraction
- **Images**: JPG, PNG, GIF, BMP, TIFF, WebP (with OCR)
- **Data Files**: CSV, JSON

### 🎯 **Smart Question Generation**
- **AI-Generated Questions**: Contextually relevant questions based on document content
- **8 Question Categories**: Factual, Analytical, Summary, Technical, Strategic, Debugging, Optimization, Implementation
- **Question Management**: Save favorites, view history, bulk operations
- **Click-to-Use**: One-click question population with collapsible interface

### 📊 **Advanced Features**
- **Enhanced Text Extraction**: Improved Jupyter notebook processing with comprehensive output analysis
- **Export Options**: Download answers, extracted text, or complete analysis
- **Model Comparison**: Compare responses from different AI models
- **Performance Tracking**: Model usage statistics and intelligent recommendations
- **Responsive Design**: Optimized layout that scales from mobile to desktop

### 🎨 Modern Interface
- **Drag & drop upload**: Intuitive file handling
- **Real-time processing**: Live feedback during document analysis
- **Responsive design**: Works on desktop and mobile
- **Clean UI**: Modern, professional interface

### 🔧 Developer Features
- **RESTful API**: Easy integration with other systems
- **Debug endpoints**: Inspect raw OCR output
- **Extensible architecture**: Easy to add new features
- **Type safety**: Full TypeScript support in frontend

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 16+
- Tesseract OCR installed
- Nebius AI Studio API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd docqa-app
   ```

2. **Backend Setup**
   ```bash
   cd backend
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   # Create .env file in backend directory
   echo "NEBIUS_API_KEY=your_nebius_api_key_here" > .env
   ```

4. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the Application

1. **Start the Backend Server**
   ```bash
   cd backend
   venv\Scripts\activate  # Windows
   python -m uvicorn main_temp:app --reload --host 0.0.0.0 --port 8000
   ```
   Server will run on `http://localhost:8000`

2. **Start the Frontend**
   ```bash
   cd frontend
   npm start
   ```
   Application will open on `http://localhost:3000`

## 📋 Supported File Formats

| Category | Formats | Notes |
|----------|---------|-------|
| **Images** | JPG, JPEG, PNG, BMP, TIFF, GIF | OCR processing with advanced preprocessing |
| **Documents** | PDF, DOCX, TXT | Smart text extraction with OCR fallback |
| **Scanned PDFs** | PDF | Automatic OCR when direct text extraction fails |

## 🔑 API Endpoints

### Main Endpoints
- `POST /ask` - Upload document and ask questions
- `POST /debug-extract` - Debug text extraction
- `GET /supported-formats` - Get supported file formats

### Example Usage
```python
import requests

# Upload and ask question
files = {'file': open('document.pdf', 'rb')}
data = {
    'question': 'What is the course code?',
    'system_prompt': 'Be precise and extract exact information.'
}

response = requests.post('http://localhost:8000/ask', files=files, data=data)
result = response.json()
print(result['answer'])
```

## 🛠️ Configuration

### Tesseract OCR Setup
**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location: `C:\Program Files\Tesseract-OCR\`
3. Path is automatically configured in the application

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### Nebius AI Studio API Key
1. Sign up at [Nebius AI Studio](https://studio.nebius.com/)
2. Generate an API key
3. Add to your `.env` file:
   ```
   NEBIUS_API_KEY=your_api_key_here
   ```

## 🏗️ Architecture

```
docqa-app/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application file
│   ├── requirements.txt    # Python dependencies
│   ├── .env               # Environment variables (create this)
│   └── venv/              # Virtual environment
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   └── App.css        # Styling
│   ├── package.json       # Node dependencies
│   └── build/             # Production build
└── README.md              # This file
```

## 🔧 Development

### Adding New Features
1. Backend changes go in `backend/main.py`
2. Frontend changes go in `frontend/src/App.tsx`
3. Always test both components after changes

### OCR Improvements
The OCR system uses multiple preprocessing techniques:
- CLAHE contrast enhancement
- Bilateral filtering
- Adaptive thresholding
- Morphological operations
- Multiple PSM modes for different document types

### AI Model Configuration
Currently using Meta-Llama-3.1-70B-Instruct via Nebius AI Studio:
- Temperature: 0.6 (balanced creativity/accuracy)
- Max tokens: 1024
- Top-p: 0.9

## 🐛 Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'PyPDF2'"**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**"Tesseract not found"**
- Install Tesseract OCR
- Verify installation path in `main.py`

**"API key not found"**
- Create `.env` file in backend directory
- Add your Nebius API key

**Empty OCR results**
- Check if Tesseract is properly installed
- Verify image quality and format
- Try different document types

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🙏 Acknowledgments

- **Nebius AI Studio** for powerful language model API
- **Tesseract OCR** for text extraction capabilities
- **FastAPI** for the robust backend framework
- **React** for the modern frontend interface

---


## 🌟 Star this repository if you found it helpful!

[![GitHub stars](https://img.shields.io/github/stars/PratikCreates/docqa-app?style=social)](https://github.com/PratikCreates/docqa-app/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/PratikCreates/docqa-app?style=social)](https://github.com/PratikCreates/docqa-app/network/members)

---

**Repository**: https://github.com/PratikCreates/docqa-app  
**Author**: [@PratikCreates](https://github.com/PratikCreates)