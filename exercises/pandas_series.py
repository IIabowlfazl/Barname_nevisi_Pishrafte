# Create a pandas Series of random integers and inspect it.

import numpy as np
import pandas as pd


def main():
    values = list(np.random.randint(1, 101, size=10))
    series = pd.Series(data=values, index=range(1, 11), name="Random Number")
    series.index.name = "idx"

    print("= Main series =")
    print(series)

    squared = series ** 2
    print("\n=== 5 last items (squared) ===")
    print(squared.tail(5))

    above_500 = squared[squared > 500].tolist()
    print("\n=== Values > 500 ===")
    print(above_500)


if __name__ == "__main__":
    main()
