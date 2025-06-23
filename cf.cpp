#include "pch.h"
#include "cf.hpp"
#include "CF插卡机Dlg.h" // 包含对话框头文件

// 资源文件路径
const std::string BOSS召唤 = "Boss.png";
const int BOSS图片区域[4] = { 1240, 780, 200, 40 };
const std::string 确认 = "configuration.png";
const int 确认图片区域[4] = { 850, 760, 200, 40 };
const std::string  伤害图片 = "dps.png";
const int 伤害图片区域[4] = { 613, 141, 63, 12 };

// 全局变量
bool MoseLeftDownFlag = false;
bool task1Running = false;  // 放卡开枪事件运行状态
bool task2Running = false;  // BOSS开枪事件运行状态
HANDLE hTaskThread = NULL;  // 任务线程句柄

/* int main() {
    // 检查管理员权限
    checkAdminRights();

    // 创建按键监控线程
    HANDLE hKeyThread = CreateThread(NULL, 0, KeyMonitorThread, NULL, 0, NULL);
    if (hKeyThread == NULL) {
        printf("Create key monitor thread failed with error: %d\n", GetLastError());
        return 1;
    }
    printf("游戏分辨率：全屏1920 * 1080，桌面分辨率最好也是1920 * 1080，桌面缩放设置100%，游戏里面打开hud放大\n");
    printf("\n需要换弹请将换弹键改为鼠标右键\n\n");
    printf("程序已启动，使用以下按键控制：\n");
    printf("F9 - 切换鼠标左键按下状态\n");
    printf("F11 - 启动/停止放卡开枪事件\n");
    printf("F12 - 启动/停止BOSS开枪事件\n");
    printf("右边Ctrl - 重置星级和卡片值\n");
    printf("目前星级：1星  卡片：第一张\n");
    printf("最大放卡张数：1000\n");

    // 主循环，等待程序结束
    while (1) {
        Sleep(1000);  // 防止CPU占用过高
    }

    return 0;
} */

cv::Mat captureScreenRegion(const int region[4]) {
    // 从输入数组提取参数
    int x = region[0];
    int y = region[1];
    int width = region[2];
    int height = region[3];

    // 检查参数有效性
    if (width <= 0 || height <= 0) {
        return cv::Mat();  // 返回空图像
    }

    // 计算右下角坐标
    int right = x + width;
    int bottom = y + height;

    // 获取屏幕设备上下文
    HDC hScreenDC = GetDC(NULL);
    HDC hMemoryDC = CreateCompatibleDC(hScreenDC);

    // 创建兼容位图
    HBITMAP hBitmap = CreateCompatibleBitmap(hScreenDC, width, height);
    HBITMAP hOldBitmap = (HBITMAP)SelectObject(hMemoryDC, hBitmap);

    // 复制屏幕区域到内存DC
    BitBlt(hMemoryDC, 0, 0, width, height, hScreenDC, x, y, SRCCOPY);

    // 创建OpenCV Mat对象
    cv::Mat mat(height, width, CV_8UC4);

    // 设置位图信息头
    BITMAPINFOHEADER bmi = { 0 };
    bmi.biSize = sizeof(BITMAPINFOHEADER);
    bmi.biWidth = width;
    bmi.biHeight = -height;  // 负号表示从上到下的DIB
    bmi.biPlanes = 1;
    bmi.biBitCount = 32;      // 32位色彩（BGRA）
    bmi.biCompression = BI_RGB;

    // 转换位图数据到OpenCV Mat
    GetDIBits(hMemoryDC, hBitmap, 0, height,
        mat.data, (BITMAPINFO*)&bmi, DIB_RGB_COLORS);

    // 清理资源
    SelectObject(hMemoryDC, hOldBitmap);
    DeleteObject(hBitmap);
    DeleteDC(hMemoryDC);
    ReleaseDC(NULL, hScreenDC);

    // 将BGRA转换为BGR（移除alpha通道）
    cv::Mat bgrMat;
    cv::cvtColor(mat, bgrMat, cv::COLOR_BGRA2BGR);

    return bgrMat;
}

