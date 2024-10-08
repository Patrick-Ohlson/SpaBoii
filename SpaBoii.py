import levven_packet
import socket

def get_spa():
    # Create a UDP socket
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Enable broadcasting
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Prepare and send the broadcast message
    request_data = "Query,BlueFalls,".encode('ascii')
    client.sendto(request_data, ('<broadcast>', 9131))

    # Receive the response (no explicit bind needed)
    server_response_data, server_ep = client.recvfrom(4096)
    
    # Decode the response and output the server's address and data
    server_response = server_response_data.decode('ascii')
    print(f"Located SPA at {server_ep[0]}: {server_response}")

    # Close the client socket
    client.close()




get_spa()
