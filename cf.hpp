#ifndef CF_HPP
#define CF_HPP

#include <stdio.h>
#include <windows.h>
#include <opencv2/opencv.hpp>
#include <string>
#include <conio.h>
#include <cstdlib>
#include <iostream>
#include "framework.h"
#include <tlhelp32.h>


// 前置声明对话框类（避免循环包含）
class CCF插卡机Dlg;

// 函数声明
DWORD WINAPI KeyMonitorThread(LPVOID lpParam);
DWORD WINAPI Task1Thread(LPVOID lpParam);
DWORD WINAPI Task2Thread(LPVOID lpParam);
cv::Mat captureScreenRegion(const int region[4]);
bool imageRecognition(const std::string& templateImageName, const int region[4], double confid);
void checkAdminRights();
void ClickAt(int x, int y);
void SetMousePosition(int x, int y);
void MouseLeftDown();
void MouseLeftUp();
void PressKey(BYTE vkCode);
void KeyDown(BYTE vkCode);
void KeyUp(BYTE vkCode);
void ClickRight();
void KillProcessByWindowTitle(const wchar_t* windowTitle);

// 消息定义（确保与对话框一致）
#define WM_UPDATE_VALUE (WM_USER + 1)

#endif // CF_HPP