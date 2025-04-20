FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y curl unzip screen libcurl4 libssl3 libnss3 libnss3-tools libatomic1 jq python3 python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Flask for the HTTP API
RUN pip3 install flask
RUN pip install gunicorn

# Create working directory
WORKDIR /bedrock

# Copy scripts
COPY start.sh /start.sh
COPY . /app
WORKDIR /app
RUN chmod +x /start.sh

# Volume for data persistence
VOLUME ["/bedrock"]

EXPOSE 19132/udp
EXPOSE 19133/udp
# Flask API
EXPOSE 50000  

CMD ["/start.sh"]

