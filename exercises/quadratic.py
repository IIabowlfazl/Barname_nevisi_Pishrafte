import math
a = int(input("Enter a: "))
b = int(input("Enter b: "))
c = int(input("Enter c: "))

delta = (b**2) - (4*a*c)

if delta < 0:
    print("\nThe Delta is n't positive")
elif delta == 0:
    print("\nDelta is 0")
    x1 = (-b + math.sqrt(delta))/(2*a)
    x2 = (-b - math.sqrt(delta))/(2*a)
    print (x1,x2)
else:
    x1 = (-b + math.sqrt(delta))/(2*a)
    x2 = (-b - math.sqrt(delta))/(2*a)
    print (x1,x2)