bool imageRecognition(const std::string& templateImageName, const int region[4], double confid){
    // 1. 截取屏幕指定区域
    cv::Mat capturedImage = captureScreenRegion(region);
    if (capturedImage.empty()) {
        std::cerr << "屏幕截图失败!" << std::endl;
        return 0;
    }

    // 2. 读取模板图像
    cv::Mat templateImage = cv::imread(templateImageName, cv::IMREAD_COLOR);
    if (templateImage.empty()) {
        std::cerr << "无法加载模板图像: " << templateImageName << std::endl;
        return 0;
    }

    // 3. 计算模板匹配度（使用归一化相关系数法）
    cv::Mat result;
    int result_cols = capturedImage.cols - templateImage.cols + 1;
    int result_rows = capturedImage.rows - templateImage.rows + 1;

    if (result_cols <= 0 || result_rows <= 0) {
        std::cerr << "模板图像比截取区域大!" << std::endl;
        return 0;
    }

    result.create(result_rows, result_cols, CV_32FC1);

    // 执行模板匹配
    cv::matchTemplate(capturedImage, templateImage, result, cv::TM_CCOEFF_NORMED);

    // 4. 计算最佳匹配度
    double minVal, maxVal;
    cv::Point minLoc, maxLoc;
    cv::minMaxLoc(result, &minVal, &maxVal, &minLoc, &maxLoc);

    // 5. 可选：可视化最佳匹配位置
#ifdef VISUALIZE_RESULT
    cv::rectangle(capturedImage,
        cv::Rect(maxLoc.x, maxLoc.y, templateImage.cols, templateImage.rows),
        cv::Scalar(0, 0, 255), 2);
    cv::imshow("匹配结果", capturedImage);
    cv::waitKey(1000);
#endif
	//printf("匹配度: %f\n", maxVal);
    if(maxVal> confid){
        return true;
    }
    else {
        return false; // 如果匹配度低于阈值，返回false
    }

}



DWORD WINAPI KeyMonitorThread(LPVOID lpParam) {
    // 获取传递的主窗口句柄
    HWND hWnd = reinterpret_cast<HWND>(lpParam);

    // 检查句柄有效性
    if (!IsWindow(hWnd)) {
        return 1;
    }

    while (true)
    {
        // F9 按键处理
        if (GetAsyncKeyState(VK_F9) & 0x8000) {
            while (GetAsyncKeyState(VK_F9) & 0x8000) Sleep(50);

            INPUT input = { 0 };
            input.type = INPUT_MOUSE;
            input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
            SendInput(1, &input, sizeof(INPUT));

        }

        // F11 按键处理
        if (GetAsyncKeyState(VK_F11) & 0x8000) {
            while (GetAsyncKeyState(VK_F11) & 0x8000) Sleep(50);

            task1Running = !task1Running;

            if (task1Running) {
                task2Running = false;
                if (hTaskThread) {
                    TerminateThread(hTaskThread, 0);
                    CloseHandle(hTaskThread);
                    hTaskThread = NULL;
                }

                // 启动任务线程并传递窗口句柄
                hTaskThread = CreateThread(
                    NULL,
                    0,
                    Task1Thread,
                    hWnd, // 传递窗口句柄给任务线程
                    0,
                    NULL
                );

                if (hTaskThread == NULL) {
                    task1Running = false;
                }
            }
            else if (hTaskThread) {
                TerminateThread(hTaskThread, 0);
                CloseHandle(hTaskThread);
                hTaskThread = NULL;
            }

            // 发送状态消息

        }

        // F12 按键处理
        if (GetAsyncKeyState(VK_F12) & 0x8000) {
            while (GetAsyncKeyState(VK_F12) & 0x8000) Sleep(50);

            task2Running = !task2Running;

            if (task2Running) {
                task1Running = false;
                if (hTaskThread) {
                    TerminateThread(hTaskThread, 0);
                    CloseHandle(hTaskThread);
                    hTaskThread = NULL;
                }

                // 启动任务线程并传递窗口句柄
                hTaskThread = CreateThread(
                    NULL,
                    0,
                    Task2Thread,
                    hWnd, // 传递窗口句柄给任务线程
                    0,
                    NULL
                );

                if (hTaskThread == NULL) {
                    task2Running = false;
                }
            }
            else if (hTaskThread) {
                TerminateThread(hTaskThread, 0);
                CloseHandle(hTaskThread);
                hTaskThread = NULL;
            }

        }

        Sleep(50);
    }
    return 0;
}


