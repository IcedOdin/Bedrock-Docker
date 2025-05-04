#!/bin/bash
set -e

cd /bedrock


# Setup logs
mkdir -p logs
PIPE_PATH="/bedrock/server_input"

# Avoid "file exists" error
if [[ ! -p "$PIPE_PATH" ]]; then
    mkfifo "$PIPE_PATH"
fi

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

# Setup Server Resources
# Creating Files the Hard Way
echo "Creating app files......"
mkdir -p static
mkdir -p templates
cd ../

cp main.py /bedrock/
cp custom.js /bedrock/static/
cp console.html settings.html layout.html /bedrock/templates/

cd bedrock/

echo "Loading Environment Settings ...."
python3 -c "from main import apply_env_to_server_properties; apply_env_to_server_properties()"
echo "server.properties updated ...."
# Start Bedrock server
echo "Starting Bedrock server..."
# Keep the pipe open with a background tail that never exits
tail -f "$PIPE_PATH" | ./bedrock_server > /bedrock/logs/latest.log 2>&1 &
BEDROCK_PID=$!
echo "$BEDROCK_PID" > /bedrock/bedrock_server.pid



# Start the Flask API with Gunicorn in the background
echo "Starting Flask API with Gunicorn..."
gunicorn --bind 0.0.0.0:50000 'main:app' > /bedrock/logs/api.log 2>&1 &

# Wait and confirm services
sleep 5
echo "Bedrock server and API should now be running."

# Keep container alive and stream logs
tail -f /bedrock/logs/latest.log
