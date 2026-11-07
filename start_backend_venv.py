#!/usr/bin/env python3
"""
Start backend using virtual environment
"""
import subprocess
import sys
import os
import platform

def start_backend():
    """Start the backend server using virtual environment"""
    try:
        print("🚀 Starting Document Intelligence Platform Backend...")
        print()
        
        # Get the backend directory
        backend_path = os.path.join(os.getcwd(), 'backend')
        
        if not os.path.exists(backend_path):
            print("❌ Backend directory not found!")
            return False
        
        # Check if virtual environment exists
        if platform.system() == "Windows":
            venv_activate = os.path.join(backend_path, 'venv', 'Scripts', 'activate.bat')
            python_exe = os.path.join(backend_path, 'venv', 'Scripts', 'python.exe')
        else:
            venv_activate = os.path.join(backend_path, 'venv', 'bin', 'activate')
            python_exe = os.path.join(backend_path, 'venv', 'bin', 'python')
        
        if not os.path.exists(python_exe):
            print("❌ Virtual environment not found!")
            print("   Please create it with: python -m venv backend/venv")
            print("   Then install requirements: pip install -r backend/requirements.txt")
            return False
        
        print("✅ Virtual environment found")
        print("🔄 Starting backend server on http://localhost:8000...")
        
        # Start uvicorn server using virtual environment python
        cmd = [
            python_exe, '-m', 'uvicorn', 
            'main:app', 
            '--reload',
            '--host', '0.0.0.0', 
            '--port', '8000'
        ]
        
        print(f"📍 Working directory: {backend_path}")
        print(f"🚀 Command: {' '.join(cmd)}")
        print()
        
        # Start the process
        subprocess.run(cmd, cwd=backend_path)
        
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped by user")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_backend()