void checkAdminRights() {
    BOOL isAdmin = FALSE;
    HANDLE hToken = NULL;

    // 检查是否是管理员权限
    if (OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &hToken)) {
        TOKEN_ELEVATION elevation;
        DWORD cbSize = sizeof(TOKEN_ELEVATION);

        if (GetTokenInformation(hToken, TokenElevation, &elevation, sizeof(elevation), &cbSize)) {
            isAdmin = elevation.TokenIsElevated;
        }
        CloseHandle(hToken);
    }

    // 非管理员权限则尝试重启
    if (!isAdmin) {
        wchar_t exePath[MAX_PATH];
        GetModuleFileNameW(NULL, exePath, MAX_PATH);

        // 构造参数（跳过第一个参数 - 程序自身路径）
        int argc;
        wchar_t** argv = CommandLineToArgvW(GetCommandLineW(), &argc);
        wchar_t cmdLine[1024] = L"";

        for (int i = 1; i < argc; ++i) {
            wcscat_s(cmdLine, 1024, L"\"");
            wcscat_s(cmdLine, 1024, argv[i]);
            wcscat_s(cmdLine, 1024, L"\" ");
        }

        SHELLEXECUTEINFOW sei = { sizeof(sei) };
        sei.lpVerb = L"runas";
        sei.lpFile = exePath;
        sei.lpParameters = cmdLine;
        sei.hwnd = NULL;
        sei.nShow = SW_NORMAL;

        // 尝试以管理员身份启动
        if (ShellExecuteExW(&sei)) {
            LocalFree(argv);
            ExitProcess(0); // 正常退出当前非管理员进程
        }

        LocalFree(argv);
    }
}

// 设置鼠标位置（不产生移动事件）
void SetMousePosition(int x, int y) {
    INPUT input = { 0 };
    input.type = INPUT_MOUSE;
    input.mi.dx = (x * 65535) / (GetSystemMetrics(SM_CXSCREEN) - 1);
    input.mi.dy = (y * 65535) / (GetSystemMetrics(SM_CYSCREEN) - 1);
    input.mi.dwFlags = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE | MOUSEEVENTF_VIRTUALDESK;
    SendInput(1, &input, sizeof(INPUT));
}

