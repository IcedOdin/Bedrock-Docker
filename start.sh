#!/bin/bash
set -e

cd /bedrock

# Setup logs
mkdir -p logs
LOGFILE="logs/bedrock_$(date +%Y%m%d_%H%M%S).log"

# Download latest Bedrock server if not present
echo "Checking for the latest Bedrock server version..."
LATEST_INFO=$(curl -s https://www.minecraft.net/en-us/download/server/bedrock)
LATEST_URL=$(echo "$LATEST_INFO" | grep -oP 'https://minecraft\.azureedge\.net/bin-linux/bedrock-server-[\d\.]+\.zip' | head -n 1)
ZIP_NAME=$(basename "$LATEST_URL")

if [ ! -f "$ZIP_NAME" ]; then
    echo "Downloading $ZIP_NAME..."
    curl -o "$ZIP_NAME" "$LATEST_URL"
    unzip -o "$ZIP_NAME"
    rm "$ZIP_NAME"
    chmod +x bedrock_server
fi

# Start the server in the background and capture its PID
echo "Starting Minecraft Bedrock server..."
./bedrock_server > >(tee "$LOGFILE") 2>&1 &

# Save PID so Flask can write to server stdin
echo $! > bedrock_server.pid

# Start the Flask API
echo "Starting command API on port 5000..."
exec python3 /server_api.py
