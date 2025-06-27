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
    
    REM Generate the HSBC spec file using Python
    python generate_spec.py
    
    REM Build the HSBC version
    pyinstaller --clean genie-hsbc.spec
) else (
    REM Build the regular executable
    pyinstaller --clean genie.spec
)

REM Copy CLI wrapper scripts to dist folder
echo Copying CLI wrapper scripts...
if "%HSBC_BUILD%"=="true" (
    copy secretgenie-cli.bat dist\secretgenie-cli.bat >nul 2>&1
    copy secretgenie-cli.ps1 dist\secretgenie-cli.ps1 >nul 2>&1
    echo CLI wrapper scripts copied to dist folder.
) else (
    copy secretgenie-cli.bat dist\secretgenie-cli.bat >nul 2>&1
    copy secretgenie-cli.ps1 dist\secretgenie-cli.ps1 >nul 2>&1
    echo CLI wrapper scripts copied to dist folder.
)

echo Build complete!
if "%HSBC_BUILD%"=="true" (
    echo The HSBC version executable can be found at dist\SecretGenie-HSBC.exe
    echo CLI wrappers: dist\secretgenie-cli.bat and dist\secretgenie-cli.ps1
) else (
    echo The executable can be found in the dist folder.
    echo CLI wrappers: dist\secretgenie-cli.bat and dist\secretgenie-cli.ps1
)
pause 