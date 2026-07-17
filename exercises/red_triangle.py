# Draw a single red equilateral triangle with the turtle.

import turtle


def main():
    turtle.color("red")
    for _ in range(3):
        turtle.forward(100)
        turtle.left(120)
    turtle.done()


if __name__ == "__main__":
    main()
