import socket
import threading
import queue
import io
import time
from enum import Enum
from levven_packet import LevvenPacket  
import proto.spa_live_pb2 as SpaLive
import proto.SpaCommand_pb2 as SpaCommand
import proto.SpaInformation_pb2 as SpaInformation
import proto.spa_configuration_pb2 as SpaConfiguration

from HA_auto_mqtt import init as HA_init


from API.BL.producer import Producer
from API.BL.consumer import Consumer

global producer, consumer
global debug

debug=False

class MessageType(Enum):
    LIVE = 0x00
    COMMAND = 0x01
    PING = 0x0A
    INFORMATION = 0x30
    CONFIGURATION = 0x03

def get_message_title(value):
    try:
        return MessageType(value).name.title()  # Convert name to title case
    except ValueError:
        return f"\033[41;97mUnknown message type {value}\033[0m"

# Convert °F to °C and round to 2 decimal places
def temperature_F_to_C(temperatureInF):
    return round((temperatureInF- 32) * 5 / 9, 2)

# Create shared queues for messages and responses
cmd_queue = queue.Queue()
message_queue = queue.Queue()
response_queue = queue.Queue()

# Instantiate Producer and Consumer
producer = Producer(message_queue, response_queue, cmd_queue)
consumer = Consumer(message_queue, response_queue, cmd_queue)

# Initialize the sensors
sensors= HA_init(producer)

# Start the consumer
consumer.start()





state = 0
temp1 = temp2 = temp3 = 0
i = 0
packet = LevvenPacket()
debug=False
debug=True

def PingSpa(client, message_type = MessageType.LIVE.value):
    if debug:
        print(f"Sending {get_message_title(message_type)} ping with no content, type 0x{message_type:02X}:")
    pckt = LevvenPacket(message_type, bytearray())  # Initialize with type 0 and an empty payload
    #pckt = LevvenPacket(MessageType.LIVE.value, bytearray())  # Initialize with type 0 and an empty payload
    pack = LevvenToBytes(pckt)

    # Send the serialized packet over the TCP connection
    client.sendall(pack)

def LevvenToBytes(pckt):
    pack = pckt.serialize()  # Serialize the packet to bytes

    # Debug: Print the serialized packet as hex bytes
    if debug:
        hex_representation = ' '.join(f'{byte:02X}' for byte in pack)
        print(f"Serialized packet in hex ({len(pack)}): {hex_representation}")
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

    rawByte = b
    # Convert the input byte to a signed byte
    b = to_signed_byte(b)

    try:
        if state == 1:
            # Second byte of 4 byte magic number 0x AB AD 1D 3A
            state = 2 if rawByte == 0xAD else 0
            return
        elif state == 2:
            # Third byte of 4 byte magic number 0x AB AD 1D 3A
            state = 3 if rawByte == 0x1D else 0
            return
        elif state == 3:
            # Fourth byte of 4 byte magic number 0x AB AD 1D 3A
            state = 4 if rawByte == 0x3A else 0
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
            # First byte of 4 byte magic number 0x AB AD 1D 3A
            state = 1 if rawByte == 0xAB else 0
            return
    except Exception:
        state = 0

def receive(packet):
    """Handle the received packet (placeholder function)."""
    #print(f"Received packet: {packet}")

