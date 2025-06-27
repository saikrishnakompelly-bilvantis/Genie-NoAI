@echo off
rem SecretGenie Command Line Interface Wrapper
rem This batch file ensures console output is visible when using command-line arguments

rem Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

rem Check if SecretGenie.exe exists in the same directory
if exist "%SCRIPT_DIR%SecretGenie.exe" (
    set SECRETGENIE_EXE=%SCRIPT_DIR%SecretGenie.exe
) else (
    echo ERROR: SecretGenie.exe not found in %SCRIPT_DIR%
    echo Please ensure this batch file is in the same directory as SecretGenie.exe
    pause
    exit /b 1
)

rem Check if any arguments were provided
if "%~1"=="" (
    echo SecretGenie Command Line Interface
    echo.
    echo Usage:
    echo   %~nx0 /install      - Install SecretGenie hooks
    echo   %~nx0 /uninstall    - Uninstall SecretGenie hooks
    echo   %~nx0 --help        - Show help
    echo.
    echo To run the GUI version, double-click SecretGenie.exe directly
    pause
    exit /b 0
)

rem Check for command-line arguments
if /i "%~1"=="/install" goto :run_cli
if /i "%~1"=="/uninstall" goto :run_cli
if /i "%~1"=="--install" goto :run_cli
if /i "%~1"=="--uninstall" goto :run_cli
if /i "%~1"=="--help" goto :run_cli
if /i "%~1"=="-h" goto :run_cli

rem If we get here, run GUI mode
echo Starting SecretGenie in GUI mode...
start "" "%SECRETGENIE_EXE%"
exit /b 0

:run_cli
rem For command-line mode, we need to allocate a console and run synchronously
echo Running SecretGenie in command-line mode...
echo.

rem Run the executable with all arguments and wait for completion
"%SECRETGENIE_EXE%" %*

rem Capture the exit code
set EXIT_CODE=%ERRORLEVEL%

rem Show completion message
echo.
if %EXIT_CODE%==0 (
    echo Command completed successfully.
) else (
    echo Command failed with exit code %EXIT_CODE%.
)

rem Pause to keep console open so user can see the output
echo.
echo Press any key to close this window...
pause >nul

exit /b %EXIT_CODE% 