# Monte Carlo simulation of the gambler's ruin problem.
# For each fixed bet size x we estimate the probability of ruin
# before reaching the target, then report the best x.

import random


def simulate_ruin(starting_capital, target, win_probability, bet, trials):
    ruined = 0
    for _ in range(trials):
        capital = starting_capital
        while 0 < capital < target:
            if random.random() < win_probability:
                capital += bet
            else:
                capital -= bet
        if capital <= 0:
            ruined += 1
    return ruined / trials


def main():
    capital = int(input("Please enter the initial capital: "))
    target = int(input("Please enter the target capital: "))
    win_prob = float(input("Please enter win probability (e.g. 0.5): "))
    trials = int(input("Please enter number of simulations: "))

    best_bet = 1
    lowest_ruin = 1.0

    print("\nComputing ruin probability for different bet sizes...\n")
    for bet in range(1, capital + 1):
        ruin_prob = simulate_ruin(capital, target, win_prob, bet, trials)
        print(f"Bet x = {bet} | Ruin probability = {ruin_prob:.3f}")
        if ruin_prob <= lowest_ruin:
            lowest_ruin = ruin_prob
            best_bet = bet

    print("-" * 40)
    print(f"Final result: best bet size = {best_bet}")
    print(f"Lowest ruin probability: {lowest_ruin:.3f}")


if __name__ == "__main__":
    main()
