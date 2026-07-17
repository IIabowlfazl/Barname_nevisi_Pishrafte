# Number guessing game: the computer picks a secret, the player guesses.

import random


def main():
    upper_bound = 1_000_000
    secret = random.randrange(1, upper_bound + 1)

    print(f"Guess a number between 1 and {upper_bound}")

    while True:
        try:
            guess = int(input("What is your guess? "))
        except ValueError:
            print("Please enter an integer.")
            continue

        if guess < secret:
            print("Too low")
        elif guess > secret:
            print("Too high")
        else:
            print("You win!")
            break


if __name__ == "__main__":
    main()
