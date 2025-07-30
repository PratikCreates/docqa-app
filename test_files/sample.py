#!/usr/bin/env python3
"""
Sample Python file for testing code parsing
"""

def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number"""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.processed = False
    
    def process(self):
        """Process the data"""
        self.data = [x * 2 for x in self.data]
        self.processed = True
        return self.data

if __name__ == "__main__":
    # Test the functions
    print("Fibonacci sequence:")
    for i in range(10):
        print(f"F({i}) = {calculate_fibonacci(i)}")
    
    # Test the class
    processor = DataProcessor([1, 2, 3, 4, 5])
    result = processor.process()
    print(f"Processed data: {result}")