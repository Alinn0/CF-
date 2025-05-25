import ctypes
import time
import sys
import threading
import keyboard
import pyautogui
import pydirectinput
import win32api
import win32con
from win32gui import FindWindow, SendMessage

# 检查管理员权限
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 配置参数
GAME_WINDOW_TITLE = "穿越火线"  # 修改为实际窗口标题
LOG_MAX_LINES = 15

class InputTester:
    def __init__(self):
        self.running = True
        self.log = []
        self.setup_hotkeys()
        print("脚本已启动，按F3测试各种输入方法，按ESC退出")

    def log_message(self, msg):
        """带时间戳的日志记录"""
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        self.log = [entry] + self.log[-LOG_MAX_LINES:]
        print(entry)

    def setup_hotkeys(self):
        """设置全局热键"""
        keyboard.add_hotkey('f3', self.test_all_methods)
        keyboard.add_hotkey('esc', self.exit)

   # 以下是不同输入方法实现
    def method1_pyautogui(self):
        """前台模拟方案"""
        try:
            pyautogui.press('r')
            return True
        except Exception as e:
            self.log_message(f"PyAutoGUI失败: {str(e)}")
            return False

    def method2_directinput(self):
        """DirectX输入方案"""
        try:
            pydirectinput.press('r')
            return True
        except Exception as e:
            self.log_message(f"DirectInput失败: {str(e)}")
            return False

    def method3_win32api(self):
        """Windows消息方案"""
        try:
            hwnd = FindWindow(None, GAME_WINDOW_TITLE)
            if hwnd:
                SendMessage(hwnd, win32con.WM_KEYDOWN, ord('R'), 0)
                time.sleep(0.01)
                SendMessage(hwnd, win32con.WM_KEYUP, ord('R'), 0)
                return True
            return False
        except Exception as e:
            self.log_message(f"Win32API失败: {str(e)}")
            return False

    def method4_ctypes(self):
        """底层驱动方案"""
        try:
            # 定义Windows API结构
            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", ctypes.c_ushort),
                    ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                ]

            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", ctypes.c_ulong),
                    ("ki", KEYBDINPUT),
                    ("pad", ctypes.c_ubyte * 8)
                ]

            # 构造输入事件
            def send_key(scancode, keydown=True):
                extra = ctypes.pointer(ctypes.c_ulong(0))
                flags = 0 if keydown else 0x0002  # KEYEVENTF_KEYUP
                ictx = INPUT()
                ictx.type = 1  # KEYBOARD_INPUT
                ictx.ki = KEYBDINPUT(0, scancode, flags, 0, extra)
                ctypes.windll.user32.SendInput(1, ctypes.byref(ictx), ctypes.sizeof(ictx))

            send_key(0x13, True)  # R键扫描码
            time.sleep(0.01)
            send_key(0x13, False)
            return True
        except Exception as e:
            self.log_message(f"CTypes失败: {str(e)}")
            return False

    def test_all_methods(self):
        """执行所有测试方法"""
        self.log_message("开始输入测试...")
        methods = [
            #("PyAutoGUI前台", self.method1_pyautogui),
            ("DirectX输入", self.method2_directinput),
            #("窗口消息", self.method3_win32api),
            #("底层驱动", self.method4_ctypes)
        ]

        for name, method in methods:
            start_time = time.time()
            result = method()
            elapsed = (time.time() - start_time) * 1000
            status = "成功" if result else "失败"
            self.log_message(f"{name}: {status} ({elapsed:.1f}ms)")
            time.sleep(0.5)  # 方法间间隔

    def exit(self):
        """安全退出"""
        self.running = False
        self.log_message("正在退出程序...")
        keyboard.unhook_all()
        exit(0)

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    tester = InputTester()
    while tester.running:
        time.sleep(0.1)