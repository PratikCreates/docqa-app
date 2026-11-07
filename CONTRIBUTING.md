# 🤝 Contributing to DocuMind AI

Thank you for your interest in contributing to DocuMind AI! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 16+
- Git
- Tesseract OCR
- Nebius AI Studio API key

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/PratikCreates/docqa-app.git
   cd docqa-app
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Environment Configuration**
   ```bash
   # Create backend/.env
   NEBIUS_API_KEY=your_api_key_here
   ```

## 📋 How to Contribute

### 🐛 Bug Reports
- Use the GitHub issue tracker
- Include detailed reproduction steps
- Provide system information (OS, Python version, etc.)
- Include error logs and screenshots

### ✨ Feature Requests
- Check existing issues first
- Provide clear use case and rationale
- Include mockups or examples if applicable
- Discuss implementation approach

### 🔧 Code Contributions

#### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation updates

#### Pull Request Process
1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Add tests for new functionality
4. Update documentation as needed
5. Submit a pull request with detailed description

#### Code Style
- **Python**: Follow PEP 8 guidelines
- **TypeScript/React**: Use ESLint and Prettier
- **Commit Messages**: Use conventional commits format

## 🧪 Testing

### Running Tests
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test

# Integration tests
python test_complete_ux.py
```

### Test Coverage
- Aim for >80% code coverage
- Include unit tests for new functions
- Add integration tests for API endpoints
- Test UI components and user flows

## 📁 Project Structure

```
docqa-app/
├── backend/                 # FastAPI backend
│   ├── main_temp.py        # Main application (ACTIVE)
│   ├── services/           # Business logic services
│   ├── models/             # Data models and AI configurations
│   └── middleware/         # API middleware
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   └── App.css        # Styling
│   └── public/            # Static assets
├── .kiro/specs/           # Feature specifications
├── test_files/            # Test documents
└── docs/                  # Documentation
```

## 🎯 Development Guidelines

### Backend Development
- Use `main_temp.py` as the main application file
- Follow FastAPI best practices
- Implement proper error handling
- Add type hints for all functions
- Use async/await for I/O operations

### Frontend Development
- Use TypeScript for type safety
- Follow React hooks patterns
- Implement responsive design
- Add proper error boundaries
- Use semantic HTML and accessibility features

### AI Model Integration
- Test with all supported models (Meta Llama, DeepSeek, Qwen3)
- Handle model failures gracefully
- Implement proper fallback mechanisms
- Monitor performance and accuracy

## 🔒 Security Guidelines

- Never commit API keys or secrets
- Validate all user inputs
- Implement proper file upload restrictions
- Use HTTPS in production
- Follow OWASP security guidelines

## 📖 Documentation

### Code Documentation
- Add docstrings to all functions
- Include type hints and parameter descriptions
- Document complex algorithms and business logic
- Update API documentation for new endpoints

### User Documentation
- Update README.md for new features
- Add examples and use cases
- Include troubleshooting guides
- Update installation instructions

## 🏷️ Release Process

### Version Numbering
- Follow Semantic Versioning (SemVer)
- Major.Minor.Patch format
- Use beta/alpha tags for pre-releases

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers bumped
- [ ] Security review completed
- [ ] Performance testing done

## 🤔 Questions?

- Check existing issues and discussions
- Join our community discussions
- Contact maintainers for complex questions
- Read the documentation thoroughly

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to DocuMind AI!** 🚀

Your contributions help make document intelligence accessible to everyone.