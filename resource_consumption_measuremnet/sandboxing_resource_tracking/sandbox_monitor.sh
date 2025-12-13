#!/bin/bash

# Define the Docker command to run the sandbox
SANDBOX_COMMAND="docker run --rm -v $PWD/bin:/br2/bins --privileged --name sandbox_container arm-qemu:1.0-uclibc -i /br2/bins/a297356968802bf004cd99b1e2ce61c2327f01357b9f17a3f648ef5f5468c971.elf -r abc.exe -t 300"

# Define the output log file
LOG_FILE="sandbox_resource_usage_$(date '+%Y%m%d_%H%M%S').csv"

# Write CSV headers
echo "Timestamp,CPU_Usage(%),Memory_Usage(MB)" > $LOG_FILE

# Start the sandbox (Docker container) and ensure it has a unique name
$SANDBOX_COMMAND &
SANDBOX_PID=$!

# Wait a moment to ensure the container starts
sleep 2

# Check if the container started successfully
CONTAINER_ID=$(docker ps --filter "name=sandbox_container" --format "{{.ID}}")
if [ -z "$CONTAINER_ID" ]; then
    echo "Failed to start the Docker container. Exiting."
    exit 1
fi

echo "Sandbox container started with ID: $CONTAINER_ID"
echo "Monitoring CPU and Memory usage..."

# Monitor the sandbox container until it exits
while docker ps --filter "id=$CONTAINER_ID" --format "{{.ID}}" > /dev/null; do
    # Get the current timestamp
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # Capture CPU and Memory usage from `docker stats` (non-interactive mode)
    USAGE=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" $CONTAINER_ID)

    # Extract CPU and Memory usage
    CPU_USAGE=$(echo $USAGE | cut -d',' -f1 | tr -d '%' | awk '{printf "%.2f", $1}')
    MEMORY_USAGE=$(echo $USAGE | cut -d',' -f2 | awk -F'/' '{print $1}' | sed 's/[^0-9.]//g')

    # Append the usage data to the log file
    echo "$TIMESTAMP,$CPU_USAGE,$MEMORY_USAGE" >> $LOG_FILE

    # Sleep for 1 second before the next reading
    sleep 1
done

echo "Sandbox container with ID $CONTAINER_ID has terminated."
echo "Resource usage data logged to $LOG_FILE"

