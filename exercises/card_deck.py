# Build and print a standard 52-card deck.

import random

SUITS = ["Clubs", "Diamonds", "Hearts", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "Jack", "Queen", "King", "Ace"]


def build_deck():
    return [f"{rank} of {suit}" for rank in RANKS for suit in SUITS]


def main():
    deck = build_deck()
    # Draw one random card to show the structure works.
    random.shuffle(deck)
    print("Full deck size:", len(deck))
    print("Sample card:", deck[0])
    print(deck)


if __name__ == "__main__":
    main()
