#!/bin/bash
# Development server startup script
# This script starts both Django and Celery workers together

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Bazary Development Server Launcher${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source bazary_env/bin/activate
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill 0
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Warning: Redis is not running!${NC}"
    echo -e "${YELLOW}   Celery tasks will queue but won't execute.${NC}"
    echo -e "${YELLOW}   Start Redis with: sudo systemctl start redis${NC}"
    echo ""
fi

# Start Celery worker in background
echo -e "${GREEN}🚀 Starting Celery worker...${NC}"
celery -A bazary worker -l info > logs/celery.log 2>&1 &
CELERY_PID=$!
echo -e "${GREEN}   Celery worker started (PID: $CELERY_PID)${NC}"
echo -e "${GREEN}   Logs: logs/celery.log${NC}"
echo ""

# Give Celery time to start
sleep 2

# Start Django development server
echo -e "${GREEN}🚀 Starting Django development server...${NC}"
python manage.py runserver
echo -e "${GREEN}   Django server started at http://localhost:8000${NC}"
echo ""

# Wait for both processes
wait