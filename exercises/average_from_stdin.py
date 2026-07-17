# Compute the average of numbers supplied one per line on standard input.

import sys


def main():
    total = 0.0
    count = 0
    for line in sys.stdin:
        try:
            total += float(line.strip())
            count += 1
        except ValueError:
            continue
    if count > 0:
        print(f"Average: {total / count}")
    else:
        print("No valid numbers found.")


if __name__ == "__main__":
    main()
