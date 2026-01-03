<#
.SYNOPSIS
    Sets up Windows Task Scheduler to run Solio automation on a schedule.
    
.DESCRIPTION
    Creates a scheduled task that runs the Solio FPL automation.
    By default, it runs daily at 7:00 AM.
    
.PARAMETER Time
    The time to run the task (default: "07:00")
    
.PARAMETER Daily
    Run once per day (default)
    
.PARAMETER Frequency
    How often to run: "Daily", "Twice" (7AM and 7PM), or "Custom"
    
.EXAMPLE
    .\setup_scheduled_task.ps1
    # Creates daily task at 7:00 AM
    
.EXAMPLE
    .\setup_scheduled_task.ps1 -Time "08:30"
    # Creates daily task at 8:30 AM
    
.EXAMPLE
    .\setup_scheduled_task.ps1 -Frequency "Twice"
    # Creates tasks at 7:00 AM and 7:00 PM
    
.NOTES
    Run this script as Administrator to create the scheduled task.
#>

param(
    [string]$Time = "07:00",
    [ValidateSet("Daily", "Twice", "Custom")]
    [string]$Frequency = "Daily"
)

$TaskName = "Solio FPL AutoSolve"
$TaskDescription = "Automatically runs Solio FPL optimization and sends email results"

# Derive paths from script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$ScriptPath = Join-Path $ScriptDir "run_scheduled.ps1"

# Check if running as administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $IsAdmin) {
    Write-Host "WARNING: Not running as Administrator. Task may not be created with full permissions." -ForegroundColor Yellow
    Write-Host "Consider re-running this script as Administrator." -ForegroundColor Yellow
    Write-Host ""
}

# Remove existing task if it exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Removing existing task '$TaskName'..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the action
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" -WorkingDirectory $ProjectDir

# Create trigger(s) based on frequency
$Triggers = @()

switch ($Frequency) {
    "Daily" {
        $Triggers += New-ScheduledTaskTrigger -Daily -At $Time
        Write-Host "Creating daily task at $Time"
    }
    "Twice" {
        $Triggers += New-ScheduledTaskTrigger -Daily -At "07:00"
        $Triggers += New-ScheduledTaskTrigger -Daily -At "19:00"
        Write-Host "Creating twice-daily task at 7:00 AM and 7:00 PM"
    }
    "Custom" {
        $Triggers += New-ScheduledTaskTrigger -Daily -At $Time
        Write-Host "Creating custom daily task at $Time"
    }
}

# Create settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Create principal (run as current user)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

# Register the task
try {
    Register-ScheduledTask -TaskName $TaskName -Description $TaskDescription -Action $Action -Trigger $Triggers -Settings $Settings -Principal $Principal
    
    Write-Host ""
    Write-Host "SUCCESS: Scheduled task '$TaskName' created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Schedule: $Frequency at $Time"
    Write-Host "  Script: $ScriptPath"
    Write-Host ""
    Write-Host "To manage the task:" -ForegroundColor Cyan
    Write-Host "  - Open Task Scheduler (taskschd.msc)"
    Write-Host "  - Find '$TaskName' in the Task Scheduler Library"
    Write-Host ""
    Write-Host "To test the task manually:" -ForegroundColor Cyan
    Write-Host "  schtasks /run /tn `"$TaskName`""
    Write-Host ""
    Write-Host "To remove the task:" -ForegroundColor Cyan
    Write-Host "  Unregister-ScheduledTask -TaskName `"$TaskName`""
}
catch {
    Write-Host "ERROR: Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
