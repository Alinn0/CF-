#include "pch.h"
#include "cf.hpp"
#include "CF�忨��Dlg.h" // �����Ի���ͷ�ļ�

// ��Դ�ļ�·��
const std::string BOSS�ٻ� = "Boss.png";
const int BOSSͼƬ����[4] = { 1240, 780, 200, 40 };
const std::string ȷ�� = "configuration.png";
const int ȷ��ͼƬ����[4] = { 850, 760, 200, 40 };
const std::string  �˺�ͼƬ = "dps.png";
const int �˺�ͼƬ����[4] = { 613, 141, 63, 12 };

// ȫ�ֱ���
bool MoseLeftDownFlag = false;
bool task1Running = false;  // �ſ���ǹ�¼�����״̬
bool task2Running = false;  // BOSS��ǹ�¼�����״̬
HANDLE hTaskThread = NULL;  // �����߳̾��

/* int main() {
    // ������ԱȨ��
    checkAdminRights();

    // ������������߳�
    HANDLE hKeyThread = CreateThread(NULL, 0, KeyMonitorThread, NULL, 0, NULL);
    if (hKeyThread == NULL) {
        printf("Create key monitor thread failed with error: %d\n", GetLastError());
        return 1;
    }
    printf("��Ϸ�ֱ��ʣ�ȫ��1920 * 1080������ֱ������Ҳ��1920 * 1080��������������100%����Ϸ�����hud�Ŵ�\n");
    printf("\n��Ҫ�����뽫��������Ϊ����Ҽ�\n\n");
    printf("������������ʹ�����°������ƣ�\n");
    printf("F9 - �л�����������״̬\n");
    printf("F11 - ����/ֹͣ�ſ���ǹ�¼�\n");
    printf("F12 - ����/ֹͣBOSS��ǹ�¼�\n");
    printf("�ұ�Ctrl - �����Ǽ��Ϳ�Ƭֵ\n");
    printf("Ŀǰ�Ǽ���1��  ��Ƭ����һ��\n");
    printf("���ſ�������1000\n");

    // ��ѭ�����ȴ��������
    while (1) {
        Sleep(1000);  // ��ֹCPUռ�ù���
    }

    return 0;
} */

cv::Mat captureScreenRegion(const int region[4]) {
    // ������������ȡ����
    int x = region[0];
    int y = region[1];
    int width = region[2];
    int height = region[3];

    // ��������Ч��
    if (width <= 0 || height <= 0) {
        return cv::Mat();  // ���ؿ�ͼ��
    }

    // �������½�����
    int right = x + width;
    int bottom = y + height;

    // ��ȡ��Ļ�豸������
    HDC hScreenDC = GetDC(NULL);
    HDC hMemoryDC = CreateCompatibleDC(hScreenDC);

    // ��������λͼ
    HBITMAP hBitmap = CreateCompatibleBitmap(hScreenDC, width, height);
    HBITMAP hOldBitmap = (HBITMAP)SelectObject(hMemoryDC, hBitmap);

    // ������Ļ�����ڴ�DC
    BitBlt(hMemoryDC, 0, 0, width, height, hScreenDC, x, y, SRCCOPY);

    // ����OpenCV Mat����
    cv::Mat mat(height, width, CV_8UC4);

    // ����λͼ��Ϣͷ
    BITMAPINFOHEADER bmi = { 0 };
    bmi.biSize = sizeof(BITMAPINFOHEADER);
    bmi.biWidth = width;
    bmi.biHeight = -height;  // ���ű�ʾ���ϵ��µ�DIB
    bmi.biPlanes = 1;
    bmi.biBitCount = 32;      // 32λɫ�ʣ�BGRA��
    bmi.biCompression = BI_RGB;

    // ת��λͼ���ݵ�OpenCV Mat
    GetDIBits(hMemoryDC, hBitmap, 0, height,
        mat.data, (BITMAPINFO*)&bmi, DIB_RGB_COLORS);

    // ������Դ
    SelectObject(hMemoryDC, hOldBitmap);
    DeleteObject(hBitmap);
    DeleteDC(hMemoryDC);
    ReleaseDC(NULL, hScreenDC);

    // ��BGRAת��ΪBGR���Ƴ�alphaͨ����
    cv::Mat bgrMat;
    cv::cvtColor(mat, bgrMat, cv::COLOR_BGRA2BGR);

    return bgrMat;
}

