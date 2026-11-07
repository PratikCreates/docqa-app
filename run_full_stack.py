#!/usr/bin/env python3
"""
Run both backend and frontend for the Document Intelligence Platform
"""

import subprocess
import sys
import time
import os
from pathlib import Path
import threading

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          Document Intelligence Platform - Full Stack         ║
║                    Backend + Frontend                        ║
╚══════════════════════════════════════════════════════════════╝
    """)

def run_backend():
    """Run the FastAPI backend"""
    print("🚀 Starting Backend API Server...")
    print("📊 Backend will be available at: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    
    try:
        # Change to backend directory
        backend_dir = Path('backend')
        if backend_dir.exists():
            os.chdir(backend_dir)
        
        # Start the backend server
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'main:app', 
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ])
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Backend error: {e}")

def run_frontend():
    """Run the React frontend"""
    print("⚛️  Starting React Frontend...")
    print("🌐 Frontend will be available at: http://localhost:3000")
    
    try:
        # Change to frontend directory
        frontend_dir = Path('frontend')
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            return
        
        os.chdir(frontend_dir)
        
        # Check if node_modules exists
        if not Path('node_modules').exists():
            print("📦 Installing frontend dependencies...")
            subprocess.run(['npm', 'install'], check=True)
        
        # Start the frontend server
        subprocess.run(['npm', 'start'])
        
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Frontend error: {e}")

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found. Please install from: https://nodejs.org/")
        return False
    
    # Check npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm: {result.stdout.strip()}")
        else:
            print("❌ npm not found")
            return False
    except FileNotFoundError:
        print("❌ npm not found")
        return False
    
    # Check Python
    print(f"✅ Python: {sys.version.split()[0]}")
    
    return True

def main():
    """Main function to run both servers"""
    print_banner()
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install missing tools.")
        return
    
    print("\n🎯 Starting Full Stack Document Intelligence Platform...")
    print("📝 Instructions:")
    print("   • Backend API: http://localhost:8000")
    print("   • Frontend UI: http://localhost:3000")
    print("   • API Docs: http://localhost:8000/docs")
    print("   • Press Ctrl+C to stop both servers")
    print("\n" + "="*60)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend in main thread
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down full stack platform...")
        print("👋 Thanks for using Document Intelligence Platform!")

if __name__ == "__main__":
    main()