FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
        curl unzip screen libcurl4 libssl3 libnss3 libnss3-tools \
        libatomic1 jq python3 python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir flask gunicorn

# Create working directory for Bedrock server
WORKDIR /bedrock

# Volume for persistent data
VOLUME ["/bedrock"]

# Copy app
#COPY . /app
COPY main.py bedrock/app/
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Set app working directory
#WORKDIR /app

# Expose Bedrock ports
EXPOSE 19132/udp
EXPOSE 19133/udp

# Expose Flask API port
EXPOSE 50000

# Start script
#CMD ["/start.sh"]
ENTRYPOINT ["/start.sh"]
