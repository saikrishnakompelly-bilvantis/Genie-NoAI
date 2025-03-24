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

REM Build the executable
pyinstaller --clean genie.spec

echo Build complete!
echo The executable can be found in the dist folder.
pause 