# SecretGenie Command Line Interface Wrapper (PowerShell)
# This script ensures console output is visible when using command-line arguments

param(
    [Parameter(Position=0)]
    [string]$Command,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if SecretGenie.exe exists in the same directory
$secretgenieExe = Join-Path $scriptDir "SecretGenie.exe"

if (-not (Test-Path $secretgenieExe)) {
    Write-Host "ERROR: SecretGenie.exe not found in $scriptDir" -ForegroundColor Red
    Write-Host "Please ensure this script is in the same directory as SecretGenie.exe" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Show usage if no arguments provided
if (-not $Command) {
    Write-Host "SecretGenie Command Line Interface" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\secretgenie-cli.ps1 /install      - Install SecretGenie hooks" -ForegroundColor White
    Write-Host "  .\secretgenie-cli.ps1 /uninstall    - Uninstall SecretGenie hooks" -ForegroundColor White
    Write-Host "  .\secretgenie-cli.ps1 --help        - Show help" -ForegroundColor White
    Write-Host ""
    Write-Host "To run the GUI version, double-click SecretGenie.exe directly" -ForegroundColor Gray
    Read-Host "Press Enter to exit"
    exit 0
}

# Check for command-line arguments
$validCliArgs = @("/install", "/uninstall", "--install", "--uninstall", "--help", "-h")

if ($Command -in $validCliArgs) {
    Write-Host "Running SecretGenie in command-line mode..." -ForegroundColor Green
    Write-Host ""
    
    # Build argument list
    $args = @($Command) + $RemainingArgs
    
    # Run the executable with all arguments
    $process = Start-Process -FilePath $secretgenieExe -ArgumentList $args -Wait -PassThru -NoNewWindow
    
    # Get the exit code
    $exitCode = $process.ExitCode
    
    # Show completion message
    Write-Host ""
    if ($exitCode -eq 0) {
        Write-Host "Command completed successfully." -ForegroundColor Green
    } else {
        Write-Host "Command failed with exit code $exitCode." -ForegroundColor Red
    }
    
    # Pause to keep console open
    Write-Host ""
    Read-Host "Press Enter to close this window"
    
    exit $exitCode
} else {
    # For other arguments or GUI mode, just start the GUI
    Write-Host "Starting SecretGenie in GUI mode..." -ForegroundColor Green
    Start-Process -FilePath $secretgenieExe -ArgumentList ($Command, $RemainingArgs)
    exit 0
} 