try:
    income = int(input("Enter your Income Rate: "))
    if 0 < income <= 300:
        rate = 0.0
    elif 300 < income <= 1500:
        rate = 0.3
    elif 1500 < income <= 6000:
        rate = 0.5
    elif 6000 < income <= 12000:
        rate = 0.7
    else:
        rate = 0.86
        

    print(f"Your income: " , income)
    print(f"Your tax rate is: " , rate)

except ValueError:
    print("Please Enter Number and Income!")