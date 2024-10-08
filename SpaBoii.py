
import socket
from levven_packet import LevvenPacket  # Assuming you have saved the LevvenPacket class in a module

def send_packet_with_debug():
    # Create a TCP client socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server at IP 192.168.68.106 on port 65534
    #client.connect(("192.168.68.106", 65534))

    # Prepare the LevvenPacket
    pckt = LevvenPacket(0, bytearray())  # Initialize with type 0 and an empty payload
    pack = pckt.serialize()  # Serialize the packet to bytes

    # Debug: Print the serialized packet as hex bytes
    hex_representation = ' '.join(f'{byte:02X}' for byte in pack)
    print(f"Serialized packet in hex: {hex_representation}")

    # Send the serialized packet over the TCP connection
    #client.sendall(pack)

    # Optionally close the connection after sending
    #client.close()

# Example usage:
# send_packet_with_debug()



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
send_packet_with_debug()
