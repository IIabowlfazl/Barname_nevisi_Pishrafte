# Sierpinski triangle via the chaos game (turtle).

import turtle
import random

VERTICES = [
    (0, 200, "blue"),
    (-200, -200, "red"),
    (200, -200, "green"),
]


def draw_sierpinski(iterations=10_000):
    screen = turtle.Screen()
    screen.tracer(0)
    pen = turtle.Turtle()
    pen.speed(0)
    pen.hideturtle()
    pen.penup()

    for vx, vy, color in VERTICES:
        pen.goto(vx, vy)
        pen.dot(10, color)

    x = y = 0
    for _ in range(iterations):
        vx, vy, color = random.choice(VERTICES)
        x = (x + vx) / 2
        y = (y + vy) / 2
        pen.goto(x, y)
        pen.dot(3, color)

    screen.update()
    turtle.done()


if __name__ == "__main__":
    draw_sierpinski()
