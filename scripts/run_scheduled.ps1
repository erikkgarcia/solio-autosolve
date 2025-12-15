<#
.SYNOPSIS
    Solio AutoSolve - Scheduled Task Runner (PowerShell version)
    
.DESCRIPTION
    This script is designed to be run by Windows Task Scheduler.
    It runs the Solio automation in headless mode and logs the results.
    
.NOTES
    To create a scheduled task, run setup_scheduled_task.ps1 as Administrator.
#>

$ErrorActionPreference = "Continue"

# Configuration
$ProjectDir = "C:\Users\erknud3\PythonProjects\solio-autosolve"
$LogDir = Join-Path $ProjectDir "logs"
$LogFile = Join-Path $LogDir "scheduler.log"

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Log function
function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    Add-Content -Path $LogFile -Value $LogMessage
    Write-Host $LogMessage
}

# Start
Write-Log "Starting Solio automation..."

try {
    # Change to project directory
    Set-Location $ProjectDir
    
    # Run the automation
    $Output = & uv run solio --headless 2>&1
    $ExitCode = $LASTEXITCODE
    
    # Log output
    foreach ($Line in $Output) {
        Write-Log "  $Line"
    }
    
    if ($ExitCode -eq 0) {
        Write-Log "Solio automation completed successfully."
    } else {
        Write-Log "Solio automation failed with exit code: $ExitCode"
    }
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
}

Write-Log "---"
