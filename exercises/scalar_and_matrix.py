import random
a = 3861542722
u = []
for i in str(a):
    j = int(i)
    if j not in u:
        u += [j]
print(u)
###############################################
################part of MATRIX#################
###############################################
b = []
for x in str(a):
    y = int(x)
    if y not in b:
        b.append(y)

m1 = []
m2 = []
for _ in range(3):
    r1 = []
    r2 = []
    for _ in range(3):
        r1.append(random.choice(b))
        r2.append(random.choice(b))
    m1.append(r1)
    m2.append(r2)

print("M1:")
for r in m1:
    print(r)

print("M2:")
for r in m2:
    print(r)
