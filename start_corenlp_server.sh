#!/bin/bash

# Stanford CoreNLP Server Startup Script
# This script starts the Stanford CoreNLP server with all necessary annotators

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORENLP_DIR="$SCRIPT_DIR/stanford-corenlp-4.5.5"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Stanford CoreNLP Server Startup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if Stanford CoreNLP directory exists
if [ ! -d "$CORENLP_DIR" ]; then
    echo -e "${RED}ERROR: Stanford CoreNLP not found at $CORENLP_DIR${NC}"
    echo -e "${YELLOW}Please download Stanford CoreNLP 4.5.5 and extract it to the project root.${NC}"
    echo ""
    echo "Download from: https://nlp.stanford.edu/software/stanford-corenlp-4.5.5.zip"
    exit 1
fi

# Check if port 9000 is already in use
if lsof -Pi :9000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}WARNING: Port 9000 is already in use${NC}"
    echo ""
    read -p "Do you want to kill the existing process? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing process on port 9000..."
        lsof -ti:9000 | xargs kill -9
        sleep 2
    else
        echo "Exiting. Please stop the existing process first."
        exit 1
    fi
fi

# Change to CoreNLP directory
cd "$CORENLP_DIR" || exit 1

echo ""
echo -e "${GREEN}Starting Stanford CoreNLP server...${NC}"
echo -e "${YELLOW}Configuration:${NC}"
echo "  - Port: 9000"
echo "  - Memory: 4GB"
echo "  - Timeout: 30 seconds"
echo "  - Annotators: tokenize, ssplit, pos, lemma, ner, depparse, coref"
echo ""
echo -e "${YELLOW}The server will start in the background.${NC}"
echo -e "${YELLOW}Check server status: curl http://localhost:9000${NC}"
echo -e "${YELLOW}View logs: tail -f corenlp_server.log${NC}"
echo -e "${YELLOW}Stop server: ./stop_corenlp_server.sh${NC}"
echo ""

# Start server in background
nohup java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
    -port 9000 \
    -timeout 30000 \
    -annotators tokenize,ssplit,pos,lemma,ner,depparse,coref \
    > corenlp_server.log 2>&1 &

SERVER_PID=$!

# Wait a moment for server to start
echo "Waiting for server to start..."
sleep 5

# Check if server is running
if curl -s http://localhost:9000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Stanford CoreNLP server started successfully!${NC}"
    echo -e "${GREEN}✓ Server PID: $SERVER_PID${NC}"
    echo -e "${GREEN}✓ Server URL: http://localhost:9000${NC}"
    echo ""
    echo "Server is ready for use."

    # Save PID to file for stop script
    echo $SERVER_PID > corenlp_server.pid
else
    echo -e "${RED}✗ Failed to start Stanford CoreNLP server${NC}"
    echo "Check corenlp_server.log for details:"
    tail -20 corenlp_server.log
    exit 1
fi
