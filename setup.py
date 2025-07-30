#!/usr/bin/env python3
"""
Setup script for Smart Document Q&A System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_node_version():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f"✅ Node.js {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Node.js is not installed")
        return False

def setup_backend():
    """Setup backend environment"""
    print("\n🔧 Setting up backend...")
    
    backend_dir = Path("backend")
    venv_dir = backend_dir / "venv"
    
    # Create virtual environment
    if not venv_dir.exists():
        if not run_command("python -m venv venv", cwd=backend_dir):
            return False
    
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = venv_dir / "Scripts" / "activate.bat"
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        activate_script = venv_dir / "bin" / "activate"
        pip_path = venv_dir / "bin" / "pip"
    
    # Install requirements
    if not run_command(f'"{pip_path}" install -r requirements.txt', cwd=backend_dir):
        return False
    
    # Check if .env exists
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("⚠️  Please create backend/.env file with your NEBIUS_API_KEY")
        print("   Copy backend/.env.example and add your API key")
    
    return True

def setup_frontend():
    """Setup frontend environment"""
    print("\n🎨 Setting up frontend...")
    
    frontend_dir = Path("frontend")
    
    # Install npm dependencies
    if not run_command("npm install", cwd=frontend_dir):
        return False
    
    return True

def check_tesseract():
    """Check if Tesseract OCR is installed"""
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        print(f"✅ Tesseract OCR installed")
        return True
    except FileNotFoundError:
        print("❌ Tesseract OCR is not installed")
        print("   Please install from: https://github.com/UB-Mannheim/tesseract/wiki")
        return False

def main():
    """Main setup function"""
    print("🚀 Smart Document Q&A System Setup")
    print("=" * 40)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    checks = [
        check_python_version(),
        check_node_version(),
        check_tesseract()
    ]
    
    if not all(checks):
        print("\n❌ Please install missing prerequisites and run setup again")
        return False
    
    # Setup backend
    if not setup_backend():
        print("\n❌ Backend setup failed")
        return False
    
    # Setup frontend
    if not setup_frontend():
        print("\n❌ Frontend setup failed")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Add your NEBIUS_API_KEY to backend/.env")
    print("2. Start backend: cd backend && venv/Scripts/activate && python -m uvicorn main:app --reload")
    print("3. Start frontend: cd frontend && npm start")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)