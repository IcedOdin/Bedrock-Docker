FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y curl unzip libcurl4 libssl3 libnss3 libnss3-tools libatomic1 jq && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /bedrock

# Add startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create volume for persistent data
VOLUME ["/bedrock"]

EXPOSE 19132/udp
EXPOSE 19133/udp

CMD ["/start.sh"]
