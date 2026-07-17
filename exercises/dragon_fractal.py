# A dragon-like fractal drawn with the turtle module.

import turtle
import random


def draw_fractal(iterations=50_000):
    screen = turtle.Screen()
    screen.tracer(0, 0)
    pen = turtle.Turtle()
    pen.hideturtle()
    pen.speed(0)
    pen.penup()
    pen.color("brown")

    x = y = 0.0
    scale = 250
    for _ in range(iterations):
        px, py = x * scale, y * scale - 250
        pen.goto(px, py)
        pen.dot(2)

        r = random.random()
        if r < 0.10:
            x, y = x * 0.05, y * 0.60
        elif r < 0.20:
            x, y = x * 0.05, y * -0.50 + 1.0
        elif r < 0.60:
            x, y = x * 0.46 - y * 0.32, x * 0.39 + y * 0.38 + 0.60
        else:
            x, y = x * 0.47 - y * 0.15, x * 0.17 + y * 0.42 + 1.10

    turtle.update()
    turtle.done()


if __name__ == "__main__":
    draw_fractal()
