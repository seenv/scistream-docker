#!/bin/bash

# SSH connection details
publisher_host="165.124.33.245"
consumer_host="140.221.36.114"
username="anl"
ssh_key="~/.ssh/id_rsa"

# Check if fps argument is provided
if [ $# -eq 0 ]; then
    echo "Please provide the fps as an argument."
    exit 1
fi

fps=$1

# Check if an argument is provided
if [ $# -eq 1 ]; then
    queue_size=50000
    echo "No queue size argument provided. Using the default value of 50000."
else
    queue_size=$2
    echo "Using the provided queue size: $queue_size"
fi

# Start publishing data on the publisher node
ssh -i "$ssh_key" "$username@$publisher_host" "nohup /home/anl/miniconda3/bin/pvapy-ad-sim-server -cn pvapy:image -nx 512 -ny 512 -dt uint8 -rt 30 -fps $fps -dc -rp 1000 > /dev/null 2>&1 & "

if [ $? -eq 0 ]; then
    echo "Data publishing command sent successfully"
else
    echo "Failed to send data publishing command"
    exit 1
fi

# Check consumer behavior on the consumer node
log_filename="output_$(date +'%Y%m%d_%H%M%S').log"
ssh -i "$ssh_key" "$username@$consumer_host" "/home/anl/miniconda3/bin/pvapy-hpc-consumer --input-channel pvapy:image --control-channel consumer::control --status-channel consumer::status --output-channel consumer:\*:output --processor-class pvapy.hpc.userDataProcessor.UserDataProcessor --report-period 60 --server-queue-size 50000 --n-consumers 1 -dc --log-level info --runtime 45 --distributor-updates 1 > data/$log_filename 2>&1"

# Retrieve log files from the consumer node
scp -i "$ssh_key" "$username@$consumer_host:~/data/$log_filename" "./$log_filename"

if [ $? -eq 0 ]; then
    echo "Log file retrieved successfully"
else
    echo "Failed to retrieve log file"
    exit 1
fi
