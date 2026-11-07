#!/usr/bin/env python3
"""
Frontend starter script for Document Intelligence Platform
"""
import subprocess
import sys
import os
import shutil

def check_prerequisites():
    """Check if Node.js and npm are installed"""
    node_version = None
    npm_version = None
    
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            node_version = result.stdout.strip()
            print(f"✅ Node.js found: {node_version}")
        else:
            print("❌ Node.js not found!")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found!")
        return False
    
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            npm_version = result.stdout.strip()
            print(f"✅ npm found: {npm_version}")
        else:
            print("❌ npm not found!")
            return False
    except FileNotFoundError:
        print("❌ npm not found!")
        return False
    
    return True

def start_react_frontend():
    """Start the React development server"""
    try:
        frontend_path = os.path.join(os.getcwd(), 'frontend')
        
        if not os.path.exists(frontend_path):
            print("❌ Frontend directory not found!")
            return False
        
        print("📦 Installing dependencies...")
        install_result = subprocess.run(['npm', 'install'], cwd=frontend_path, capture_output=True, text=True)
        
        if install_result.returncode != 0:
            print(f"❌ npm install failed: {install_result.stderr}")
            return False
        
        print("🚀 Starting React development server...")
        subprocess.run(['npm', 'start'], cwd=frontend_path)
        
    except Exception as e:
        print(f"❌ Error starting React frontend: {e}")
        return False

def start_simple_frontend():
    """Start simple HTTP server for static files"""
    try:
        print("🌐 Starting simple HTTP server on port 3000...")
        subprocess.run([sys.executable, '-m', 'http.server', '3000'])
    except Exception as e:
        print(f"❌ Error starting simple frontend: {e}")
        return False

def main():
    """Main function"""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          Document Intelligence Platform - Frontend           ║")
    print("║                    React Development Server                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    print("🔍 Checking prerequisites...")
    
    if check_prerequisites():
        print("\n✅ All prerequisites met!")
        print("🚀 Starting React frontend...")
        start_react_frontend()
    else:
        print("\n❌ Prerequisites not met. Please install Node.js and npm first.")
        print("\n💡 Alternative: You can use the simple HTML frontend:")
        print("   python -m http.server 3000")
        print("   Then visit: http://localhost:3000/simple_frontend.html")

if __name__ == "__main__":
    main()