bool imageRecognition(const std::string& templateImageName, const int region[4], double confid){
    // 1. ��ȡ��Ļָ������
    cv::Mat capturedImage = captureScreenRegion(region);
    if (capturedImage.empty()) {
        std::cerr << "��Ļ��ͼʧ��!" << std::endl;
        return 0;
    }

    // 2. ��ȡģ��ͼ��
    cv::Mat templateImage = cv::imread(templateImageName, cv::IMREAD_COLOR);
    if (templateImage.empty()) {
        std::cerr << "�޷�����ģ��ͼ��: " << templateImageName << std::endl;
        return 0;
    }

    // 3. ����ģ��ƥ��ȣ�ʹ�ù�һ�����ϵ������
    cv::Mat result;
    int result_cols = capturedImage.cols - templateImage.cols + 1;
    int result_rows = capturedImage.rows - templateImage.rows + 1;

    if (result_cols <= 0 || result_rows <= 0) {
        std::cerr << "ģ��ͼ��Ƚ�ȡ�����!" << std::endl;
        return 0;
    }

    result.create(result_rows, result_cols, CV_32FC1);

    // ִ��ģ��ƥ��
    cv::matchTemplate(capturedImage, templateImage, result, cv::TM_CCOEFF_NORMED);

    // 4. �������ƥ���
    double minVal, maxVal;
    cv::Point minLoc, maxLoc;
    cv::minMaxLoc(result, &minVal, &maxVal, &minLoc, &maxLoc);

    // 5. ��ѡ�����ӻ����ƥ��λ��
#ifdef VISUALIZE_RESULT
    cv::rectangle(capturedImage,
        cv::Rect(maxLoc.x, maxLoc.y, templateImage.cols, templateImage.rows),
        cv::Scalar(0, 0, 255), 2);
    cv::imshow("ƥ����", capturedImage);
    cv::waitKey(1000);
#endif
	//printf("ƥ���: %f\n", maxVal);
    if(maxVal> confid){
        return true;
    }
    else {
        return false; // ���ƥ��ȵ�����ֵ������false
    }

}



