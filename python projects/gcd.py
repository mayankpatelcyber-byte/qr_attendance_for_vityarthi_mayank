num1=int(input("enter the number 1 "))
num2=int(input("enter the number 2 "))
for i in range(1, min(num1,num2) + 1):
    if num1 % i == 0 and num2 % i == 0:
        gcd = i
        print("The GCD of", num1, "and", num2, "is:", gcd)
        