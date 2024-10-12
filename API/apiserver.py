from flask import Flask, request, jsonify

app = Flask(__name__)

# Mock spa state for testing
spa_state = {
    "connected": True,
    "temperatureF": 100,
    "setpointF": 102,
    "lights": "off",
    "pumps": {
        "1": "off",
        "2": "off",
        "3": "off",
        "4": "off",
        "5": "off",
    },
    "filter_status": 0,
    "filter_duration": 4,
    "filter_frequency": 2.0,
    "filter_suspension": False
}

# Mock API key for testing
API_KEY = "test_api_key"


def check_api_key():
    # Ensure the request contains a valid API key
    api_key = request.headers.get("X-API-KEY")
    return api_key != API_KEY


@app.route('/v2/spa/status', methods=['GET'])
def get_spa_status():
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(spa_state), 200


@app.route('/v2/spa/temperature', methods=['PUT'])
def set_spa_temperature():
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    new_setpoint = data.get('setpointF')

    if not (80 <= new_setpoint <= 104):
        return jsonify({"error": "Invalid setpoint", "accepted_range": "80-104"}), 422

    spa_state['setpointF'] = new_setpoint
    return jsonify({"message": "Temperature set successfully"}), 200


@app.route('/v2/spa/lights', methods=['PUT'])
def set_spa_lights():
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    state = data.get('state')
    if state not in ['on', 'off']:
        return jsonify({"error": "Invalid state"}), 422

    spa_state['lights'] = state
    return jsonify({"message": "Lights toggled successfully"}), 200


@app.route('/v2/spa/pumps/<pump>', methods=['PUT'])
def set_spa_pump(pump):
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    state = data.get('state')

    if pump not in spa_state['pumps'] and pump != "all":
        return jsonify({"error": "Pump not available"}), 404

    if state not in ['off', 'low', 'high']:
        return jsonify({"error": "Invalid state"}), 422

    if pump == "all":
        for p in spa_state['pumps']:
            spa_state['pumps'][p] = state
    else:
        spa_state['pumps'][pump] = state

    return jsonify({"message": f"Pump {pump} set to {state}"}), 200


@app.route('/v2/spa/filter', methods=['PUT'])
def set_filter_settings():
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    spa_state['filter_status'] = data.get('state', spa_state['filter_status'])
    spa_state['filter_duration'] = data.get('duration', spa_state['filter_duration'])
    spa_state['filter_frequency'] = data.get('frequency', spa_state['filter_frequency'])
    spa_state['filter_suspension'] = data.get('suspension', spa_state['filter_suspension'])

    return jsonify({"message": "Filter settings updated successfully"}), 200


if __name__ == '__main__':
    #debug must be false for vscode to work
    app.run(debug=False, port=5000,host='0.0.0.0')
