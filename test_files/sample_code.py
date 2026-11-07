
def fibonacci(n):
    '''Calculate the nth Fibonacci number using recursion'''
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    '''A simple calculator class'''
    
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
calc = Calculator()
print(calc.add(5, 3))
print(calc.multiply(4, 7))
