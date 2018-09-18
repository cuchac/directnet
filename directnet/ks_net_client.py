import binascii
import socket

from directnet.ks_client import KSClient, bit_addresses
from directnet.common import ControlCodes


class KSNetClient(KSClient):
    """
    Client for accessing ethernet port using K-Sequence protocol
    """

    def __init__(self, ip, port):
        self.port = port
        self.ip = ip
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.socket.bind(('0.0.0.0', 0))
        self.client_id = 1
        self.counter = 0

    def send(self, data):
        self.socket.sendto(data, (self.ip, self.port))

    def send_kseq(self, kseq_data):
        net_data = bytearray()
        net_data += self.to_hex_le(0x1A, 2)
        net_data += self.to_hex_le(len(kseq_data), 2)
        net_data += kseq_data

        self.counter = (self.counter + 1) % 256

        data = bytearray()
        data += b"HAP"
        data += self.to_hex_le(self.counter, 2)
        data += self.to_hex_le(0, 2)
        data += self.to_hex_le(len(net_data), 2)
        data += net_data

        self.socket.sendto(data, (self.ip, self.port))

    def test_connection(self):
        pass

    def disconnect(self):
        self.socket.close()

    def get_request_header(self, read, address, size):
        # Header 01:40:01:0f:ed:03:17:a0
        header = ControlCodes.SOH

        # Operation Read/Write 0/8
        header += self.to_hex(0x40 if read else 0x50, 1)

        # Client ID
        header += self.to_hex(self.client_id, 1)

        # Address
        address = address[1:]
        header += self.to_hex(int(address, base=8), 2)

        header += self.to_hex(size, 1)

        header += ControlCodes.ETB

        # Checksum
        header += self.calc_csum(header[1:-1])

        return header

    def read_data(self):
        data, addr = self.socket.recvfrom(1024)  # buffer size is 1024 bytes
        counter = int.from_bytes(data[3:5], byteorder='little', signed=False)
        if counter != self.counter:
            raise Exception()

        return data[9 + 4 + 6:]

    def read_ack(self):
        self.read_data()

    def read_value(self, address, size):
        header = self.get_request_header(read=True, address=address, size=size)
        self.send_kseq(header)

        self.read_ack()

        data = self.read_data()

        return data[:size]

    def write_bit(self, address, value):
        header = ControlCodes.SOH
        header += b'\x44' if value else b'\x45'
        header += b'\x01'

        # Data type
        memory_type = address[0]

        # Address
        address = address[1:]
        header += self.to_hex(bit_addresses[memory_type]+int(address, base=8), 2)
        header += ControlCodes.ETB

        # Checksum
        header += self.calc_csum(header[1:-1])

        self.send_kseq(header)

        self.read_ack()
        self.read_data()

    def read_bit(self, address):
        header = ControlCodes.SOH
        header += b'\x40'
        header += b'\x01'

        # Data type
        memory_type = address[0]

        # Address
        address = address[1:]
        address = bit_addresses[memory_type]+int(address, base=8)
        header += self.to_hex(address, 2)

        header += b'\x01'

        header += ControlCodes.ETB

        # Checksum
        header += self.calc_csum(header[1:-1])

        self.send_kseq(header)

        self.read_ack()

        data = self.read_data()

        return self.to_int(data[0]) % 2 != 0

    def parse_data(self, size, additional=0):
        data = self.serial.read(4+size*2+4)  # STX + DATA + ETX + CSUM
        return data[6:-4 + additional]

    def to_hex(self, number, size):
        hex_string = '%x' % number
        return binascii.unhexlify(hex_string.zfill(size * 2)[0:size*2])

    def to_hex_le(self, number, size):
        return bytes(reversed(self.to_hex(number, size)))
