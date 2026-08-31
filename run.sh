#!/bin/bash
# Helper runner script for Auto Video Generation & TikTok Publishing Bot
# Sets up working directory, environment, and logs

PROJECT_DIR="/Users/yes/Desktop/auto_video"
PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.14/bin/python3"
LOG_FILE="$PROJECT_DIR/logs/cron.log"

cd "$PROJECT_DIR" || exit 1

# Ensure logs directory exists
mkdir -p "$PROJECT_DIR/logs"

echo "========================================================" >> "$LOG_FILE"
echo "🚀 Auto-Video Run Started at $(date)" >> "$LOG_FILE"
echo "========================================================" >> "$LOG_FILE"

"$PYTHON_BIN" "$PROJECT_DIR/main.py" >> "$LOG_FILE" 2>&1

echo "🏁 Run Finished at $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
