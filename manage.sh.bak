#!/bin/bash

# A simple management script for the Discord RPG Bot

BOT_COMMAND="python3 bot.py"
PID_FILE="bot.pid"
LOG_FILE="bot.log"

# Function to check if the bot is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null; then
            return 0 # Process is running
        fi
    fi
    return 1 # Process is not running
}

# Function to start the bot
start() {
    if is_running; then
        echo "Bot is already running (PID: $(cat "$PID_FILE"))."
        return 1
    fi

    echo "Starting bot in the background..."
    nohup $BOT_COMMAND > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    # Give it a moment to start up
    sleep 2

    if is_running; then
        echo "Bot started successfully (PID: $(cat "$PID_FILE"))."
        echo "Output is being logged to $LOG_FILE."
    else
        echo "Failed to start the bot. Check $LOG_FILE for errors."
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop the bot
stop() {
    if ! is_running; then
        echo "Bot is not running."
        # Clean up stale PID file if it exists
        if [ -f "$PID_FILE" ]; then
            rm -f "$PID_FILE"
        fi
        return 1
    fi

    pid=$(cat "$PID_FILE")
    echo "Stopping bot (PID: $pid)..."
    kill $pid
    
    # Wait for the process to terminate
    sleep 2

    if is_running; then
        echo "Failed to stop the bot. Forcing kill..."
        kill -9 $pid
        sleep 2
    fi

    rm -f "$PID_FILE"
    echo "Bot stopped."
}

# Main script logic
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        echo "Restarting bot..."
        stop
        start
        ;;
    status)
        if is_running; then
            echo "Bot is running (PID: $(cat "$PID_FILE"))."
        else
            echo "Bot is not running."
        fi
        ;;
    log)
        echo "Displaying last 20 lines of the log file ($LOG_FILE):"
        tail -n 20 "$LOG_FILE"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|log}"
        exit 1
        ;;
esac

exit 0
