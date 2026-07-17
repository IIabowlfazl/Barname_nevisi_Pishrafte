import random
numbers = []
for i in range(20):
    numbers.append(random.randint(0, 15))

# print("Numbers: ", numbers)
numbers.sort(reverse=True)

subset = []
total = 0
i = 0

while i < len(numbers):
    if total + numbers[i] <= 52:
        subset.append(numbers[i])
        total += numbers[i]
    if 50 <= total <= 52:
        break
    i += 1

if 50 <= total <= 52:
    print("Subsets:", subset)
    print("Sum of subsets:", total)
    print("Number of Subsets", len(subset))
else:
    print("No subcategories found.")