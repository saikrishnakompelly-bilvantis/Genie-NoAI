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

echo Build complete!
if "%HSBC_BUILD%"=="true" (
    echo The HSBC version executable can be found at dist\Genie-HSBC.exe
) else (
    echo The executable can be found in the dist folder.
)
pause 