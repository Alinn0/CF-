import ctypes
import sys
import time
import pyautogui
import win32gui
import win32con

screenshot = pyautogui.screenshot(region=(870, 388, 20, 20))
screenshot.save("debug_region.png")