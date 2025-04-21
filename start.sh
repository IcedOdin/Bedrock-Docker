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

# Start Minecraft Bedrock server in background
/bedrock/bedrock_server > /bedrock/logs/latest.log 2>&1 &
echo "Bedrock Server is running....."
# Save its PID so Flask can find it
echo $! > /bedrock/bedrock_server.pid
# Creating Files the Hard Way
echo "Creating app files......"
mkdir -p static
mkdir -p templates
cd ../
cp main.py /bedrock/main.py
cp custom.js /bedrock/static/custom.js
cp settings.html /bedrock/templates/settings.html
cp layout.html /bedrock/templates/layout.html
cd bedrock/

# Start Flask API with Gunicorn (4 workers, port 5000)
exec gunicorn -w 2 -b 0.0.0.0:50000 'main:app'