def send_packet_with_debug(spaIP,sensors):
    global debug
    # Create a TCP client socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server at IP 192.168.68.106 on port 65534
    client.connect((spaIP, 65534))
  

    
    i=0
    #get start time of loop
    start_time = time.time()
    while True:

        #handle commands

        try:
            cmd=producer.cmd_queue.get(timeout=1)
        except queue.Empty:
            cmd=None
        if cmd!=None:
            action=cmd["CMD"]
            closeservice=action.get("CloseService")
            newSetpointF=action.get("SetPoint")
            if closeservice != None:
                #exit SPABoii
                break
            if newSetpointF!=None:
                #set new setpoint
                print(f"Setpoint: {newSetpointF}°F")
                spacmd=SpaCommand.spa_command()
                #convert newSetpointF to fahrenheit int 
                
                newSetpointC=(newSetpointF*9/5)+32
                #convert to int
                newSetpointC=int(newSetpointC)
                


                
                spacmd.set_temperature_setpoint_fahrenheit=newSetpointC
                #convert spacmd proto to bytes
                buffer=spacmd.SerializeToString()
                pckt = LevvenPacket(MessageType.COMMAND.value, buffer)  # Initialize with type 1 (Command) and an empty payload
                if debug:
                    print(f"Sending new Setpoint Packet Type: {pckt.type}/0x{pckt.type:02X}")
                pack = LevvenToBytes(pckt)

                # Send the serialized packet over the TCP connection
                client.sendall(pack)
                
                #break

        # Request the configuration on start
        if i  == 0:
            PingSpa(client, MessageType.CONFIGURATION.value)
        # Request the spa information on start after short delay
        elif i  == 4:
            PingSpa(client, MessageType.INFORMATION.value)
        #if i  == 8:
        #    PingSpa(client, MessageType.PING.value)
        i += 1
        # Ping the spa every 4th iteration for keep alive
        if i % 4 == 0:
            PingSpa(client, MessageType.LIVE.value)


        temp = bytearray(2048)  # Declare the variable temp
        try:
            temp = client.recv(2048)  # Receive data from the server
            
        except Exception as e:
            #calculate time in minutes since start
            elapsed_minutes = (time.time() - start_time) / 60 /60
            print(f"Connection lost after {elapsed_minutes:.2f} hours")
            client.close()
            
            print("Restarting")
            
            
            #print(f"Error: {e}")
            break
        #print recieved data as hex
        hex_representation = ' '.join(f'{byte:02X}' for byte in temp)

        # Process the received data
        with io.BytesIO(temp) as net_stream:
            read_and_process_packets(net_stream)
            
        try:
            if debug:
                print(f"Packet Type: {packet.type}/0x{packet.type:02X} - {get_message_title(packet.type)}")

            if packet.type == MessageType.PING.value:
                # Nothing to see here, don't decode or debug print the packet
                continue
            pack=LevvenToBytes(packet)
        except Exception as e:
            pack=None
            continue

        if pack!=None:
            if packet.type == MessageType.INFORMATION.value:
                if debug:
                    print(f"\n{get_message_title(packet.type)}:\n")
                    bytes_result = bytes(packet.payload)
                    spa_information = SpaInformation.spa_information()
                    spa_information.ParseFromString(bytes_result)

                    print(f"Pack Serial Number: {spa_information.pack_serial_number}")
                    print(f"Pack Firmware Version: {spa_information.pack_firmware_version}")
                    print(f"Pack Hardware Version: {spa_information.pack_hardware_version}")
                    print(f"Pack Product ID: {spa_information.pack_product_id}")
                    print(f"Pack Board ID: {spa_information.pack_board_id}")
                    print(f"Topside Product ID: {spa_information.topside_product_id}")
                    print(f"Topside Software Version: {spa_information.topside_software_version}")
                    print(f"GUID: {spa_information.guid}")
                    print(f"Website Registration: {spa_information.website_registration}")
                    print(f"Website Registration Confirm: {spa_information.website_registration_confirm}")

                    mac_hex = ' '.join(f'{byte:02X}' for byte in spa_information.mac_address)
                    print(f"MAC Address: {mac_hex}")
                    print(f"Firmware Version: {spa_information.firmware_version}")
                    print(f"Product Code: {SpaInformation.PRODUCT_CODE.Name(spa_information.product_code)}")
                    print(f"Spa Type: {SpaInformation.SPA_TYPE.Name(spa_information.spa_type)}")
                continue
            elif packet.type == MessageType.CONFIGURATION.value:
                if debug:
                    print(f"\n{get_message_title(packet.type)}:\n")
                    bytes_result = bytes(packet.payload)
                    spa_configuration = SpaConfiguration.spa_configuration()
                    spa_configuration.ParseFromString(bytes_result)

                    print(f"Pump 1: {spa_configuration.pump_1}")
                    print(f"Pump 2: {spa_configuration.pump_2}")
                    print(f"Pump 3: {spa_configuration.pump_3}")
                    print(f"Pump 4: {spa_configuration.pump_4}")
                    print(f"Pump 5: {spa_configuration.pump_5}")
                    print(f"Lights: {spa_configuration.lights}")
                    print(f"Stereo: {spa_configuration.stereo}")
                    print(f"Heater 1: {spa_configuration.heater_1}")
                    print(f"Heater 2: {spa_configuration.heater_2}")
                    print(f"Filter: {spa_configuration.filter}")
                    print(f"Onzen: {spa_configuration.onzen}")
                    print(f"Smart Onzen: {spa_configuration.smart_onzen}")
                    print(f"Ozone Peak 1: {spa_configuration.ozone_peak_1}")
                    print(f"Ozone Peak 2: {spa_configuration.ozone_peak_2}")
                    print(f"Blower 1: {spa_configuration.blower_1}")
                    print(f"Blower 2: {spa_configuration.blower_2}")
                    print(f"Power: {SpaConfiguration.PHASE.Name(spa_configuration.powerlines)}")
                    print(f"Exhaust Fan: {spa_configuration.exhaust_fan}")
                    print(f"Breaker Size: {spa_configuration.breaker_size}")
                    print(f"Fogger: {spa_configuration.fogger}")
                continue
            elif packet.type == MessageType.LIVE.value:
                if debug:
                    print(f"\n{get_message_title(packet.type)}:\n")
                bytes_result = bytes(packet.payload)
                #print the bytes
                hex_representation = ' '.join(f'{byte:02}' for byte in bytes_result)                
                spa_live = SpaLive.spa_live()
                spa_live.ParseFromString(bytes_result)
                
                if debug==True:
                    print(f"Live Temperature: {temperature_F_to_C(spa_live.temperature_fahrenheit):.1f}°C {spa_live.temperature_fahrenheit}°F")
                    print(f"Setpoint Temperature: {temperature_F_to_C(spa_live.temperature_setpoint_fahrenheit):.1f}°C {spa_live.temperature_setpoint_fahrenheit}°F")
                    print(f"Filter: {SpaLive.FILTER_STATUS.Name(spa_live.filter)}")
                    print(f"Onzen: {spa_live.onzen}")
                    print(f"Ozone: {SpaLive.OZONE_STATUS.Name(spa_live.ozone).lstrip('OZONE_')}")
                    print(f"Blower 1: {SpaLive.PUMP_STATUS.Name(spa_live.blower_1)}")
                    print(f"Blower 2: {SpaLive.PUMP_STATUS.Name(spa_live.blower_2)}")
                    print(f"Pump 1: { SpaLive.PUMP_STATUS.Name(spa_live.pump_1) }")
                    print(f"Pump 2: {SpaLive.PUMP_STATUS.Name(spa_live.pump_2)}")
                    print(f"Pump 3: {SpaLive.PUMP_STATUS.Name(spa_live.pump_3) }")
                    status_str = ', '.join(f"{name} = {value}" for value, name in SpaLive.HEATER_STATUS.items())
                    print(f"Heater Status Options: {status_str}")
                    print(f"Heater 1: {SpaLive.HEATER_STATUS.Name(spa_live.heater_1)}")
                    print(f"Heater 2: {SpaLive.HEATER_STATUS.Name(spa_live.heater_2)}")
                    print(f"Lights: {spa_live.lights}")
                    print(f"All On: {spa_live.all_on}")
                    print(f"Economy: {spa_live.economy}")
                    print(f"Exhaust Fan: {spa_live.exhaust_fan}")

                    print(f"Heater ADC: {spa_live.heater_adc}")
                    print(f"Current ADC: {spa_live.current_adc}")
                
                live_json={
                    "SetPoint": temperature_F_to_C(spa_live.temperature_setpoint_fahrenheit),
                    "SetPoint_F": spa_live.temperature_setpoint_fahrenheit,
                    "Temperature": temperature_F_to_C(spa_live.temperature_fahrenheit),
                    "Temperature_F": spa_live.temperature_fahrenheit,
                    "Filter": SpaLive.FILTER_STATUS.Name(spa_live.filter),
                    "Onzen": SpaLive.OZONE_STATUS.Name(spa_live.onzen).lstrip("OZONE_"),
                    "Blower 1": SpaLive.PUMP_STATUS.Name(spa_live.blower_1),
                    "Blower 2": SpaLive.PUMP_STATUS.Name(spa_live.blower_2),
                    "Pump 1": SpaLive.PUMP_STATUS.Name(spa_live.pump_1),
                    "Pump 2": SpaLive.PUMP_STATUS.Name(spa_live.pump_2),
                    "Pump 3": SpaLive.PUMP_STATUS.Name(spa_live.pump_3),
                    "Heater 1": SpaLive.HEATER_STATUS.Name(spa_live.heater_1),
                    "Heater 2": SpaLive.HEATER_STATUS.Name(spa_live.heater_2),
                    "Light": spa_live.lights,
                    "All On": spa_live.all_on,
                    "Current ADC": spa_live.current_adc
                    }
                
                status=producer.send_message(live_json, "SPABoii.Live")
                #print(status)

                #get value by name Temperature from list
                for name, sensor in sensors:
                    if debug:
                        print(f"HA Sensor Name: {name}")#, Value: {sensor}")
                    if name=="Temperature":
                        temp=live_json.get("Temperature")
                        sensor.set_state(temp)
                    if name=="SetPoint":
                        temp=live_json.get("SetPoint")
                        #round to 2 decimals
                        temp=round(temp,2)
                        if temp>9:
                            sensor.set_value(temp)
                    if name=="Heater1":
                        heaterStatus = SpaLive.HEATER_STATUS.Name(spa_live.heater_1)

                        if heaterStatus == "HEATING" or heaterStatus == "WARMUP":
                            sensor.on()
                        else:
                            sensor.off()
                    if name=="Pump1":
                        if debug:
                            print(f"Publishing Pump1 state");
                        sensor.mqtt_client.publish("hmd/select/SPABoii-Pump1/state", SpaLive.PUMP_STATUS.Name(spa_live.pump_1), False)
            

                
                
                

                
                
                

    
    client.close()







while True:
    try:
        spaIP="192.168.68.106" #get_spa()
        print (f"Spa IP: {spaIP}")
        send_packet_with_debug(spaIP,sensors=sensors)
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nCtrl-C detected. Exiting gracefully...")
        break  # Exit the loop gracefully
    except Exception as e:
        continue




