import queue
import threading
import time
import random
import uuid



# Consumer class
class Consumer:
    def __init__(self, message_queue, response_queue,cmd_queue):
        self.message_queue = message_queue
        self.response_queue = response_queue
        self.cmd_queue = cmd_queue
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
            success = False

            #handle messages
            if route_id == "SPABoii.CloseService":
                self.cmd_queue.put("CloseService")
                print("Consumer: CloseService command recieved")
                success = True

            # Simulate random success or error in processing
            #if random.choice([True, False]):
            if success:
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