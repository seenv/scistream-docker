#!/bin/bash

# Remote host details
publisher_host="165.124.33.245"
scistream_host="165.124.33.240"
consumer_host="140.221.36.114"
username="anl"
ssh_key="~/.ssh/id_rsa"

# Python script to be executed remotely
python_script="get_metrics.py"

# Log file name
log_file="metrics.json"

# Transfer the Python script to the publisher host
scp -i "$ssh_key" "$python_script" "$username@$publisher_host:~/"
scp -i "$ssh_key" "$python_script" "$username@$scistream_host:~/"
scp -i "$ssh_key" "$python_script" "$username@$consumer_host:~/"

echo "transfered python files"

# Execute the Python script on the publisher host and retrieve the metrics
ssh -i "$ssh_key" "$username@$publisher_host" "python3 ~/get_metrics.py" > "publisher_pre_metrics.json" &
ssh -i "$ssh_key" "$username@$scistream_host" "python3 ~/get_metrics.py" > "scistream_pre_metrics.json" &
ssh -i "$ssh_key" "$username@$consumer_host" "python3 ~/get_metrics.py" > "consumer_pre_metrics.json" &
wait

echo "Metrics collected from the publisher host:"
cat "publisher_pre_metrics.json"
echo ""

echo "Metrics collected from the scistream host:"
cat "scistream_pre_metrics.json"
echo ""

echo "Metrics collected from the consumer host:"
cat "consumer_pre_metrics.json"
