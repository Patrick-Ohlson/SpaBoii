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
        
        #check if message_queue is full
        if self.message_queue.length() != 0:
            return {'status': 'error', 'message': 'Message queue is full'}, 503



        print(f"Producer: Sending message - {message_payload}")
        self.message_queue.put(message_payload)  # Put the message in the queue

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