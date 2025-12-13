#!/bin/bash

# Define the Python program to run
PYTHON_PROGRAM="python3 scaled_replay_single_ip.py"

# Define the output log file
LOG_FILE="python_resource_network_usage_$(date '+%Y%m%d_%H%M%S').csv"

# Write CSV headers
echo "Timestamp,CPU_Usage(%),Memory_Usage(MB),Bytes_Received(Bytes),Bytes_Sent(Bytes)" > $LOG_FILE

# Start the Python program and get its PID
$PYTHON_PROGRAM &
PYTHON_PID=$!

# Check if the Python program started successfully
if [ -z "$PYTHON_PID" ]; then
    echo "Failed to start the Python program. Exiting."
    exit 1
fi

echo "Python program started with PID: $PYTHON_PID"
echo "Monitoring CPU, Memory, and Network usage..."

# Monitor the Python program until it exits
while kill -0 $PYTHON_PID 2>/dev/null; do
    # Get the current timestamp
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # Capture CPU usage from `ps`
    CPU_USAGE=$(ps -p $PYTHON_PID -o %cpu --no-headers | awk '{printf "%.2f", $1}')

    # Capture memory usage in kilobytes from /proc/[pid]/statm
    if [ -e /proc/$PYTHON_PID/statm ]; then
        MEMORY_KB=$(awk '{print $2 * 4}' /proc/$PYTHON_PID/statm) # 4 KB per page
        MEMORY_MB=$(echo "$MEMORY_KB / 1024" | bc -l | awk '{printf "%.2f", $1}')
    else
        MEMORY_MB="0.00"
    fi

    # Append the usage data to the log file
    echo "$TIMESTAMP,$CPU_USAGE,$MEMORY_MB" >> $LOG_FILE

    # Sleep for 1 second before the next reading
    sleep 1
done

echo "Python program with PID $PYTHON_PID has terminated."
echo "Resource usage data logged to $LOG_FILE"

