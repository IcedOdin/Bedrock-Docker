FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y curl unzip libcurl4 libssl3 libnss3 libnss3-tools libatomic1 jq python3 python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Flask for the HTTP API
RUN pip3 install flask

# Create working directory
WORKDIR /bedrock

# Copy scripts
COPY start.sh /start.sh
COPY server_api.py /server_api.py
RUN chmod +x /start.sh

# Volume for data persistence
VOLUME ["/bedrock"]

EXPOSE 19132/udp
EXPOSE 19133/udp
EXPOSE 5000/tcp  # Flask API

CMD ["/start.sh"]

