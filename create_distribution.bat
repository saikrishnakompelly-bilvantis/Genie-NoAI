@echo off
echo Creating distribution package...

REM Create a temporary directory for packaging
mkdir temp_dist

REM Copy the executable
copy dist\Genie.exe temp_dist\

REM Create a README file
echo Genie - Secret Scanning Tool > temp_dist\README.txt
echo. >> temp_dist\README.txt
echo Installation Instructions: >> temp_dist\README.txt
echo 1. Extract all files from this zip >> temp_dist\README.txt
echo 2. Double-click Genie.exe to run the application >> temp_dist\README.txt
echo 3. Follow the on-screen instructions to install Git hooks >> temp_dist\README.txt
echo. >> temp_dist\README.txt
echo System Requirements: >> temp_dist\README.txt
echo - Windows 7 or later >> temp_dist\README.txt
echo - Git installed on your system >> temp_dist\README.txt
echo. >> temp_dist\README.txt
echo For support or questions, please contact your system administrator. >> temp_dist\README.txt

REM Create zip file
powershell Compress-Archive -Path temp_dist\* -DestinationPath Genie-Secrets.zip -Force

REM Clean up
rmdir /s /q temp_dist

echo Distribution package created successfully!
echo You can find Genie-Secrets.zip in the current directory.
pause 