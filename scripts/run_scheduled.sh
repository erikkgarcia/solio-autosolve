#!/bin/bash
# Solio CLI - Scheduled Run Script for Linux
# This script is designed to be called by systemd timers or cron

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create logs directory if it doesn't exist
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# Set log file with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/scheduled_run_$TIMESTAMP.log"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Log start time
echo "==================================" | tee -a "$LOG_FILE"
echo "Solio CLI - Scheduled Run" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run the automation (headless by default)
echo "Running: uv run solio" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

uv run solio 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

echo "" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"
echo "Finished at: $(date)" | tee -a "$LOG_FILE"
echo "Exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "==================================" | tee -a "$LOG_FILE"

# Keep only the last 30 log files
cd "$LOG_DIR" || exit 0
ls -t scheduled_run_*.log | tail -n +31 | xargs -r rm --

exit $EXIT_CODE