// 点击屏幕指定位置（左键按下+释放）
void ClickAt(int x, int y) {
    // 设置鼠标位置
    SetMousePosition(x, y);

    // 准备点击事件
    INPUT inputs[2] = { 0 };

    // 左键按下
    inputs[0].type = INPUT_MOUSE;
    inputs[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;

    // 左键释放
    inputs[1].type = INPUT_MOUSE;
    inputs[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;

    // 发送点击事件
    SendInput(2, inputs, sizeof(INPUT));
}

// 在指定坐标点击鼠标中键（滚轮按钮）
void ClickRight() {
    // 设置鼠标位置

    // 准备点击事件
    INPUT inputs[2] = { 0 };

    // 中键按下事件
    inputs[0].type = INPUT_MOUSE;
    inputs[0].mi.dwFlags = MOUSEEVENTF_RIGHTDOWN;

    // 中键释放事件
    inputs[1].type = INPUT_MOUSE;
    inputs[1].mi.dwFlags = MOUSEEVENTF_RIGHTUP;

    // 发送点击事件
    SendInput(2, inputs, sizeof(INPUT));
}

// 按下鼠标左键
void MouseLeftDown() {
	if (MoseLeftDownFlag) return; // 如果鼠标左键已经按下，直接返回
    INPUT input = { 0 };
    input.type = INPUT_MOUSE;
    input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
    SendInput(1, &input, sizeof(INPUT));
	MoseLeftDownFlag = true; // 设置鼠标左键按下标志
}

// 释放鼠标左键
void MouseLeftUp() {
    if (!MoseLeftDownFlag) return; // 如果鼠标左键已经按下，直接返回
    INPUT input = { 0 };
    input.type = INPUT_MOUSE;
    input.mi.dwFlags = MOUSEEVENTF_LEFTUP;
    SendInput(1, &input, sizeof(INPUT));
	MoseLeftDownFlag = false; // 重置鼠标左键按下标志
}

// 点击键盘按键（按下+释放）
void PressKey(BYTE vkCode) {
    INPUT inputs[2] = { 0 };

    // 按键按下
    inputs[0].type = INPUT_KEYBOARD;
    inputs[0].ki.wVk = vkCode;

    // 按键释放
    inputs[1].type = INPUT_KEYBOARD;
    inputs[1].ki.wVk = vkCode;
    inputs[1].ki.dwFlags = KEYEVENTF_KEYUP;

    SendInput(2, inputs, sizeof(INPUT));
}

// 按下键盘按键
void KeyDown(BYTE vkCode) {
    INPUT input = { 0 };
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = vkCode;
    SendInput(1, &input, sizeof(INPUT));
}

// 释放键盘按键
void KeyUp(BYTE vkCode) {
    INPUT input = { 0 };
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = vkCode;
    input.ki.dwFlags = KEYEVENTF_KEYUP;
    SendInput(1, &input, sizeof(INPUT));
}

// 放卡开枪事件线程
DWORD WINAPI Task1Thread(LPVOID lpParam) {
    // 获取主窗口句柄
    bool E状态 = false;
    HWND hWnd = reinterpret_cast<HWND>(lpParam);

    // 检查句柄有效性
    if (!IsWindow(hWnd)) {
        return 1;
    }

    MoseLeftDownFlag = false;
    int ReleaseCard = 0; // 释放卡片次数
    bool 上次BOSS图片状态 = false; // 上次BOSS图片状态


    while (task1Running) {
        if (imageRecognition(确认, 确认图片区域, 0.5)) {
            ClickAt(960, 785);
        }

        bool BOSS = imageRecognition(伤害图片, 伤害图片区域, 0.5);
        if (BOSS != 上次BOSS图片状态) {
            if (!BOSS) {
                MouseLeftUp();
                Sleep(200);
                ClickRight();
                Sleep(200);
                ClickRight();
                Sleep(200);
                ClickRight();
                上次BOSS图片状态 = false;
                E状态 = false;
            }
        }

        if (BOSS) {
            MouseLeftDown();
            上次BOSS图片状态 = true;
        }
        else {
            // 发送放卡消息
            if (!E状态) {
                PressKey(0x45); // 按E键
                Sleep(200);

                if (imageRecognition(BOSS召唤, BOSS图片区域, 0.5)) {
                    ClickAt(590 + 星级 * 150, 367); // 点击星级
                    Sleep(200);
                    ClickAt(630 + 卡片类型 * 200, 540); // 点击卡片
                    Sleep(200);

                    if (imageRecognition(BOSS召唤, BOSS图片区域, 0.5)) {
                        Sleep(100);

                        if (imageRecognition(BOSS召唤, BOSS图片区域, 0.5)) {
                            if (ReleaseCard < 放卡数量) {
                                ClickAt(1346, 806); // 点击放卡按钮
                                E状态 = true;
                                ReleaseCard++;
                                CString* pCountMsg = new CString;
                                pCountMsg->Format(_T("释放卡片次数: %d/%d"), ReleaseCard, 放卡数量);
                                ::PostMessage(hWnd, WM_UPDATE_VALUE, (WPARAM)pCountMsg, 0);
                            }
                            else {
                                task1Running = false;

                                break;
                            }
                        }
                    }
                }
            }
        }
        Sleep(20);
    }

    return 0;
}

// 检测boss开枪事件线程
DWORD WINAPI Task2Thread(LPVOID lpParam) {
    // 获取主窗口句柄
    HWND hWnd = reinterpret_cast<HWND>(lpParam);

    // 检查句柄有效性
    if (!IsWindow(hWnd)) {
        return 1;
    }

    MoseLeftDownFlag = false;
    int EatCard = 0; // 记录吃卡次数
    bool 上次BOSS状态 = false;


    while (task2Running) {
        bool 当前BOSS状态 = imageRecognition(伤害图片, 伤害图片区域, 0.5);

        if (当前BOSS状态) {
            if (!上次BOSS状态) {
                MouseLeftDown();
                上次BOSS状态 = true;
            }
        }
        else {
            if (上次BOSS状态) {
                MouseLeftUp();
                Sleep(200);
                ClickRight();
                Sleep(200);
                ClickRight();
                Sleep(200);
                ClickRight();
                EatCard++;
                上次BOSS状态 = false;

                // 发送吃卡计数消息
                CString* pCardMsg = new CString;
                pCardMsg->Format(_T("已吃卡张数: %d"), EatCard);
                ::PostMessage(hWnd, WM_UPDATE_VALUE, (WPARAM)pCardMsg, 0);
            }
        }

        if (imageRecognition(确认, 确认图片区域, 0.5)) {
            ClickAt(960, 785);
        }
        Sleep(20);
    }

    if (MoseLeftDownFlag) {
        MouseLeftUp();
    }

    return 0;
}

// 杀死所有窗口标题为“穿越火线”的进程
void KillProcessByWindowTitle(const wchar_t* windowTitle)
{
    HWND hWnd = NULL;
    // 枚举所有窗口
    while ((hWnd = FindWindowExW(NULL, hWnd, NULL, windowTitle)) != NULL)
    {
        DWORD pid = 0;
        GetWindowThreadProcessId(hWnd, &pid);
        if (pid != 0)
        {
            HANDLE hProcess = OpenProcess(PROCESS_TERMINATE, FALSE, pid);
            if (hProcess)
            {
                TerminateProcess(hProcess, 0);
                CloseHandle(hProcess);
            }
        }
    }
}

