#!/usr/bin/env python3
"""
Start frontend using npm
"""
import subprocess
import sys
import os

def check_npm():
    """Check if npm is available"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm found: {result.stdout.strip()}")
            return True
        else:
            print("❌ npm not found!")
            return False
    except FileNotFoundError:
        print("❌ npm not found!")
        return False

def start_frontend():
    """Start the React frontend using npm"""
    try:
        print("🌐 Starting Document Intelligence Platform Frontend...")
        print()
        
        # Check npm
        if not check_npm():
            print("   Please install Node.js and npm first")
            return False
        
        # Get the frontend directory
        frontend_path = os.path.join(os.getcwd(), 'frontend')
        
        if not os.path.exists(frontend_path):
            print("❌ Frontend directory not found!")
            return False
        
        if not os.path.exists(os.path.join(frontend_path, 'package.json')):
            print("❌ package.json not found in frontend directory!")
            return False
        
        print("✅ Frontend directory found")
        print("📦 Installing/updating dependencies...")
        
        # Install dependencies
        install_result = subprocess.run(['npm', 'install'], cwd=frontend_path)
        
        if install_result.returncode != 0:
            print("❌ npm install failed!")
            return False
        
        print("✅ Dependencies installed")
        print("🚀 Starting React development server...")
        print()
        print("📱 Frontend will be available at: http://localhost:3000")
        print("🔗 Backend proxy configured for: http://localhost:8000")
        print()
        
        # Start React development server
        subprocess.run(['npm', 'start'], cwd=frontend_path)
        
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped by user")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_frontend()