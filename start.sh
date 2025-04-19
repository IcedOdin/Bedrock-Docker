#!/bin/bash
set -e

cd /bedrock

# Setup logs
mkdir -p logs
LOGFILE="logs/bedrock_$(date +%Y%m%d_%H%M%S).log"

mkdir -p downloads
# Download latest Bedrock server if not present
echo "Checking for the latest Bedrock server version..."
curl -H "Accept-Encoding: identity" -H "Accept-Language: en" -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.33 (KHTML, like Gecko) Chrome/90.0.$RandNum.212 Safari/537.33" -o downloads/version.html https://minecraft.net/en-us/download/server/bedrock/
DownloadURL=$(grep -o 'https://www.minecraft.net/bedrockdedicatedserver/bin-linux/[^"]*' downloads/version.html)
DownloadFile=$(echo "$DownloadURL" | sed 's#.*/##')


if [ ! -f "$DownloadFile" ]; then
    echo "Downloading $DownloadFile..."
    UserName=$(whoami)
    curl -H "Accept-Encoding: identity" -H "Accept-Language: en" -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.33 (KHTML, like Gecko) Chrome/90.0.$RandNum.212 Safari/537.33" -o "downloads/$DownloadFile" "$DownloadURL"
    unzip -o "downloads/$DownloadFile"
    rm "downloads/$DownloadFile"
    chmod +x bedrock_server
fi

python3 /server_api.py &

# Add this:
echo "Trying to start bedrock server..."
./bedrock_server || echo "Bedrock crashed with status $?"

# Keep container alive to inspect logs
sleep infinity
