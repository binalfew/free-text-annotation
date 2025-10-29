#!/bin/bash

# Stanford CoreNLP Server Stop Script
# This script stops the Stanford CoreNLP server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORENLP_DIR="$SCRIPT_DIR/stanford-corenlp-4.5.5"
PID_FILE="$CORENLP_DIR/corenlp_server.pid"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Stanford CoreNLP Server Stop${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    SERVER_PID=$(cat "$PID_FILE")
    echo "Found server PID: $SERVER_PID"

    # Check if process is running
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "Stopping Stanford CoreNLP server (PID: $SERVER_PID)..."
        kill $SERVER_PID

        # Wait for graceful shutdown
        sleep 3

        # Force kill if still running
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            echo "Process still running, forcing shutdown..."
            kill -9 $SERVER_PID
            sleep 1
        fi

        if ps -p $SERVER_PID > /dev/null 2>&1; then
            echo -e "${RED}✗ Failed to stop server${NC}"
            exit 1
        else
            echo -e "${GREEN}✓ Stanford CoreNLP server stopped successfully${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}Server process not found (PID: $SERVER_PID)${NC}"
        rm -f "$PID_FILE"
    fi
else
    echo -e "${YELLOW}PID file not found. Checking for CoreNLP processes...${NC}"

    # Check if any CoreNLP server is running on port 9000
    if lsof -Pi :9000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Found process on port 9000. Killing..."
        lsof -ti:9000 | xargs kill -9
        sleep 1
        echo -e "${GREEN}✓ Stopped process on port 9000${NC}"
    else
        echo "No Stanford CoreNLP server found running."
    fi
fi

echo ""
echo "Done."
