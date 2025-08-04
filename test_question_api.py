#!/usr/bin/env python3
"""
Test script for the Question Generation API
"""

import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_FILES_DIR = "test_files"

def test_generate_questions_from_file():
    """Test question generation from file upload"""
    print("🧪 Testing question generation from file...")
    
    # Create a test file if it doesn't exist
    test_file_path = os.path.join(TEST_FILES_DIR, "sample_code.py")
    if not os.path.exists(test_file_path):
        os.makedirs(TEST_FILES_DIR, exist_ok=True)
        with open(test_file_path, 'w') as f:
            f.write("""
def fibonacci(n):
    '''Calculate the nth Fibonacci number using recursion'''
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    '''Calculate factorial of n'''
    if n <= 1:
        return 1
    return n * factorial(n-1)

class Calculator:
    '''Simple calculator class'''
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

# Example usage
if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.multiply(4, 7))
    print(f"Fibonacci(10): {fibonacci(10)}")
    print(f"Factorial(5): {factorial(5)}")
""")
    
    # Test the API
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('sample_code.py', f, 'text/plain')}
            data = {
                'max_questions': 8,
                'document_category': 'code',
                'user_preferences': json.dumps({
                    'preferred_categories': ['technical', 'debugging', 'optimization']
                })
            }
            
            response = requests.post(f"{BASE_URL}/generate-questions", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Question generation successful!")
                print(f"📄 File: {result['filename']}")
                print(f"📂 Category: {result['document_category']}")
                print(f"🔢 Total questions: {result['total_questions']}")
                print(f"📊 Categories: {result['categories_summary']}")
                
                print("\n🤔 Generated Questions:")
                for i, question in enumerate(result['questions'], 1):
                    print(f"{i}. [{question['category'].upper()}] {question['text']}")
                    print(f"   Relevance: {question['relevance_score']:.2f}")
                    if question['follow_ups']:
                        print(f"   Follow-ups: {', '.join(question['follow_ups'][:2])}")
                    print()
                
                return True
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_generate_questions_from_text():
    """Test question generation from raw text"""
    print("\n🧪 Testing question generation from text...")
    
    sample_text = """
    Machine Learning Model Performance Analysis
    
    This document presents the results of our comprehensive analysis of three machine learning models: 
    Random Forest, Support Vector Machine (SVM), and Neural Network. The study was conducted on a 
    dataset of 10,000 customer records with 25 features including demographic information, 
    purchase history, and behavioral patterns.
    
    Methodology:
    - Data preprocessing included normalization and feature selection
    - 80/20 train-test split was used for model validation
    - Cross-validation with 5 folds was performed
    - Performance metrics: Accuracy, Precision, Recall, F1-score
    
    Results:
    - Random Forest achieved 87.3% accuracy with excellent interpretability
    - SVM showed 85.1% accuracy but required longer training time
    - Neural Network reached 89.2% accuracy but was prone to overfitting
    
    Conclusions:
    The Neural Network model showed the highest accuracy but requires careful regularization.
    Random Forest provides the best balance of performance and interpretability for business use.
    """
    
    try:
        data = {
            'text': sample_text,
            'max_questions': 10,
            'document_category': 'research',
            'filename': 'ml_analysis.txt',
            'user_preferences': json.dumps({
                'preferred_categories': ['analytical', 'factual', 'summary']
            })
        }
        
        response = requests.post(f"{BASE_URL}/generate-questions-from-text", data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Text-based question generation successful!")
            print(f"📄 Document: {result['filename']}")
            print(f"📂 Category: {result['document_category']}")
            print(f"🔢 Total questions: {result['total_questions']}")
            
            print("\n🤔 Generated Questions:")
            for i, question in enumerate(result['questions'], 1):
                print(f"{i}. [{question['category'].upper()}] {question['text']}")
                print(f"   Relevance: {question['relevance_score']:.2f}")
                print()
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_question_categories():
    """Test question categories endpoint"""
    print("\n🧪 Testing question categories endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/question-categories")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Question categories retrieved successfully!")
            print(f"📊 Total categories: {result['total_categories']}")
            
            print("\n📋 Available Categories:")
            for category_id, category_info in result['categories'].items():
                print(f"• {category_info['name']}: {category_info['description']}")
                print(f"  Examples: {', '.join(category_info['examples'])}")
                print()
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Question Generation API Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/supported-formats")
        if response.status_code != 200:
            print("❌ Server is not running or not accessible")
            print("Please start the backend server with: python backend/main.py")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("Please start the backend server with: python backend/main.py")
        return
    
    print("✅ Server is running")
    
    # Run tests
    tests = [
        test_question_categories,
        test_generate_questions_from_text,
        test_generate_questions_from_file
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Question Generation API is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()