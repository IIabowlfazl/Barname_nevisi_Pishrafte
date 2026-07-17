n = int(input("Enter The Number: "))
ruler = ' '
for i in range(1, n + 1):
    ruler = ruler + str(i) + ruler
print(ruler)