DWORD WINAPI KeyMonitorThread(LPVOID lpParam) {
    // ��ȡ���ݵ������ھ��
    HWND hWnd = reinterpret_cast<HWND>(lpParam);

    // �������Ч��
    if (!IsWindow(hWnd)) {
        return 1;
    }

    while (true)
    {
        // F9 ��������
        if (GetAsyncKeyState(VK_F9) & 0x8000) {
            while (GetAsyncKeyState(VK_F9) & 0x8000) Sleep(50);

            INPUT input = { 0 };
            input.type = INPUT_MOUSE;
            input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
            SendInput(1, &input, sizeof(INPUT));

        }

        // F11 ��������
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

                // ���������̲߳����ݴ��ھ��
                hTaskThread = CreateThread(
                    NULL,
                    0,
                    Task1Thread,
                    hWnd, // ���ݴ��ھ���������߳�
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

            // ����״̬��Ϣ

        }

        // F12 ��������
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

                // ���������̲߳����ݴ��ھ��
                hTaskThread = CreateThread(
                    NULL,
                    0,
                    Task2Thread,
                    hWnd, // ���ݴ��ھ���������߳�
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

    // ����Ƿ��ǹ���ԱȨ��
    if (OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &hToken)) {
        TOKEN_ELEVATION elevation;
        DWORD cbSize = sizeof(TOKEN_ELEVATION);

        if (GetTokenInformation(hToken, TokenElevation, &elevation, sizeof(elevation), &cbSize)) {
            isAdmin = elevation.TokenIsElevated;
        }
        CloseHandle(hToken);
    }

    // �ǹ���ԱȨ����������
    if (!isAdmin) {
        wchar_t exePath[MAX_PATH];
        GetModuleFileNameW(NULL, exePath, MAX_PATH);

        // ���������������һ������ - ��������·����
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

        // �����Թ���Ա�������
        if (ShellExecuteExW(&sei)) {
            LocalFree(argv);
            ExitProcess(0); // �����˳���ǰ�ǹ���Ա����
        }

        LocalFree(argv);
    }
}

// �������λ�ã��������ƶ��¼���
void SetMousePosition(int x, int y) {
    INPUT input = { 0 };
    input.type = INPUT_MOUSE;
    input.mi.dx = (x * 65535) / (GetSystemMetrics(SM_CXSCREEN) - 1);
    input.mi.dy = (y * 65535) / (GetSystemMetrics(SM_CYSCREEN) - 1);
    input.mi.dwFlags = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE | MOUSEEVENTF_VIRTUALDESK;
    SendInput(1, &input, sizeof(INPUT));
}

// �����Ļָ��λ�ã��������+�ͷţ�
void ClickAt(int x, int y) {
    // �������λ��
    SetMousePosition(x, y);

    // ׼������¼�
    INPUT inputs[2] = { 0 };

    // �������
    inputs[0].type = INPUT_MOUSE;
    inputs[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;

    // ����ͷ�
    inputs[1].type = INPUT_MOUSE;
    inputs[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;

    // ���͵���¼�
    SendInput(2, inputs, sizeof(INPUT));
}

// ��ָ������������м������ְ�ť��
void ClickRight() {
    // �������λ��

    // ׼������¼�
    INPUT inputs[2] = { 0 };

    // �м������¼�
    inputs[0].type = INPUT_MOUSE;
    inputs[0].mi.dwFlags = MOUSEEVENTF_RIGHTDOWN;

    // �м��ͷ��¼�
    inputs[1].type = INPUT_MOUSE;
    inputs[1].mi.dwFlags = MOUSEEVENTF_RIGHTUP;

    // ���͵���¼�
    SendInput(2, inputs, sizeof(INPUT));
}

// ����������
void MouseLeftDown() {
	if (MoseLeftDownFlag) return; // ����������Ѿ����£�ֱ�ӷ���
    INPUT input = { 0 };
    input.type = INPUT_MOUSE;
    input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
    SendInput(1, &input, sizeof(INPUT));
	MoseLeftDownFlag = true; // �������������±�־
}

// �ͷ�������
void MouseLeftUp() {
    if (!MoseLeftDownFlag) return; // ����������Ѿ����£�ֱ�ӷ���
    INPUT input = { 0 };
    input.type = INPUT_MOUSE;
    input.mi.dwFlags = MOUSEEVENTF_LEFTUP;
    SendInput(1, &input, sizeof(INPUT));
	MoseLeftDownFlag = false; // �������������±�־
}

// ������̰���������+�ͷţ�
void PressKey(BYTE vkCode) {
    INPUT inputs[2] = { 0 };

    // ��������
    inputs[0].type = INPUT_KEYBOARD;
    inputs[0].ki.wVk = vkCode;

    // �����ͷ�
    inputs[1].type = INPUT_KEYBOARD;
    inputs[1].ki.wVk = vkCode;
    inputs[1].ki.dwFlags = KEYEVENTF_KEYUP;

    SendInput(2, inputs, sizeof(INPUT));
}

// ���¼��̰���
void KeyDown(BYTE vkCode) {
    INPUT input = { 0 };
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = vkCode;
    SendInput(1, &input, sizeof(INPUT));
}

// �ͷż��̰���
void KeyUp(BYTE vkCode) {
    INPUT input = { 0 };
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = vkCode;
    input.ki.dwFlags = KEYEVENTF_KEYUP;
    SendInput(1, &input, sizeof(INPUT));
}

// �ſ���ǹ�¼��߳�
DWORD WINAPI Task1Thread(LPVOID lpParam) {
    // ��ȡ�����ھ��
    bool E״̬ = false;
    HWND hWnd = reinterpret_cast<HWND>(lpParam);

    // �������Ч��
    if (!IsWindow(hWnd)) {
        return 1;
    }

    MoseLeftDownFlag = false;
    int ReleaseCard = 0; // �ͷſ�Ƭ����
    bool �ϴ�BOSSͼƬ״̬ = false; // �ϴ�BOSSͼƬ״̬


    while (task1Running) {
        if (imageRecognition(ȷ��, ȷ��ͼƬ����, 0.5)) {
            ClickAt(960, 785);
        }

        bool BOSS = imageRecognition(�˺�ͼƬ, �˺�ͼƬ����, 0.5);
        if (BOSS != �ϴ�BOSSͼƬ״̬) {
            if (!BOSS) {
                MouseLeftUp();
                Sleep(200);
                ClickRight();
                Sleep(200);
                ClickRight();
                Sleep(200);
                ClickRight();
                �ϴ�BOSSͼƬ״̬ = false;
                E״̬ = false;
            }
        }

        if (BOSS) {
            MouseLeftDown();
            �ϴ�BOSSͼƬ״̬ = true;
        }
        else {
            // ���ͷſ���Ϣ
            if (!E״̬) {
                PressKey(0x45); // ��E��
                Sleep(200);

                if (imageRecognition(BOSS�ٻ�, BOSSͼƬ����, 0.5)) {
                    ClickAt(590 + �Ǽ� * 150, 367); // ����Ǽ�
                    Sleep(200);
                    ClickAt(630 + ��Ƭ���� * 200, 540); // �����Ƭ
                    Sleep(200);

                    if (imageRecognition(BOSS�ٻ�, BOSSͼƬ����, 0.5)) {
                        Sleep(100);

                        if (imageRecognition(BOSS�ٻ�, BOSSͼƬ����, 0.5)) {
                            if (ReleaseCard < �ſ�����) {
                                ClickAt(1346, 806); // ����ſ���ť
                                E״̬ = true;
                                ReleaseCard++;
                                CString* pCountMsg = new CString;
                                pCountMsg->Format(_T("�ͷſ�Ƭ����: %d/%d"), ReleaseCard, �ſ�����);
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

// ���boss��ǹ�¼��߳�
DWORD WINAPI Task2Thread(LPVOID lpParam) {
    // ��ȡ�����ھ��
    HWND hWnd = reinterpret_cast<HWND>(lpParam);

    // �������Ч��
    if (!IsWindow(hWnd)) {
        return 1;
    }

    MoseLeftDownFlag = false;
    int EatCard = 0; // ��¼�Կ�����
    bool �ϴ�BOSS״̬ = false;


    while (task2Running) {
        bool ��ǰBOSS״̬ = imageRecognition(�˺�ͼƬ, �˺�ͼƬ����, 0.5);

        if (��ǰBOSS״̬) {
            if (!�ϴ�BOSS״̬) {
                MouseLeftDown();
                �ϴ�BOSS״̬ = true;
            }
        }
        else {
            if (�ϴ�BOSS״̬) {
                MouseLeftUp();
                Sleep(200);
                ClickRight();
                Sleep(200);
                ClickRight();
                Sleep(200);
                ClickRight();
                EatCard++;
                �ϴ�BOSS״̬ = false;

                // ���ͳԿ�������Ϣ
                CString* pCardMsg = new CString;
                pCardMsg->Format(_T("�ѳԿ�����: %d"), EatCard);
                ::PostMessage(hWnd, WM_UPDATE_VALUE, (WPARAM)pCardMsg, 0);
            }
        }

        if (imageRecognition(ȷ��, ȷ��ͼƬ����, 0.5)) {
            ClickAt(960, 785);
        }
        Sleep(20);
    }

    if (MoseLeftDownFlag) {
        MouseLeftUp();
    }

    return 0;
}

// ɱ�����д��ڱ���Ϊ����Խ���ߡ��Ľ���
void KillProcessByWindowTitle(const wchar_t* windowTitle)
{
    HWND hWnd = NULL;
    // ö�����д���
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

