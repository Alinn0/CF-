import ctypes
import sys
import time
import pyautogui
import win32gui
import win32con

screenshot = pyautogui.screenshot(region=(260+609, 189+520,51, 25))
screenshot.save("debug_region.png")