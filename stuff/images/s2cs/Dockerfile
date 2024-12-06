FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    iperf3 \
    python3-pip \
    iputils-ping \
    fuse-overlayfs \
    gnupg \
    lsb-release \
    vim

# Add Docker’s official GPG key
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the Docker repository
RUN echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update and install docker-ce-cli
RUN apt-get update && apt-get install -y docker-ce-cli netcat

# Copy and install the Python wheel
COPY scistream_proto-1.2.2-py3-none-any.whl  /scistream_proto-1.2.2-py3-none-any.whl 
RUN pip3 install /scistream_proto-1.2.2-py3-none-any.whl 

# Run any other setup commands
COPY conss.sh /conss.sh
COPY prods.sh /prods.sh
RUN chmod +x /conss.sh
RUN chmod +x /prods.sh

# Set default command to run
#CMD ["/conss.sh"]