import ctypes
import time


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]


class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]


MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

screen_width = ctypes.windll.user32.GetSystemMetrics(0)
screen_height = ctypes.windll.user32.GetSystemMetrics(1)


def click(x, y):
    abs_x = int(x * 65535 / screen_width)
    abs_y = int(y * 65535 / screen_height)

    extra = ctypes.c_ulong(0)
    ii_ = Input_I()

    ii_.mi = MouseInput(abs_x, abs_y, 0, MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
    input_move = Input(ctypes.c_ulong(0), ii_)

    ii_.mi = MouseInput(abs_x, abs_y, 0, MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
    input_down = Input(ctypes.c_ulong(0), ii_)

    ii_.mi = MouseInput(abs_x, abs_y, 0, MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
    input_up = Input(ctypes.c_ulong(0), ii_)

    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_move), ctypes.sizeof(input_move))
    time.sleep(0.01)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_down), ctypes.sizeof(input_down))
    time.sleep(0.01)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_up), ctypes.sizeof(input_up))