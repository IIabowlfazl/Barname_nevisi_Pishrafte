k = int (input("Enter the number: "))
re = []
kh = []
i = 0
while not k == 0:
    kh.append(k)
    k = k // 2
    r = kh[i] % 2
    re.append(r)
    i += 1
print("Binary is ", re[::-1])
