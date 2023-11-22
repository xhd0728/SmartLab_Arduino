import serial
import time
from datetime import datetime

KEY_AIRCONDITIONER = 0
KEY_LED1 = 1
KEY_LED2 = 2
KEY_LED3 = 3
KEY_LED4 = 4


def get_time(format_str="%Y-%m-%d %H:%M:%S") -> str:
    return datetime.now().strftime(format_str)


def read_dev(ser) -> str:
    data_str = ""
    try:
        data_str = ser.read(ser.in_waiting).decode("utf-8")
    except Exception as e:
        print(f"[{get_time()}] 发送失败, 错误信息：\n{str(e)}")
        return data_str
    if data_str:
        print(f"[{get_time()}] 接收成功")
    return data_str


def send_dev(ser, data_str) -> bool:
    try:
        data_str += "\r\n"
        ser.write(data_str.encode("utf-8"))
    except Exception as e:
        print(f"[{get_time()}] 发送失败, 错误信息：\n{str(e)}")
        return False
    print(f"[{get_time()}] 发送成功")
    return True


def main():
    try:
        portx = "COM1"
        bps = 9600
        timex = None
        ser = serial.Serial(portx, bps, timeout=timex)
        cnt = 1
        while True:
            data_str = str(cnt) + " " + datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
            send_dev(ser, data_str)
            cnt += 1
            receive_data = read_dev(ser)
            if receive_data:
                print(receive_data)
            time.sleep(1)
    except Exception as e:
        print("Error", str(e))


if __name__ == "__main__":
    main()
