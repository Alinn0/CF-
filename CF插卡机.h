
// CF�忨��.h: PROJECT_NAME Ӧ�ó������ͷ�ļ�
//

#pragma once

#ifndef __AFXWIN_H__
	#error "�ڰ������ļ�֮ǰ���� 'pch.h' ������ PCH"
#endif

#include "resource.h"		// ������


// CCF�忨��App:
// �йش����ʵ�֣������ CF�忨��.cpp
//

class CCF�忨��App : public CWinApp
{
public:
	CCF�忨��App();

// ��д
public:
	virtual BOOL InitInstance();

// ʵ��

	DECLARE_MESSAGE_MAP()
};

extern CCF�忨��App theApp;
