#!/bin/bash

set -e

cd /bedrock

# Get latest version info
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
else
    echo "Bedrock server already downloaded."
fi

echo "Starting Minecraft Bedrock server..."
exec ./bedrock_server
