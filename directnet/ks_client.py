import binascii
from directnet.common import ControlCodes
from directnet.dn_client import DNClient


bit_addresses = {
    'C': 0xF000,
    'T': 0xfC00,
}


class KSClient(DNClient):
    """
    Client for accessing serial port using K-Sequence protocol
    """

    ENQUIRY_ID = b'K'

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

    def read_value(self, address, size):
        self.enquiry()

        header = self.get_request_header(read=True, address=address, size=size)
        self.serial.write(header)

        self.read_ack()

        data = self.parse_data(size)

        self.write_ack()
        self.end_transaction()

        return data

    def write_bit(self, address, value):
        self.enquiry()

        header = ControlCodes.SOH

        header += '\x44' if value else '\x45'

        header += '\x01'

        # Data type
        memory_type = address[0]

        # Address
        address = address[1:]
        header += self.to_hex(bit_addresses[memory_type]+int(address, base=8), 2)

        header += ControlCodes.ETB

        # Checksum
        header += self.calc_csum(header[1:-1])

        self.serial.write(header)
        self.parse_data(0)
        self.write_ack()
        self.end_transaction()

    def read_bit(self, address):
        self.enquiry()

        header = ControlCodes.SOH

        header += '\x40'

        header += '\x01'

        # Data type
        memory_type = address[0]

        # Address
        address = address[1:]
        address = bit_addresses[memory_type]+int(address, base=8)
        header += self.to_hex(address, 2)

        header += '\x01'

        header += ControlCodes.ETB

        # Checksum
        header += self.calc_csum(header[1:-1])

        self.serial.write(header)
        self.read_ack()

        data = self.parse_data(1, 1)

        self.write_ack()
        self.end_transaction()

        return ord(data[0]) % 2 != 0

    def parse_data(self, size, additional=0):
        data = self.serial.read(4+size*2+4)  # STX + DATA + ETX + CSUM
        return data[6:-4 + additional]

    def to_hex(self, number, size):
        hex_string = '%x' % number
        return binascii.unhexlify(hex_string.zfill(size*2 + (size*2 & 1)))
