#!/usr/bin/env python3
"""
Script to start both backend and frontend services
"""
import subprocess
import sys
import os
import time
import threading

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting Backend Service...")
    backend_dir = os.path.join(os.getcwd(), 'backend')
    
    if not os.path.exists(backend_dir):
        print("❌ Backend directory not found!")
        return
    
    try:
        # Change to backend directory and start uvicorn
        os.chdir(backend_dir)
        subprocess.run([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend service stopped")
    except Exception as e:
        print(f"❌ Backend failed to start: {e}")

def start_frontend():
    """Start the React frontend"""
    print("🚀 Starting Frontend Service...")
    frontend_dir = os.path.join(os.getcwd(), 'frontend')
    
    if not os.path.exists(frontend_dir):
        print("❌ Frontend directory not found!")
        return
    
    try:
        # Change to frontend directory and start npm
        os.chdir(frontend_dir)
        subprocess.run(["npm", "start"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Frontend service stopped")
    except Exception as e:
        print(f"❌ Frontend failed to start: {e}")

def main():
    print("🎯 DocQA App - Multi-Model AI Document Analysis")
    print("=" * 50)
    
    choice = input("""
Choose an option:
1. Start Backend only (FastAPI on port 8000)
2. Start Frontend only (React on port 3000)  
3. Start Both services
4. Fix dependencies first

Enter choice (1-4): """).strip()
    
    if choice == "1":
        start_backend()
    elif choice == "2":
        start_frontend()
    elif choice == "3":
        print("🚀 Starting both services...")
        print("📝 Backend will start on http://localhost:8000")
        print("🌐 Frontend will start on http://localhost:3000")
        print("\n⚠️  Note: Start backend first, then frontend in separate terminals")
        print("\nStarting backend...")
        start_backend()
    elif choice == "4":
        print("🔧 Running dependency fix...")
        try:
            subprocess.run([sys.executable, "fix_dependencies.py"], check=True)
        except Exception as e:
            print(f"❌ Dependency fix failed: {e}")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()