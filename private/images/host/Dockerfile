FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install netcat -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    iperf3 \
    iputils-ping \
    python3-pip \
    vim

# Copy and install the Python wheel
COPY scistream_proto-1.2.2-py3-none-any.whl  /scistream_proto-1.2.2-py3-none-any.whl 
RUN pip3 install /scistream_proto-1.2.2-py3-none-any.whl 

# Run any other setup commands
COPY cons.sh /cons.sh
COPY prod.sh /prod.sh
RUN chmod +x /cons.sh
RUN chmod +x /prod.sh

# Set default command to run
#CMD ["/cons.sh"]
