#!/bin/bash

# Start Xvfb virtual display
echo "Starting virtual display (Xvfb)..."
Xvfb :99 -screen 0 1366x768x24 > /dev/null 2>&1 &
XVFB_PID=$!

# Give Xvfb time to start
sleep 2

# Export display
export DISPLAY=:99

# Run the scraper with provided arguments
echo "Starting ImmoCalcul scraper with virtual display..."
cd /app
python3 sheet_processor.py "$@"

# Capture exit code
EXIT_CODE=$?

# Cleanup Xvfb
echo "Cleaning up virtual display..."
kill $XVFB_PID 2>/dev/null || true
wait $XVFB_PID 2>/dev/null || true

exit $EXIT_CODE
