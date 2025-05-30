import ctypes
import sys
import time
import pyautogui
import win32gui
import win32con

screenshot = pyautogui.screenshot(region=(944, 432, 21, 6))
screenshot.save("debug_region.png")