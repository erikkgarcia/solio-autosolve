@echo off
REM Solio CLI - Scheduled Task Runner
REM This script is designed to be run by Windows Task Scheduler

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
REM Go up one level to project root
cd /d "%SCRIPT_DIR%.."

REM Run the automation (headless by default)
uv run solio

REM Log completion
echo [%date% %time%] Solio automation completed >> logs\scheduler.log
