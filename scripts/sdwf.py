import subprocess
from threading import Timer
import os
import sys


def generate_output():
    a = {"output1": 1, "output3": 3}
    return a
def exit_upon_timeout():
    print("Timeout, exiting...")
    sys.exit(1)

if __name__ == "__main__":
    t = Timer(10, exit_upon_timeout)
    t.start()
    print("Hello!")
    subprocess.run(["pwd"])
    # a = input()
    subprocess.run(["python", "/data/user_storage/hello.py"])
    # while True:
    #     a = input()
    #     print(a, a)
    #     if a == "0":
    #         break
    # print("end")
    t.cancel()