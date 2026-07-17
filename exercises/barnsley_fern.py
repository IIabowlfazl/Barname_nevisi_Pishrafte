# Barnsley fern drawn with the turtle module.

import turtle
import random


def step(x, y):
    """Return the next point (nx, ny) of the Barnsley fern chaos game."""
    r = random.random()
    if r < 0.01:
        return 0.0, 0.16 * y
    if r < 0.86:
        return 0.85 * x + 0.04 * y, -0.04 * x + 0.85 * y + 1.6
    if r < 0.93:
        return 0.20 * x - 0.26 * y, 0.23 * x + 0.22 * y + 1.6
    return -0.15 * x + 0.28 * y, 0.26 * x + 0.24 * y + 0.44


def draw_fern(iterations=100_000):
    screen = turtle.Screen()
    screen.tracer(0)
    pen = turtle.Turtle()
    pen.speed(0)
    pen.hideturtle()
    pen.penup()

    x = y = 0.0
    for i in range(iterations):
        x, y = step(x, y)
        pen.goto(x * 50, y * 50 - 250)
        pen.dot(2)
        if i % 1000 == 0:
            screen.update()
    screen.update()
    turtle.done()


if __name__ == "__main__":
    draw_fern()
