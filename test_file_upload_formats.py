#!/usr/bin/env python3
"""
Test file upload formats support
"""

import requests
import os

BASE_URL = "http://localhost:8000"

def test_supported_formats():
    """Test the supported formats endpoint"""
    print("🧪 Testing supported formats...")
    
    try:
        response = requests.get(f"{BASE_URL}/supported-formats")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Supported formats retrieved successfully!")
            
            formats = result['supported_formats']
            print(f"\n📊 Total formats supported: {result.get('total_formats', 'Unknown')}")
            
            print("\n📋 Format Categories:")
            for category, extensions in formats.items():
                print(f"• {category.replace('_', ' ').title()}: {', '.join(extensions)}")
            
            # Create test files for each format
            test_files_created = []
            test_dir = "test_files"
            os.makedirs(test_dir, exist_ok=True)
            
            # Test code files
            code_samples = {
                'py': 'print("Hello, Python!")\ndef greet(name):\n    return f"Hello, {name}!"',
                'js': 'console.log("Hello, JavaScript!");\nfunction greet(name) {\n    return `Hello, ${name}!`;\n}',
                'ts': 'console.log("Hello, TypeScript!");\nfunction greet(name: string): string {\n    return `Hello, ${name}!`;\n}',
                'java': 'public class Hello {\n    public static void main(String[] args) {\n        System.out.println("Hello, Java!");\n    }\n}',
                'cpp': '#include <iostream>\nint main() {\n    std::cout << "Hello, C++!" << std::endl;\n    return 0;\n}',
                'c': '#include <stdio.h>\nint main() {\n    printf("Hello, C!\\n");\n    return 0;\n}',
                'sh': '#!/bin/bash\necho "Hello, Shell!"'
            }
            
            for ext, content in code_samples.items():
                if ext in formats.get('code_files', []):
                    filename = f"{test_dir}/sample.{ext}"
                    with open(filename, 'w') as f:
                        f.write(content)
                    test_files_created.append(filename)
                    print(f"✅ Created test file: {filename}")
            
            # Test notebook file
            if 'ipynb' in formats.get('notebooks', []):
                notebook_content = '''{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["# Test Notebook\\n", "This is a test Jupyter notebook."]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "source": ["print('Hello from Jupyter!')\\n", "x = 42\\n", "print(f'The answer is {x}')"],
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": ["Hello from Jupyter!\\n", "The answer is 42\\n"]
    }
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}'''
                filename = f"{test_dir}/sample.ipynb"
                with open(filename, 'w') as f:
                    f.write(notebook_content)
                test_files_created.append(filename)
                print(f"✅ Created test notebook: {filename}")
            
            print(f"\n🎯 Created {len(test_files_created)} test files for upload testing")
            return True, test_files_created
        else:
            print(f"❌ API Error: {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False, []

def test_file_upload(test_files):
    """Test uploading different file formats"""
    print("\n🧪 Testing file upload with different formats...")
    
    success_count = 0
    total_count = len(test_files)
    
    for file_path in test_files:
        filename = os.path.basename(file_path)
        extension = filename.split('.')[-1]
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'text/plain')}
                data = {'question': f'What is this {extension} file about?'}
                
                print(f"📤 Testing upload: {filename}")
                response = requests.post(f"{BASE_URL}/ask", files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ {filename}: Upload successful")
                    print(f"   📄 Extracted text length: {len(result.get('extracted_text', ''))}")
                    print(f"   🤖 Model used: {result.get('model_used', 'Unknown')}")
                    success_count += 1
                else:
                    print(f"❌ {filename}: Upload failed ({response.status_code})")
                    print(f"   Error: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"❌ {filename}: Exception - {str(e)}")
    
    print(f"\n📊 Upload Test Results: {success_count}/{total_count} files uploaded successfully")
    return success_count == total_count

def main():
    """Run file upload format tests"""
    print("🚀 File Upload Format Testing")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/supported-formats")
        if response.status_code != 200:
            print("❌ Server is not running or not accessible")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        return
    
    print("✅ Server is running")
    
    # Test supported formats
    success, test_files = test_supported_formats()
    
    if success and test_files:
        # Test file uploads
        upload_success = test_file_upload(test_files)
        
        if upload_success:
            print("\n🎉 All file format tests passed!")
        else:
            print("\n⚠️  Some file uploads failed. Check the errors above.")
    else:
        print("\n❌ Failed to create test files")

if __name__ == "__main__":
    main()