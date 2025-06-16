# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['release.py'],  # 替换为你的主脚本文件名
    pathex=[], 
    binaries=[],
    datas=[
        ('config.json', '.')  # 包含配置文件
    ],
    hiddenimports=[
        'pynput.keyboard._win32',  # Windows 系统需要
        'pynput.mouse._win32',
        'pyautogui' 
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='窗口化CF',  # 生成的exe名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用UPX压缩
    runtime_tmpdir=None,
    console=False,  # 不显示控制台
    icon='CrossFire.ico',  # 可选图标文件
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True  # 请求管理员权限
)