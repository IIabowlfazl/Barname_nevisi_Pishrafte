import math
def find_root(equation, derivative, start, iterations=20):
    current = start 
    for i in range(iterations):
        next_value = current - equation(current) / derivative(current)
        print(f"step{i+1}: {next_value}")
        current = next_value
    return current

def my_equation(x):
    return x**3 - 2*x - 2
def my_derivative(x):
    return 3*x**2 - 1

result = find_root(my_equation, my_derivative, 1.5)
print(f"\n Derivative root {result}")
print(f"check of root: {my_equation(result)}")