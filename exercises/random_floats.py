# Print N pseudo-random floating point values in [0, 1).

import sys
import random


def main():
    n = int(sys.argv[1])
    for _ in range(n):
        print(random.random())


if __name__ == "__main__":
    main()
