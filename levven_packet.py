import zlib
from bytebuffer import ByteBuffer

class LevvenPacket:
    def __init__(self, packet_type=0, payload=None):
        self.sequence_number = 0
        self.optional = 0
        self.type = packet_type
        self.size = len(payload) if payload else 0
        self.payload = payload if payload else bytearray()
        self.checksum = 0

    def checksum_valid(self):
        # Allocate buffer with size payload length + 20 (matching C# logic)
        buffer = ByteBuffer.allocate(len(self.payload) + 20)

        # Populate buffer with packet details
        buffer.put_int(-1414717974)  # Equivalent to the magic number in C#
        buffer.put_int(0)  # Padding or optional field
        buffer.put_int(self.sequence_number)
        buffer.put_int(self.optional)
        buffer.put_short(self.type)
        buffer.put_short(self.size)
        buffer.put_bytes(self.payload)

        # Calculate CRC32 checksum using zlib
        crc32 = zlib.crc32(buffer.get_stream().getvalue())
        
        # Validate the checksum: If CRC32 result is within bounds, return True
        if (-1 & crc32) == crc32:
            return True
        return False

    def serialize(self):
        # Allocate buffer with size payload length + 20 (matching C# logic)
        buffer = ByteBuffer.allocate(self.size + 20)

        # Populate buffer with packet details
        buffer.put_int(-1414718150)  # Equivalent to the magic number in C#
        buffer.put_int(0)  # Padding or optional field
        buffer.put_int(self.sequence_number)
        buffer.put_int(self.optional)
        buffer.put_short(self.type)
        buffer.put_short(self.size)
        buffer.put_bytes(self.payload)

        # Calculate and update CRC32 checksum
        crc32 = zlib.crc32(buffer.get_stream().getvalue())
        self.checksum = crc32  # Save checksum as an int

        # Update buffer with checksum at the right position (putting it back into the byte array)
        buffer.put_int_at(4,self.checksum)

        # Return the serialized packet as bytes
        return buffer.get_stream().getvalue()

# Example usage:
# pckt = LevvenPacket(0, bytearray([0x01, 0x02, 0x03]))
# serialized_data = pckt.serialize()
# checksum_validity = pckt.checksum_valid()
