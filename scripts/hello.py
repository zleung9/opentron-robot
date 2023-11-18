def generate_output():
    a = {"output1": 1, "output2": 2}
    return a

if __name__ == "__main__":
    print("Hello!")
    print(generate_output())
    while True:
        a = input()
        print(a, a)
        if a == "0":
            break
    print("end")