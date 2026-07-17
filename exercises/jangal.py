import random

class animal:
    Zendeha = 0 
    
    def __init__(self, name, kind):
        self.name = name
        self.kind = kind
        animal.Zendeha += 1
        
    def die(self):
        animal.Zendeha -= 1

class rabbit(animal):
    pass

class fox(animal):
    def eat(self, other):
        if other.kind == 'rabbit':
            other.die()
            return True
        return False

class wolf(animal):
    def eat(self, other):
        if other.kind == 'rabbit' or other.kind == 'fox':
            other.die()
            return True
        return False

class tiger(animal):
    def eat(self, other):
        if other.kind == 'fox' or other.kind == 'wolf' or other.kind == 'rabbit':
            other.die()
            return True
        return False

class lion(animal):
    def eat(self, other):
        if other.kind != 'lion':
            other.die()
            return True
        return False


Mohit = []
Kol_tavalod = 0

print("Shabihsazi shoro shod...")
print("---------------------")

for Rooz in range(100):
    print(" Rooz " + str(Rooz + 1) )
    
    Shans = random.randint(1, 100)
    
    if Shans <= 40:
        Heyvan_jadid = rabbit("R-" + str(Rooz), 'rabbit')
        Mohit.append(Heyvan_jadid)
        print("Yek kharghoosh be donya amad.")
    elif Shans <= 65:
        Heyvan_jadid = fox("F-" + str(Rooz), 'fox')
        Mohit.append(Heyvan_jadid)
        print("Yek roobah be donya amad.")
    elif Shans <= 85:
        Heyvan_jadid = wolf("W-" + str(Rooz), 'wolf')
        Mohit.append(Heyvan_jadid)
        print("Yek gorg be donya amad.")
    elif Shans <= 95:
        Heyvan_jadid = tiger("T-" + str(Rooz), 'tiger')
        Mohit.append(Heyvan_jadid)
        print("Yek babr be donya amad.")
    else:
        Heyvan_jadid = lion("L-" + str(Rooz), 'lion')
        Mohit.append(Heyvan_jadid)
        print("Yek shir be donya amad.")

    Kol_tavalod += 1

    if len(Mohit) >= 2:
        Heyvan1 = random.choice(Mohit)
        Heyvan2 = random.choice(Mohit)
        
        if Heyvan1 != Heyvan2:
            Shekar = False
            
            if Heyvan1.kind == 'fox':
                Shekar = Heyvan1.eat(Heyvan2)
            elif Heyvan1.kind == 'wolf':
                Shekar = Heyvan1.eat(Heyvan2)
            elif Heyvan1.kind == 'tiger':
                Shekar = Heyvan1.eat(Heyvan2)
            elif Heyvan1.kind == 'lion':
                Shekar = Heyvan1.eat(Heyvan2)
                
            if Shekar == True:
                print(Heyvan1.kind + " tavanest " + Heyvan2.kind + " ra bokhorad!")
                Mohit.remove(Heyvan2)

    print("Tedad heyvanat zende: " + str(animal.Zendeha))
    print("")

print("---------------------")
print("Kole tavalod ha: " + str(Kol_tavalod))
print("Tedad zende ha dar nahayat: " + str(animal.Zendeha))