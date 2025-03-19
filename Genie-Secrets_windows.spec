# -*- mode: python ; coding: utf-8 -*-
 
import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
 
block_cipher = None
 
# Collect all data files
data_files = [('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\post-commit', 'hooks'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\post_commit.py', 'hooks'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\pre-commit', 'hooks'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\pre_commit.py', 'hooks'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\scan-repo', 'hooks'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\scan_repo.py', 'hooks'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\secretscan.log', 'hooks'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\.commit-reports\\repository-scan-report.html', 'hooks\\.commit-reports'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\.commit-reports\\scan-report.html', 'hooks\\.commit-reports'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\commit_scripts\\config.py', 'hooks\\commit_scripts'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\commit_scripts\\secretscan.log', 'hooks\\commit_scripts'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\commit_scripts\\secretscan.py', 'hooks\\commit_scripts'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\commit_scripts\\utils.py', 'hooks\\commit_scripts'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\commit_scripts\\__init__.py', 'hooks\\commit_scripts'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\commit_scripts\\templates\\report.html', 'hooks\\commit_scripts\\templates'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\commit_scripts\\__pycache__\\config.cpython-313.pyc', 'hooks\\commit_scripts\\__pycache__'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\commit_scripts\\__pycache__\\secretscan.cpython-313.pyc', 'hooks\\commit_scripts\\__pycache__'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\commit_scripts\\__pycache__\\utils.cpython-313.pyc', 'hooks\\commit_scripts\\__pycache__'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\hooks\\commit_scripts\\__pycache__\\__init__.cpython-313.pyc', 'hooks\\commit_scripts\\__pycache__'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\assets\\.DS_Store', 'assets'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\src\\assets\\logo.png', 'assets'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\resources\\qtwebengine_devtools_resources.pak', 'resources'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\resources\\qtwebengine_resources.pak', 'resources'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\resources\\qtwebengine_resources_100p.pak', 'resources'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\resources\\qtwebengine_resources_200p.pak', 'resources'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_ca.qm', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_de.qm', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_en.qm', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_es.qm', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_ka.qm', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_ko.qm', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_locales', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_pl.qm', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_ru.qm', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_uk.qm', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\translations\\qtwebengine_zh_CN.qm', 'translations'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\platforms\\qminimal.dll', 'PyQt6\\Qt6\\platforms'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\platforms\\qoffscreen.dll', 'PyQt6\\Qt6\\platforms'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\platforms\\qwindows.dll', 'PyQt6\\Qt6\\platforms'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\imageformats\\qgif.dll', 'PyQt6\\Qt6\\imageformats'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\imageformats\\qicns.dll', 'PyQt6\\Qt6\\imageformats'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\imageformats\\qico.dll', 'PyQt6\\Qt6\\imageformats'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\imageformats\\qjpeg.dll', 'PyQt6\\Qt6\\imageformats'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\imageformats\\qpdf.dll', 'PyQt6\\Qt6\\imageformats'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\imageformats\\qsvg.dll', 'PyQt6\\Qt6\\imageformats'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\imageformats\\qtga.dll', 'PyQt6\\Qt6\\imageformats'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\imageformats\\qtiff.dll', 'PyQt6\\Qt6\\imageformats'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\imageformats\\qwbmp.dll', 'PyQt6\\Qt6\\imageformats'), ('C:\\Users\\kesava.kondepudi\\Desktop\\Genie-NoAI\\venv\\Lib\\site-packages\\PyQt6\\Qt6\\plugins\\imageformats\\qwebp.dll', 'PyQt6\\Qt6\\imageformats')]
 
a = Analysis(
    [str(Path(r'C:\Users\kesava.kondepudi\Desktop\Genie-NoAI\src') / 'main.py')],
    pathex=[str(Path(r'C:\Users\kesava.kondepudi\Desktop\Genie-NoAI'))],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebChannel',
        'PyQt6.QtNetwork',
        'PyQt6.sip',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtCore'
    ],
    hookspath=[str(Path(r'C:\Users\kesava.kondepudi\Desktop\Genie-NoAI\src\hooks'))],
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
    [],
    exclude_binaries=True,
    name='Genie-Secrets',
    debug=False,
    bootloader_ignore_signals=True,  # Ignore signals to prevent console
    strip=False,
    upx=True,
    console=False,  # Set to False to hide console window
    disable_windowed_traceback=True,  # Prevent error popups
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(Path(r'C:\Users\kesava.kondepudi\Desktop\Genie-NoAI\src\assets') / 'logo.png'),
    uac_admin=False,  # Don't request admin privileges
    version='file_version_info.txt',  # Add version info
    win_private_assemblies=False,  # Prevent DLL loading issues
    runtime_tmpdir=None,  # Prevent temp directory creation
    argv_emulation=False,  # Prevent command line argument handling
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Genie-Secrets',
)
