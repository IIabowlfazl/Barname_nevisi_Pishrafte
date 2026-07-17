def number(n):
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False
    return True

def find_kth_prime_after_n(n, k):
    count = 0
    current = n + 1
    while True:
        if number(current):
            count += 1
            if count == k:
                return current
        current += 1

n = int(input("Enter n: "))
k = int(input("Enter k: "))

result = find_kth_prime_after_n(n, k)
print("The", k, "th prime number after", n, "is:", result)