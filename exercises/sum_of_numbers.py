# Sum of N numbers entered by the user.

def main():
    count = int(input("How many numbers? "))
    total = 0
    for _ in range(count):
        total += int(input())
    print("Sum is", total)

if __name__ == "__main__":
    main()
