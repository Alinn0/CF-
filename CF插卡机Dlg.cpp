#include "pch.h"
#include "framework.h"
#include "CF�忨��.h"
#include "CF�忨��Dlg.h"
#include "afxdialogex.h"
#include "cf.hpp"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

// CCF�忨��Dlg �Ի���
int �Ǽ� = 0, ��Ƭ���� = 0;
volatile int �ſ����� = 0;

// ��ǰ�����̺߳���
DWORD WINAPI KeyMonitorThread(LPVOID lpParam);

CCF�忨��Dlg::CCF�忨��Dlg(CWnd* pParent /*=nullptr*/)
	: CDialogEx(IDD_CF_DIALOG, pParent)
{
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
}

void CCF�忨��Dlg::DoDataExchange(CDataExchange* pDX)
{
	CDialogEx::DoDataExchange(pDX);
	DDX_Control(pDX, IDC_COMBO1, �Ǽ�������);
	DDX_Control(pDX, IDC_COMBO2, ��Ƭѡ���);
	DDX_Control(pDX, IDC_EDIT2, �༭��);
}

BEGIN_MESSAGE_MAP(CCF�忨��Dlg, CDialogEx)
	ON_WM_PAINT()
	ON_WM_QUERYDRAGICON()
	ON_BN_CLICKED(IDC_BUTTON1, &CCF�忨��Dlg::OnBnClickedButton1)
	ON_CBN_SELCHANGE(IDC_COMBO1, &CCF�忨��Dlg::OnCbnSelchangeCombo1)
	ON_MESSAGE(WM_UPDATE_VALUE, &CCF�忨��Dlg::OnUpdateValue)
	ON_CBN_SELCHANGE(IDC_COMBO2, &CCF�忨��Dlg::OnCbnSelchangeCombo2)
	ON_EN_CHANGE(IDC_EDIT2, &CCF�忨��Dlg::OnEnChangeEdit2)
END_MESSAGE_MAP()

// CCF�忨��Dlg ��Ϣ�������

BOOL CCF�忨��Dlg::OnInitDialog()
{
	CDialogEx::OnInitDialog();

	// ���ô˶Ի����ͼ��
	checkAdminRights();
	SetIcon(m_hIcon, TRUE);			// ���ô�ͼ��
	SetIcon(m_hIcon, FALSE);		// ����Сͼ��

	// ��ʼ��������
	�Ǽ�������.AddString(_T("һ��"));
	�Ǽ�������.AddString(_T("����"));
	�Ǽ�������.AddString(_T("����"));
	�Ǽ�������.AddString(_T("����"));
	�Ǽ�������.AddString(_T("����"));
	�Ǽ�������.AddString(_T("����"));
	�Ǽ�������.SetCurSel(0); // Ĭ��ѡ��һ��

	��Ƭѡ���.AddString(_T("��һ��"));
	��Ƭѡ���.AddString(_T("�ڶ���"));
	��Ƭѡ���.AddString(_T("������"));
	��Ƭѡ���.AddString(_T("������"));
	��Ƭѡ���.AddString(_T("������"));
	��Ƭѡ���.SetCurSel(0); // Ĭ��ѡ���һ��
	�༭��.SetWindowText(_T("1000"));
	CenterWindow();
	�ſ����� = 1000;
	// �������̼���̣߳����ݴ��ھ��
	HANDLE hKeyThread = CreateThread(
		NULL,
		0,
		KeyMonitorThread,
		reinterpret_cast<LPVOID>(GetSafeHwnd()), // �ؼ����������ݴ��ھ��
		0,
		NULL
	);

	if (hKeyThread == NULL) {
		AfxMessageBox(_T("��������߳�ʧ�ܣ�"));
	}
	else {
		CloseHandle(hKeyThread); // �ر��߳̾������ֹй¶
	}

	return TRUE;  // ���ǽ��������õ��ؼ������򷵻� TRUE
}

// ��ͼ���뱣�ֲ���
void CCF�忨��Dlg::OnPaint()
{
	if (IsIconic()) {
		CPaintDC dc(this); // ���ڻ��Ƶ��豸������
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

HCURSOR CCF�忨��Dlg::OnQueryDragIcon()
{
	return static_cast<HCURSOR>(m_hIcon);
}

void CCF�忨��Dlg::OnBnClickedButton1()
{
	// �رյ�ǰ����
	KillProcessByWindowTitle(L"��Խ����");
}

void CCF�忨��Dlg::OnCbnSelchangeCombo1()
{
	�Ǽ� = �Ǽ�������.GetCurSel(); // ��ȡѡ�е��Ǽ�
}

void CCF�忨��Dlg::OnCbnSelchangeCombo2()
{
	��Ƭ���� = ��Ƭѡ���.GetCurSel(); // ��ȡѡ�еĿ�Ƭ����
}

// ��Ϣ������ - ������ʾ
LRESULT CCF�忨��Dlg::OnUpdateValue(WPARAM wParam, LPARAM lParam)
{
	CString* pStr = reinterpret_cast<CString*>(wParam); // ��wParam��ȡ����

	if (pStr != nullptr)
	{
		SetDlgItemText(IDC_STATIC11, *pStr); // ���¿ؼ�
		delete pStr; // ɾ����̬������ڴ�
	}

	return 0;
}
void CCF�忨��Dlg::OnEnChangeEdit2()
{
	// TODO:  ����ÿؼ��� RICHEDIT �ؼ���������
	// ���ʹ�֪ͨ��������д CDialogEx::OnInitDialog()
	// ���������� CRichEditCtrl().SetEventMask()��
	// ͬʱ�� ENM_CHANGE ��־�������㵽�����С�
	CString str;
	�༭��.GetWindowText(str); // �Ƽ��÷����ʺϵ��б༭��
	�ſ����� = _ttoi(str);
	
}
