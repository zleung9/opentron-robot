from auto.robot import Robot
import sys

b = Robot("Agent2")
b.connect(
    hostname="169.254.230.44", 
    key_path="C:\\Users\\Automat\\Documents\\automation_control\\.ssh\\ssh_key_OT2_SDWF"
)
b.upload("hello.py")
b.upload("sdwf.py")
stdin, stdout, stderr = b.execute("sdwf.py")
print(stdout.readlines())
# stdin.write("1")
# print(stdout.readlines())
# stdin.write("2")
# print(stdout.readlines())
# stdin.write("0")
# print(stdout.readlines())
# b.close()