#!/usr/bin/env python3
"""
Test model availability and selection
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_available_models():
    """Test the available models endpoint"""
    print("🧪 Testing available models...")
    
    try:
        response = requests.get(f"{BASE_URL}/models")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Models retrieved successfully!")
            print(f"📊 Default model: {result['default_model']}")
            
            print("\n📋 Available Models:")
            for model_id, model_info in result['available_models'].items():
                print(f"\n• {model_id}")
                print(f"  Name: {model_info['name']}")
                print(f"  Description: {model_info['description']}")
                print(f"  Max Tokens: {model_info['max_tokens']}")
                print(f"  Temperature: {model_info['temperature']}")
                print(f"  Is Default: {model_info.get('is_default', False)}")
                print(f"  Strengths: {', '.join(model_info['strengths'][:3])}...")
            
            # Check if Meta-Llama is available
            meta_models = [mid for mid in result['available_models'].keys() if 'meta-llama' in mid.lower()]
            if meta_models:
                print(f"\n✅ Meta-Llama models found: {meta_models}")
            else:
                print("\n❌ No Meta-Llama models found!")
            
            return True, result
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False, None

def test_model_recommendation():
    """Test model recommendation for a Jupyter notebook"""
    print("\n🧪 Testing model recommendation for .ipynb file...")
    
    # Create a test Jupyter notebook
    notebook_content = '''{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["# Test Notebook"]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "source": ["import pandas as pd\\ndf = pd.DataFrame({'A': [1, 2, 3]})\\nprint(df)"]
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
    
    try:
        files = {'file': ('test.ipynb', notebook_content.encode(), 'application/json')}
        response = requests.post(f"{BASE_URL}/recommend-model", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Model recommendation successful!")
            print(f"📊 Recommended model: {result['recommended_model']}")
            print(f"🎯 Model name: {result['model_name']}")
            print(f"📝 Reasons: {', '.join(result['reasons'])}")
            print(f"🔢 Confidence: {result['confidence']:.2f}")
            
            return True, result
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False, None

def test_model_usage():
    """Test using Meta-Llama model specifically"""
    print("\n🧪 Testing Meta-Llama model usage...")
    
    notebook_content = '''{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "source": ["print('Hello from Jupyter!')"]
  }
 ]
}'''
    
    try:
        files = {'file': ('test.ipynb', notebook_content.encode(), 'application/json')}
        data = {
            'question': 'What does this notebook do?',
            'model': 'meta-llama/Meta-Llama-3.1-70B-Instruct'
        }
        
        response = requests.post(f"{BASE_URL}/ask", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Meta-Llama model usage successful!")
            print(f"🤖 Model used: {result['model_used']}")
            print(f"📝 Answer length: {len(result['answer'])} characters")
            print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
            
            return True, result
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False, None

def main():
    """Run model availability tests"""
    print("🚀 Model Availability Testing")
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
    
    # Test available models
    success, models_data = test_available_models()
    
    if success:
        # Test model recommendation
        test_model_recommendation()
        
        # Test Meta-Llama usage
        test_model_usage()
        
        print("\n🎉 Model availability tests completed!")
    else:
        print("\n❌ Failed to get available models")

if __name__ == "__main__":
    main()