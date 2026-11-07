#!/usr/bin/env python3
"""
Complete application startup script
"""
import subprocess
import sys
import os
import time
import threading

def start_backend():
    """Start the backend server"""
    try:
        print("🚀 Starting backend server on port 8001...")
        
        # Set environment to handle Unicode properly
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Change to backend directory and start server
        backend_path = os.path.join(os.getcwd(), 'backend')
        
        # Start uvicorn server
        cmd = [
            sys.executable, '-m', 'uvicorn', 
            'main:app', 
            '--host', '0.0.0.0', 
            '--port', '8001'
        ]
        
        subprocess.run(cmd, cwd=backend_path, env=env)
            
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped by user")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

def start_frontend():
    """Start the frontend server"""
    try:
        print("🌐 Starting frontend server on port 3000...")
        time.sleep(2)  # Give backend time to start
        subprocess.run([sys.executable, '-m', 'http.server', '3000'])
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped by user")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")

def main():
    """Main function to start both servers"""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          Document Intelligence Platform - Full Stack         ║")
    print("║                    Backend + Frontend                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    try:
        # Start backend in a separate thread
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        
        # Wait a moment for backend to start
        time.sleep(3)
        
        print("\n📱 Application URLs:")
        print("   Frontend: http://localhost:3000/simple_frontend.html")
        print("   Backend API: http://localhost:8001")
        print("   API Docs: http://localhost:8001/docs")
        print("\n⚠️  Press Ctrl+C to stop both servers")
        
        # Start frontend (this will block)
        start_frontend()
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

if __name__ == "__main__":
    main()