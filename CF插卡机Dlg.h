#pragma once
extern int 星级, 卡片类型;
extern volatile int 放卡数量;
#define WM_UPDATE_VALUE (WM_USER + 1)

// CCF插卡机Dlg 对话框
class CCF插卡机Dlg : public CDialogEx
{
	// 构造
public:
	CCF插卡机Dlg(CWnd* pParent = nullptr);	// 标准构造函数

	// 对话框数据
#ifdef AFX_DESIGN_TIME
	enum { IDD = IDD_CF_DIALOG };
#endif

protected:
	virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV 支持

	// 实现
protected:
	HICON m_hIcon;

	// 生成的消息映射函数
	virtual BOOL OnInitDialog();
	afx_msg void OnPaint();
	afx_msg HCURSOR OnQueryDragIcon();
	DECLARE_MESSAGE_MAP()
public:

	afx_msg void OnBnClickedButton1();
	CComboBox 星级下拉框;
	CComboBox 卡片选择框;
	afx_msg void OnCbnSelchangeCombo1();
	afx_msg LRESULT OnUpdateValue(WPARAM wParam, LPARAM lParam); // 修改参数顺序
	afx_msg void OnCbnSelchangeCombo2();
	CEdit 编辑框;
	afx_msg void OnEnChangeEdit2();
};