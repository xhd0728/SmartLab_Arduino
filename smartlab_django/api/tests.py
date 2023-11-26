from django.test import TestCase
import time
import serial

# Create your tests here.
ser = serial.Serial("COM2", 9600, timeout=None)

for i in range(1000):
    opt_data = ser.read(ser.in_waiting).decode("utf-8")
    if opt_data:
        proc_str = opt_data.strip().split(',')
        print(f"{proc_str[0]}-{proc_str[1]}-{proc_str[2]}")
    else:
        print('empty')
    time.sleep(1)
