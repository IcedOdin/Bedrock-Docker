from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify(status="ok"), 200

@app.route('/command', methods=['POST'])
def send_command():
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'Missing "command" in request'}), 400

    command = data['command']
    try:
        with open('/proc/{}/fd/0'.format(get_server_pid()), 'w') as stdin:
            stdin.write(command + '\n')
        return jsonify({'status': 'Command sent', 'command': command})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_server_pid():
    try:
        with open("/bedrock/bedrock_server.pid") as f:
            return int(f.read().strip())
    except Exception as ex:
        raise Exception("Bedrock server PID not found: " + str(ex))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50000)

