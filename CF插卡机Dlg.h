#pragma once
extern int �Ǽ�, ��Ƭ����;
extern volatile int �ſ�����;
#define WM_UPDATE_VALUE (WM_USER + 1)

// CCF�忨��Dlg �Ի���
class CCF�忨��Dlg : public CDialogEx
{
	// ����
public:
	CCF�忨��Dlg(CWnd* pParent = nullptr);	// ��׼���캯��

	// �Ի�������
#ifdef AFX_DESIGN_TIME
	enum { IDD = IDD_CF_DIALOG };
#endif

protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV ֧��

	// ʵ��
protected:
	HICON m_hIcon;

	// ���ɵ���Ϣӳ�亯��
	virtual BOOL OnInitDialog();
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	DECLARE_MESSAGE_MAP()
public:

	afx_msg void OnBnClickedButton1();
	CComboBox �Ǽ�������;
	CComboBox ��Ƭѡ���;
	afx_msg void OnCbnSelchangeCombo1();
	afx_msg LRESULT OnUpdateValue(WPARAM wParam, LPARAM lParam); // �޸Ĳ���˳��
	afx_msg void OnCbnSelchangeCombo2();
	CEdit �༭��;
	afx_msg void OnEnChangeEdit2();
};