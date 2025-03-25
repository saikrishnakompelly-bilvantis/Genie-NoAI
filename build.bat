@echo off
echo Building Genie application...

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Install requirements if not already installed
pip install -r requirements.txt

REM Convert logo.png to logo.ico if needed
REM You can use a tool like ImageMagick or an online converter to create logo.ico
REM Place the logo.ico file in src/assets/

REM Check if user wants an HSBC build
set HSBC_BUILD=false
if "%1"=="hsbc" (
    echo Building special HSBC environment version...
    set HSBC_BUILD=true
    
    REM Create an HSBC version spec file with forced fallback UI
    echo # -*- mode: python ; coding: utf-8 -*- > genie-hsbc.spec
    echo block_cipher = None >> genie-hsbc.spec
    echo a = Analysis(['src/main.py'], >> genie-hsbc.spec
    echo     pathex=[], >> genie-hsbc.spec
    echo     binaries=[], >> genie-hsbc.spec
    echo     datas=[('src/assets', 'assets'), ('src/hooks', 'hooks')], >> genie-hsbc.spec
    echo     hiddenimports=['PySide6.QtWidgets'], >> genie-hsbc.spec
    echo     hookspath=[], >> genie-hsbc.spec
    echo     hooksconfig={}, >> genie-hsbc.spec
    echo     runtime_hooks=[], >> genie-hsbc.spec
    echo     excludes=['PySide6.QtWebEngineCore'], >> genie-hsbc.spec
    echo     win_no_prefer_redirects=False, >> genie-hsbc.spec
    echo     win_private_assemblies=False, >> genie-hsbc.spec
    echo     cipher=block_cipher, >> genie-hsbc.spec
    echo     noarchive=False, >> genie-hsbc.spec
    echo ) >> genie-hsbc.spec
    echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher) >> genie-hsbc.spec
    echo exe = EXE(pyz, >> genie-hsbc.spec
    echo     a.scripts, >> genie-hsbc.spec
    echo     a.binaries, >> genie-hsbc.spec
    echo     a.zipfiles, >> genie-hsbc.spec
    echo     a.datas, >> genie-hsbc.spec
    echo     [], >> genie-hsbc.spec
    echo     name='Genie-HSBC', >> genie-hsbc.spec
    echo     debug=False, >> genie-hsbc.spec
    echo     bootloader_ignore_signals=False, >> genie-hsbc.spec
    echo     strip=False, >> genie-hsbc.spec
    echo     upx=True, >> genie-hsbc.spec
    echo     upx_exclude=[], >> genie-hsbc.spec
    echo     runtime_tmpdir=None, >> genie-hsbc.spec
    echo     console=False, >> genie-hsbc.spec
    echo     disable_windowed_traceback=False, >> genie-hsbc.spec
    echo     argv_emulation=False, >> genie-hsbc.spec
    echo     target_arch=None, >> genie-hsbc.spec
    echo     codesign_identity=None, >> genie-hsbc.spec
    echo     entitlements_file=None, >> genie-hsbc.spec
    echo     icon='src/assets/logo.ico' >> genie-hsbc.spec
    echo ) >> genie-hsbc.spec
    
    REM Build the HSBC version
    pyinstaller --clean genie-hsbc.spec
) else (
    REM Build the regular executable
    pyinstaller --clean genie.spec
)

echo Build complete!
if "%HSBC_BUILD%"=="true" (
    echo The HSBC version executable can be found at dist\Genie-HSBC.exe
) else (
    echo The executable can be found in the dist folder.
)
pause 