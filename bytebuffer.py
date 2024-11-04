import struct
import io

class ByteBuffer:
    def __init__(self, capacity=0):
        self.stream = io.BytesIO()
        self.capacity = capacity
        self.mode = 'write'

    @staticmethod
    def allocate(capacity):
        return ByteBuffer(capacity)

    @staticmethod
    def allocate_direct(capacity):
        return ByteBuffer.allocate(capacity)

    def flip(self):
        self.mode = 'read'
        self.stream.seek(0)  # Reset position for reading
        return self

    def clear(self):
        self.mode = 'write'
        self.stream.seek(0)
        self.stream.truncate(0)
        return self

    def compact(self):
        self.mode = 'write'
        remaining = self.stream.read()  # Read what's left
        self.stream = io.BytesIO(remaining)  # Keep only remaining bytes
        return self

    def put_short(self, value):
        self.stream.write(struct.pack('>h', value))  # Write short as big-endian

    def put_int(self, value):
        self.stream.write(struct.pack('>i', value))  # Write int as big-endian

    def put_bytes(self, value):
        self.stream.write(value)  # Write raw bytes

    def get_short(self):
        return struct.unpack('>h', self.stream.read(2))[0]  # Read short as big-endian

    def get_int(self):
        return struct.unpack('>i', self.stream.read(4))[0]  # Read int as big-endian

    def get_bytes(self, length):
        return self.stream.read(length)  # Read raw bytes

    def put_int_at(self, index, value):
        # Save current position
        current_position = self.stream.tell()
        # Seek to the index
        self.stream.seek(index)
        # Write int at the specific index
        self.stream.write(struct.pack('>I', value))
        # Return to the original position
        self.stream.seek(current_position)

    def put_short_at(self, index, value):
        # Save current position
        current_position = self.stream.tell()
        # Seek to the index
        self.stream.seek(index)
        # Write short at the specific index
        self.stream.write(struct.pack('>h', value))
        # Return to the original position
        self.stream.seek(current_position)

    def get_stream(self):
        return self.stream

    def get_capacity(self):
        return self.capacity

# Example usage:
# buffer = ByteBuffer.allocate(1024)
# buffer.put_int(10)
# buffer.put_int_at(0, 42)  # Overwrite the first 4 bytes with a new int
# buffer.flip()
# print(buffer.get_int())  # Output should be 42
