# Multiply two fixed 2x2 matrices using explicit loops.

def matrix_multiply(a, b):
    n = len(a)
    result = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result[i][j] += a[i][k] * b[k][j]
    return result


def main():
    first = [[2, 3], [3, 4]]
    second = [[2, 3], [3, 4]]
    print(matrix_multiply(first, second))


if __name__ == "__main__":
    main()
