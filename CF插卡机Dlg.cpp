#include "pch.h"
#include "framework.h"
#include "CF插卡机.h"
#include "CF插卡机Dlg.h"
#include "afxdialogex.h"
#include "cf.hpp"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

// CCF插卡机Dlg 对话框
int 星级 = 0, 卡片类型 = 0;
volatile int 放卡数量 = 0;

// 向前声明线程函数
DWORD WINAPI KeyMonitorThread(LPVOID lpParam);

CCF插卡机Dlg::CCF插卡机Dlg(CWnd* pParent /*=nullptr*/)
	: CDialogEx(IDD_CF_DIALOG, pParent)
{
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
}

void CCF插卡机Dlg::DoDataExchange(CDataExchange* pDX)
{
	CDialogEx::DoDataExchange(pDX);
	DDX_Control(pDX, IDC_COMBO1, 星级下拉框);
	DDX_Control(pDX, IDC_COMBO2, 卡片选择框);
	DDX_Control(pDX, IDC_EDIT2, 编辑框);
}

BEGIN_MESSAGE_MAP(CCF插卡机Dlg, CDialogEx)
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	ON_BN_CLICKED(IDC_BUTTON1, &CCF插卡机Dlg::OnBnClickedButton1)
	ON_CBN_SELCHANGE(IDC_COMBO1, &CCF插卡机Dlg::OnCbnSelchangeCombo1)
	ON_MESSAGE(WM_UPDATE_VALUE, &CCF插卡机Dlg::OnUpdateValue)
	ON_CBN_SELCHANGE(IDC_COMBO2, &CCF插卡机Dlg::OnCbnSelchangeCombo2)
	ON_EN_CHANGE(IDC_EDIT2, &CCF插卡机Dlg::OnEnChangeEdit2)
END_MESSAGE_MAP()

// CCF插卡机Dlg 消息处理程序

BOOL CCF插卡机Dlg::OnInitDialog()
{
	CDialogEx::OnInitDialog();

	// 设置此对话框的图标
	checkAdminRights();
	SetIcon(m_hIcon, TRUE);			// 设置大图标
	SetIcon(m_hIcon, FALSE);		// 设置小图标

	// 初始化下拉框
	星级下拉框.AddString(_T("一星"));
	星级下拉框.AddString(_T("二星"));
	星级下拉框.AddString(_T("三星"));
	星级下拉框.AddString(_T("四星"));
	星级下拉框.AddString(_T("五星"));
	星级下拉框.AddString(_T("六星"));
	星级下拉框.SetCurSel(0); // 默认选择一星

	卡片选择框.AddString(_T("第一张"));
	卡片选择框.AddString(_T("第二张"));
	卡片选择框.AddString(_T("第三张"));
	卡片选择框.AddString(_T("第四张"));
	卡片选择框.AddString(_T("第五张"));
	卡片选择框.SetCurSel(0); // 默认选择第一张
	编辑框.SetWindowText(_T("1000"));
	CenterWindow();
	放卡数量 = 1000;
	// 启动键盘监控线程，传递窗口句柄
	HANDLE hKeyThread = CreateThread(
		NULL,
		0,
		KeyMonitorThread,
		reinterpret_cast<LPVOID>(GetSafeHwnd()), // 关键修正：传递窗口句柄
		0,
		NULL
	);

	if (hKeyThread == NULL) {
		AfxMessageBox(_T("创建监控线程失败！"));
	}
	else {
		CloseHandle(hKeyThread); // 关闭线程句柄，防止泄露
	}

	return TRUE;  // 除非将焦点设置到控件，否则返回 TRUE
}

// 绘图代码保持不变
void CCF插卡机Dlg::OnPaint()
{
	if (IsIconic()) {
		CPaintDC dc(this); // 用于绘制的设备上下文
		SendMessage(WM_ICONERASEBKGND, reinterpret_cast<WPARAM>(dc.GetSafeHdc()), 0);
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;
		dc.DrawIcon(x, y, m_hIcon);
	}
	else {
		CDialogEx::OnPaint();
	}
}

HCURSOR CCF插卡机Dlg::OnQueryDragIcon()
{
	return static_cast<HCURSOR>(m_hIcon);
}

void CCF插卡机Dlg::OnBnClickedButton1()
{
	// 关闭当前程序
	KillProcessByWindowTitle(L"穿越火线");
}

void CCF插卡机Dlg::OnCbnSelchangeCombo1()
{
	星级 = 星级下拉框.GetCurSel(); // 获取选中的星级
}

void CCF插卡机Dlg::OnCbnSelchangeCombo2()
{
	卡片类型 = 卡片选择框.GetCurSel(); // 获取选中的卡片类型
}

// 消息处理函数 - 更新显示
LRESULT CCF插卡机Dlg::OnUpdateValue(WPARAM wParam, LPARAM lParam)
{
	CString* pStr = reinterpret_cast<CString*>(wParam); // 从wParam获取数据

	if (pStr != nullptr)
	{
		SetDlgItemText(IDC_STATIC11, *pStr); // 更新控件
		delete pStr; // 删除动态分配的内存
	}

	return 0;
}
void CCF插卡机Dlg::OnEnChangeEdit2()
{
	// TODO:  如果该控件是 RICHEDIT 控件，它将不
	// 发送此通知，除非重写 CDialogEx::OnInitDialog()
	// 函数并调用 CRichEditCtrl().SetEventMask()，
	// 同时将 ENM_CHANGE 标志“或”运算到掩码中。
	CString str;
	编辑框.GetWindowText(str); // 推荐用法，适合单行编辑框
	放卡数量 = _ttoi(str);
	
}
