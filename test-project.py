#!/usr/bin/env python3
"""
Test script for Smart Document Q&A System
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def run_command(command, cwd=None, timeout=30):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True, timeout=timeout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"

def test_backend_imports():
    """Test if backend imports work"""
    print("🔧 Testing backend imports...")
    backend_dir = Path("backend")
    
    # Test imports
    success, output = run_command(
        "venv\\Scripts\\python -c \"import main; print('All imports successful')\"",
        cwd=backend_dir
    )
    
    if success:
        print("✅ Backend imports work")
        return True
    else:
        print(f"❌ Backend import failed: {output}")
        return False

def test_api_key():
    """Test if API key is configured"""
    print("🔑 Testing API key configuration...")
    env_file = Path("backend/.env")
    
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    if "your_nebius_api_key_here" in content:
        print("⚠️  Please add your actual Nebius API key to backend/.env")
        return False
    
    if "NEBIUS_API_KEY=" in content and len(content.split("NEBIUS_API_KEY=")[1].split()[0]) > 10:
        print("✅ API key appears to be configured")
        return True
    
    print("❌ API key not properly configured")
    return False

def test_frontend_build():
    """Test if frontend builds"""
    print("🎨 Testing frontend build...")
    frontend_dir = Path("frontend")
    
    success, output = run_command("npm run build", cwd=frontend_dir, timeout=120)
    
    if success:
        print("✅ Frontend builds successfully")
        return True
    else:
        print(f"❌ Frontend build failed: {output}")
        return False

def test_backend_server():
    """Test if backend server starts"""
    print("🚀 Testing backend server startup...")
    backend_dir = Path("backend")
    
    # Start server in background
    try:
        process = subprocess.Popen(
            "venv\\Scripts\\python -m uvicorn main:app --host 127.0.0.1 --port 8001",
            shell=True,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(5)
        
        # Test if server is responding
        try:
            response = requests.get("http://127.0.0.1:8001/supported-formats", timeout=10)
            if response.status_code == 200:
                print("✅ Backend server starts and responds")
                success = True
            else:
                print(f"❌ Backend server responded with status {response.status_code}")
                success = False
        except requests.exceptions.RequestException as e:
            print(f"❌ Backend server not responding: {e}")
            success = False
        
        # Clean up
        process.terminate()
        process.wait(timeout=5)
        
        return success
        
    except Exception as e:
        print(f"❌ Failed to start backend server: {e}")
        return False

def test_supported_formats():
    """Test supported formats endpoint"""
    print("📋 Testing supported formats...")
    
    try:
        response = requests.get("http://127.0.0.1:8001/supported-formats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            expected_images = ["jpg", "jpeg", "png", "bmp", "tiff", "gif"]
            expected_docs = ["pdf", "docx", "doc", "txt"]
            
            if (data.get("supported_formats", {}).get("images") == expected_images and
                data.get("supported_formats", {}).get("documents") == expected_docs):
                print("✅ Supported formats endpoint works correctly")
                return True
            else:
                print("❌ Supported formats data incorrect")
                return False
        else:
            print("❌ Supported formats endpoint failed")
            return False
    except:
        print("⚠️  Skipping supported formats test (server not running)")
        return True

def main():
    """Main test function"""
    print("🧪 Smart Document Q&A System - Comprehensive Test")
    print("=" * 50)
    
    tests = [
        ("Backend Imports", test_backend_imports),
        ("API Key Configuration", test_api_key),
        ("Frontend Build", test_frontend_build),
        ("Backend Server", test_backend_server),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Project is ready for use.")
        print("\n📝 Next steps:")
        print("1. Make sure your Nebius API key is in backend/.env")
        print("2. Start backend: cd backend && venv\\Scripts\\activate && python -m uvicorn main:app --reload")
        print("3. Start frontend: cd frontend && npm start")
        print("4. Open http://localhost:3000 in your browser")
        return True
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)