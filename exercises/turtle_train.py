import turtle

def draw_polygon(n, length):
    angle = 360 / n
    for _ in range(n):
        turtle.forward(length)
        turtle.left(angle)

def draw_many_polygons(n, length):
    for _ in range(n):
        draw_polygon(n, length)
        turtle.forward(length)

n = int(turtle.textinput("Enter the number of sides","The number of Sides must be more than 2"))
if n <= 2:
    print("The Number of Sides must be more than 2 :/")
    turtle.done() 

length = 40
turtle.speed(10)
draw_many_polygons(n, length)
turtle.done()