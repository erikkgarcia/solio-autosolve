@echo off
REM Solio AutoSolve - Scheduled Task Runner
REM This script is designed to be run by Windows Task Scheduler

cd /d "C:\Users\erknud3\PythonProjects\solio-autosolve"

REM Run the automation in headless mode
uv run solio --headless

REM Log completion
echo [%date% %time%] Solio automation completed >> logs\scheduler.log
