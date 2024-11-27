from flask import Flask, jsonify, request, send_from_directory
import subprocess
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')

LABELS_FILE = "peer_labels.json"


def load_labels():
    """Load labels from the peer_labels.json file."""
    if not os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, 'w') as f:
            json.dump({}, f)
    with open(LABELS_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_labels(labels):
    """Save updated labels to the peer_labels.json file."""
    with open(LABELS_FILE, 'w') as f:
        json.dump(labels, f)


def get_wg_status():
    """Retrieve the status of WireGuard peers using the `wg show all dump` command."""
    result = subprocess.run(["wg", "show", "all", "dump"], capture_output=True, text=True)
    peers = []
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        for line in lines[1:]:  # Skip the header
            data = line.split('\t')
            peer_info = {
                "peer": data[4][:-3],
                "allowed_ips": data[3].split(":")[0],
                "latest_handshake": datetime.utcfromtimestamp(int(data[5])).strftime("%Y-%m-%d %H:%M:%S"),
                "transfer_rx": data[5],
                "transfer_tx": data[6],
            }
            peers.append(peer_info)
    else:
        print("Error retrieving WireGuard status:", result.stderr)
    print("Retrieved peers:", peers)  # Debugging output
    return peers


@app.route('/')
def index():
    """Serve the index.html file."""
    return send_from_directory('static', 'index.html')


@app.route('/peers', methods=['GET'])
def peers():
    """Return the list of WireGuard peers with their labels."""
    labels = load_labels()  # Load labels from file
    peers = get_wg_status()  # Get live WireGuard peer data
    for peer in peers:
        peer['label'] = labels.get(peer['peer'], "Unknown")  # Match by IP address
    return jsonify(peers)


@app.route('/label', methods=['POST'])
def update_labels():
    """Update multiple labels."""
    try:
        updates = request.json  # Expecting an array of { peer, label }
        if not isinstance(updates, list):
            return jsonify({"error": "Invalid data format, expected a list"}), 400

        labels = load_labels()

        # Process each update
        for update in updates:
            peer = update.get('peer')
            label = update.get('label')
            if peer and label:
                labels[peer] = label

        save_labels(labels)  # Save all updates at once
        return jsonify({"success": True, "updated": len(updates)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug', methods=['GET'])
def debug_labels():
    """Debugging route to return the contents of peer_labels.json."""
    return jsonify(load_labels())


if __name__ == '__main__':
    # Run the app on all available interfaces
    app.run(host='0.0.0.0', port=5000)