from flask import Flask, request, jsonify
import queue
import threading
import time
import random
import uuid

# Producer class
class Producer:
    def __init__(self, message_queue, response_queue):
        self.message_queue = message_queue
        self.response_queue = response_queue

    def send_message(self, message, route_id, timeout=5):
        """Send a message to the message queue with a unique ID and wait for a response."""
        # Generate a unique GUID for this message
        guid = str(uuid.uuid4())
        message_payload = {'guid': guid, 'message': message, 'route_id': route_id}
        
        print(f"Producer: Sending message - {message_payload}")
        self.message_queue.put(message_payload)

        try:
            # Wait for the response from the consumer with a timeout
            while True:
                response = self.response_queue.get(timeout=timeout)
                # Check if the response corresponds to the current message's GUID
                if response['guid'] == guid:
                    break
        except queue.Empty:
            # If the response is not received within the timeout, return an error
            return {'status': 'error', 'message': 'Timeout waiting for response'}, 504

        # Return the response based on the consumer's processing result
        if response['status'] == 'success':
            return {'status': 'success', 'message': response['message']}, 200
        else:
            return {'status': 'error', 'message': response['message']}, 500

# Consumer class
class Consumer:
    def __init__(self, message_queue, response_queue):
        self.message_queue = message_queue
        self.response_queue = response_queue
        self.running = True

    def start(self):
        """Start the consumer thread."""
        self.thread = threading.Thread(target=self._consume, daemon=True)
        self.thread.start()

    def _consume(self):
        """Consume messages from the queue and process them."""
        while self.running:
            message_payload = self.message_queue.get()  # Get message from the queue
            if message_payload is None:
                # Stop processing if the special signal is received
                print("Consumer: No more messages to process.")
                self.response_queue.put({'status': 'success', 'message': 'Processing completed', 'guid': None})
                break

            # Extract the message, route_id, and GUID from the payload
            guid = message_payload['guid']
            message = message_payload['message']
            route_id = message_payload['route_id']

            # Simulate random success or error in processing
            if random.choice([True, False]):
                print(f"Consumer: Successfully processed message from {route_id} - {message}")
                response = {'status': 'success', 'message': f"Processed {message}", 'guid': guid}
            else:
                print(f"Consumer: Failed to process message from {route_id} - {message}")
                response = {'status': 'error', 'message': f"Failed to process {message}", 'guid': guid}

            # Send the response back to the response queue
            self.response_queue.put(response)
            time.sleep(2)  # Simulate processing time

    def stop(self):
        """Stop the consumer by sending a termination signal."""
        self.running = False
        self.message_queue.put(None)  # Send a termination signal to the consumer
        self.thread.join()  # Wait for the consumer thread to finish

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
