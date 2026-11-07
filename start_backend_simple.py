#!/usr/bin/env python3
"""
Simple backend starter without Unicode issues
"""
import subprocess
import sys
import os

def start_backend():
    """Start the backend server"""
    try:
        print("Starting backend server...")
        
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
        
        print(f"Starting server in: {backend_path}")
        print(f"Command: {' '.join(cmd)}")
        
        # Start the process
        subprocess.run(cmd, cwd=backend_path, env=env)
            
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    start_backend()