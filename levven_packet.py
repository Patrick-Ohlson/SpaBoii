
class LevvenPacket:
    def __init__(self, packet_type=0, payload=None):
        self.sequence_number = 0
        self.optional = 0
        self.type = packet_type
        self.size = len(payload) if payload else 0
        self.payload = payload if payload else []
        self.checksum = 0

    def checksum_valid(self):
        # Assuming checksum calculation is a sum of payload (this can vary depending on the C# implementation)
        calculated_checksum = sum(self.payload) % 256
        return calculated_checksum == self.checksum

    def serialize(self):
        # Serialize the object as a byte array (similar to the C# version)
        data = bytearray()
        data.extend(self.sequence_number.to_bytes(4, 'big'))
        data.extend(self.optional.to_bytes(4, 'big'))
        data.extend(self.type.to_bytes(2, 'big'))
        data.extend(self.size.to_bytes(2, 'big'))
        data.extend(self.payload)
        data.extend(self.checksum.to_bytes(4, 'big'))
        return data
