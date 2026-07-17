Year = int(input("Enter The Year: "))
if (Year % 4 == 0 and Year % 100 != 0) or (Year % 400 == 0):
    print("Kabise")
else:
    print("Casual")
