
import socket
import threading
import queue
import io
from levven_packet import LevvenPacket  
import proto.spa_live_pb2 as SpaLive

# Create shared queues for messages and responses
message_queue = queue.Queue()
response_queue = queue.Queue()



state = 0
temp1 = temp2 = temp3 = 0
i = 0
packet = LevvenPacket()
debug=False

def PingSpa(client):
    pckt = LevvenPacket(0, bytearray())  # Initialize with type 0 and an empty payload
    pack = LevvenToBytes(pckt)

    # Send the serialized packet over the TCP connection
    client.sendall(pack)

def LevvenToBytes(pckt):
    pack = pckt.serialize()  # Serialize the packet to bytes

    # Debug: Print the serialized packet as hex bytes
    if debug:
        hex_representation = ' '.join(f'{byte:02X}' for byte in pack)
        print(f"Serialized packet in hex: {hex_representation}")
    return pack

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
    if debug:
        print(f"Located SPA at {server_ep[0]}: {server_response}")

    # Close the client socket
    client.close()
    return server_ep[0]

def read_and_process_packets(net_stream):
    # Simulating MemoryStream using BytesIO
    ms = io.BytesIO()
    data = bytearray(2048)
    
    # Read from the network stream
    while True:
        num_bytes_read = net_stream.readinto(data)
        if num_bytes_read == 0:
            break
        ms.write(data[:num_bytes_read])
        if num_bytes_read < len(data):
            break

    # Get the full byte array from the memory stream
    bytes_data = ms.getvalue()
    hex_representation = ' '.join(f'{byte:02X}' for byte in bytes_data)
    # Process each byte by calling handle_packets
    for item in bytes_data:
        handle_packets(item)

def get_int(b1, b2, b3, b4):
    """Convert four bytes to an integer."""
    return (b1 << 24) | (b2 << 16) | (b3 << 8) | b4

def get_short(b1, b2):
    """Convert two bytes to a short."""
    return (b1 << 8) | b2

def get_int(b1, b2, b3, b4):
    """Convert four bytes to an integer."""
    return (b1 << 24) | (b2 << 16) | (b3 << 8) | b4

def get_short(b1, b2):
    """Convert two bytes to a short."""
    return (b1 << 8) | b2

def to_signed_byte(value):
    """Convert a byte (0-255) to a signed byte (-128 to 127)."""
    if value > 127:
        return value - 256
    return value

def handle_packets(b):
    global state, temp1, temp2, temp3, i, packet

    # Convert the input byte to a signed byte
    b = to_signed_byte(b)

    try:
        if state == 1:
            state = 2 if b == -83 else 0
            return
        elif state == 2:
            state = 3 if b == 29 else 0
            return
        elif state == 3:
            state = 4 if b == 58 else 0
            return
        elif state == 4:
            temp1 = b
            state = 5
            return
        elif state == 5:
            temp2 = b
            state = 6
            return
        elif state == 6:
            temp3 = b
            state = 7
            return
        elif state == 7:
            packet.checksum = get_int(temp1, temp2, temp3, b)
            state = 8
            return
        elif state == 8:
            temp1 = b
            state = 9
            return
        elif state == 9:
            temp2 = b
            state = 10
            return
        elif state == 10:
            temp3 = b
            state = 11
            return
        elif state == 11:
            packet.sequence_number = get_int(temp1, temp2, temp3, b)
            state = 12
            return
        elif state == 12:
            temp1 = b
            state = 13
            return
        elif state == 13:
            temp2 = b
            state = 14
            return
        elif state == 14:
            temp3 = b
            state = 15
            return
        elif state == 15:
            packet.optional = get_int(temp1, temp2, temp3, b)
            state = 16
            return
        elif state == 16:
            temp3 = b
            state = 17
            return
        elif state == 17:
            packet.type = get_short(temp3, b)
            state = 18
            return
        elif state == 18:
            temp3 = b
            state = 19
            return
        elif state == 19:
            i = 0
            packet.size = get_short(temp3, b)
            packet.payload = bytearray(packet.size)
            if packet.size == 0:
                receive(packet)
                state = 0
                return
            state = 20
            return
        elif state == 20:
            packet.payload[i] = b & 0xFF  # Convert to unsigned byte for storage
            i += 1
            if i >= packet.size:
                receive(packet)
                state = 0
            return
        else:
            packet = LevvenPacket()
            state = 1 if b == -85 else 0
            return
    except Exception:
        state = 0

def receive(packet):
    """Handle the received packet (placeholder function)."""
    #print(f"Received packet: {packet}")

def send_packet_with_debug(spaIP):
    # Create a TCP client socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server at IP 192.168.68.106 on port 65534
    client.connect((spaIP, 65534))
  

    
    i=0
    while True:
        #ping the spa every 4th iteration
        if i%4==0:
            i=0
            PingSpa(client)
        i+=1


        temp = bytearray(2048)  # Declare the variable temp
        temp=client.recv(2048)

        #print recieved data as hex
        hex_representation = ' '.join(f'{byte:02X}' for byte in temp)

        # Process the received data
        with io.BytesIO(temp) as net_stream:
            read_and_process_packets(net_stream)
            
        try:
            pack=LevvenToBytes(packet)
        except Exception as e:
            
            pack=None
            continue
        if pack!=None:
            print(f"Packet: {packet.type}")
            if packet.type==48:
                #print("Configurations")
                continue
            elif packet.type==0:
                print("\n\nLive:\n")
                bytes_result = bytes(packet.payload)
                #print the bytes
                hex_representation = ' '.join(f'{byte:02}' for byte in bytes_result)                
                spa_live = SpaLive.spa_live()
                spa_live.ParseFromString(bytes_result)
                

                

                print(f"Temperature: {(spa_live.temperature_fahrenheit-32)* 5 / 9}")
                print(f"Filter: {SpaLive.FILTER_STATUS.Name(spa_live.filter)}")
                print(f"Onzen: {SpaLive.OZONE_STATUS.Name(spa_live.onzen).lstrip('OZONE_')}")
                print(f"BLower 1: {SpaLive.PUMP_STATUS.Name(spa_live.blower_1)}")
                print(f"BLower 2: {SpaLive.PUMP_STATUS.Name(spa_live.blower_2)}")
                print(f"Pump 1: { SpaLive.PUMP_STATUS.Name(spa_live.pump_1) }")
                print(f"Pump 2: {SpaLive.PUMP_STATUS.Name(spa_live.pump_2)}")
                print(f"Pump 3: {SpaLive.PUMP_STATUS.Name(spa_live.pump_3) }")
                print(f"Heater 1: {SpaLive.HEATER_STATUS.Name(spa_live.heater_1)}")
                print(f"Heater 1: {SpaLive.HEATER_STATUS.Name(spa_live.heater_2)}")
                print(f"Light: {spa_live.lights}")
                print(f"All On: {spa_live.all_on}")

                print(f"Current ADC: {spa_live.current_adc}")

                #convert spa_live to json string
                
                
                if message_queue.full() == False:
                    message_queue.put(spa_live)
                
                
                

    
    client.close()



spaIP="192.168.68.106"#get_spa()
print (f"Spa IP: {spaIP}")
send_packet_with_debug(spaIP)




