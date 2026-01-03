#!/bin/bash
# Solio AutoSolve - Linux Scheduler Setup Script
# Sets up systemd timers to run the automation twice daily

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default times
MORNING_TIME="10:00"
EVENING_TIME="18:00"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --morning)
            MORNING_TIME="$2"
            shift 2
            ;;
        --evening)
            EVENING_TIME="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --morning TIME    Set morning run time (default: 10:00)"
            echo "  --evening TIME    Set evening run time (default: 18:00)"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                              # Use default times (10:00 and 18:00)"
            echo "  $0 --morning 08:00 --evening 20:00"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}Solio AutoSolve - Linux Scheduler${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""
echo -e "Project directory: ${GREEN}$PROJECT_DIR${NC}"
echo -e "Morning run time: ${GREEN}$MORNING_TIME${NC}"
echo -e "Evening run time: ${GREEN}$EVENING_TIME${NC}"
echo ""

# Make run script executable
chmod +x "$SCRIPT_DIR/run_scheduled.sh"
echo -e "${GREEN}✓${NC} Made run_scheduled.sh executable"

# Create systemd user directory if it doesn't exist
SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

# Create the service file
SERVICE_FILE="$SYSTEMD_DIR/solio-autosolve.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Solio AutoSolve - FPL Optimization
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$PROJECT_DIR
ExecStart=$SCRIPT_DIR/run_scheduled.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

echo -e "${GREEN}✓${NC} Created systemd service: $SERVICE_FILE"

# Create timer for morning run
MORNING_TIMER="$SYSTEMD_DIR/solio-autosolve-morning.timer"
cat > "$MORNING_TIMER" << EOF
[Unit]
Description=Solio AutoSolve - Morning Run

[Timer]
OnCalendar=*-*-* $MORNING_TIME:00
Persistent=true
Unit=solio-autosolve.service

[Install]
WantedBy=timers.target
EOF

echo -e "${GREEN}✓${NC} Created morning timer: $MORNING_TIMER"

# Create timer for evening run
EVENING_TIMER="$SYSTEMD_DIR/solio-autosolve-evening.timer"
cat > "$EVENING_TIMER" << EOF
[Unit]
Description=Solio AutoSolve - Evening Run

[Timer]
OnCalendar=*-*-* $EVENING_TIME:00
Persistent=true
Unit=solio-autosolve.service

[Install]
WantedBy=timers.target
EOF

echo -e "${GREEN}✓${NC} Created evening timer: $EVENING_TIMER"

# Reload systemd user daemon
systemctl --user daemon-reload
echo -e "${GREEN}✓${NC} Reloaded systemd daemon"

# Enable and start the timers
systemctl --user enable solio-autosolve-morning.timer
systemctl --user enable solio-autosolve-evening.timer
systemctl --user start solio-autosolve-morning.timer
systemctl --user start solio-autosolve-evening.timer

echo -e "${GREEN}✓${NC} Enabled and started timers"
echo ""

# Enable lingering so timers run even when not logged in
loginctl enable-linger "$USER"
echo -e "${GREEN}✓${NC} Enabled lingering (timers will run when not logged in)"
echo ""

echo -e "${BLUE}==================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}==================================${NC}"
echo ""
echo "Scheduled runs configured for:"
echo -e "  Morning: ${YELLOW}$MORNING_TIME${NC}"
echo -e "  Evening: ${YELLOW}$EVENING_TIME${NC}"
echo ""
echo "Useful commands:"
echo -e "  ${YELLOW}# Check timer status${NC}"
echo "  systemctl --user list-timers"
echo ""
echo -e "  ${YELLOW}# View recent logs${NC}"
echo "  journalctl --user -u solio-autosolve.service -n 50"
echo ""
echo -e "  ${YELLOW}# Run manually right now${NC}"
echo "  systemctl --user start solio-autosolve.service"
echo ""
echo -e "  ${YELLOW}# Or just use the CLI command${NC}"
echo "  uv run solio"
echo ""
echo -e "  ${YELLOW}# Disable timers${NC}"
echo "  systemctl --user stop solio-autosolve-morning.timer"
echo "  systemctl --user stop solio-autosolve-evening.timer"
echo "  systemctl --user disable solio-autosolve-morning.timer"
echo "  systemctl --user disable solio-autosolve-evening.timer"
echo ""
