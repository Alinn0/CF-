import ctypes
import sys
import time
import pyautogui
import win32gui
import win32con

screenshot = pyautogui.screenshot(region=(1240, 780,200, 40))
screenshot.save("debug_region.png")