from flask import Flask, request, jsonify
import queue
import threading
import time
import random
import uuid
from BL.producer import Producer
from BL.consumer import Consumer

# Create shared queues for messages and responses
message_queue = queue.Queue()
response_queue = queue.Queue()

# Instantiate Producer and Consumer
producer = Producer(message_queue, response_queue)
consumer = Consumer(message_queue, response_queue)

# Start the consumer
consumer.start()

# Create the Flask app
app = Flask(__name__)

# Define four send_message routes, each with a different route ID
@app.route('/send_message_1', methods=['GET'])
def send_message_1():
    return handle_message_request('route_1')

@app.route('/send_message_2', methods=['POST'])
def send_message_2():
    return handle_message_request('route_2')

@app.route('/send_message_3', methods=['POST'])
def send_message_3():
    return handle_message_request('route_3')

@app.route('/send_message_4', methods=['POST'])
def send_message_4():
    return handle_message_request('route_4')

def handle_message_request(route_id):
    """Common handler for the send message routes."""
    #content = request.json
    message="SPABoii testbed" 
    #message = jsonify({'message': 'No message provided'}) #content.get('message', '')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Use the producer to send the message with the given route ID and wait for the response
    response, status_code = producer.send_message(message, route_id)
    return jsonify(response), status_code

# Route to gracefully shut down the consumer
@app.route('/shutdown', methods=['GET'])
def shutdown():
    consumer.stop()
    return jsonify({'message': 'Consumer shutdown completed'}), 200

# Run the Flask app
if __name__ == '__main__':
    #debug must be false for vscode to work
    app.run(debug=False, port=5000,host='0.0.0.0')
