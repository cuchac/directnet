import serial
import binascii


class ControlCodes:
    ENQ = b'\x05'  # Enquiry - initiate request
    ACK = b'\x06'  # Acknowledge - the communication was received without error
    NAK = b'\x15'  # Negative Acknowledge - there was a problem with the communication
    SOH = b'\x01'  # Start of Header - beginning of header
    ETB = b'\x17'  # End of Transmission Block - end of intermediate block
    STX = b'\x02'  # Start of Text - beginning of data block
    ETX = b'\x03'  # End of Text - End of last data block
    EOT = b'\x04'  # End of Transmission - the request is complete.


memory_map = {
    'V': 1,
}

bit_addresses = {
    'C': 0xF000,
    'T': 0xfC00,
}


class Client(object):
    """
    Client for accessing serial port using DirectNET protocol

    @type serial: serial.Serial
    """

    def __init__(self, port):
        self.serial = serial.serial_for_url(port, timeout=1, parity=serial.PARITY_ODD)
        self.client_id = 1

    def test_connection(self):
        self.enquiry()

    def enquiry(self):
        self.serial.write(b'N' + chr(0x20 + self.client_id) + ControlCodes.ENQ)
        ack = self.serial.read(size=3)
        assert ack == b'N' + chr(0x20 + self.client_id) + ControlCodes.ACK, "ACK not received. Instead got: "+ack

    def get_request_header(self, read, address, size):
        # Header
        header = ControlCodes.SOH

        # Client ID
        header += self.to_hex(self.client_id, 2)

        # Operation Read/Write 0/8
        header += self.to_hex(0 if read else 8, 1)

        # Data type
        memory_type = address[0]
        header += self.to_hex(memory_map[memory_type], 1)

        # Address
        address = address[1:]
        header += self.to_hex(int(address, base=8)+1, 4)

        # No of blocks, bytes in last block
        header += self.to_hex(size / 256, 2)
        header += self.to_hex(size % 256, 2)

        # master id = 0
        header += self.to_hex(0, 2)

        header += ControlCodes.ETB

        # Checksum
        header += self.calc_csum(header[1:15])

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
        header = ControlCodes.SOH

        header += '44' if value else '45'

        header += '01'

        # Data type
        memory_type = address[0]

        # Address
        address = address[1:]
        header += self.to_hex(bit_addresses[memory_type]+int(address, base=8), 4)

        header += ControlCodes.ETB

        # Checksum
        header += self.calc_csum(header[1:-2])
        print header
        #self.read_ack()

    def read_bit(self, address):
        header = ControlCodes.SOH

        header += '\x40'

        header += '\x01'

        # Data type
        memory_type = address[0]

        # Address
        address = address[1:]
        address = bit_addresses[memory_type]+int(address, base=8)
        header += self.to_hex_binary(address, 2)

        header += '\x01'

        header += ControlCodes.ETB

        # Checksum
        header += self.calc_csum(header[1:-2])
        print(header, len(header))
        self.serial.write(header)
        print(repr(self.serial.readall()))
        #self.read_ack()

    def read_ack(self):
        ack = self.serial.read(1)
        assert ack == ControlCodes.ACK, ack + ' != ACK'

    def write_ack(self):
        self.serial.write(ControlCodes.ACK)

    def end_transaction(self):
        assert self.serial.read(1) == ControlCodes.EOT
        self.serial.write(ControlCodes.EOT)

    def parse_data(self, size):
        data = self.serial.read(1 + size + 2)  # STX + DATA + ETX + CSUM

        return data[1:size+1]

    def calc_csum(self, data):
        csum = 0

        for item in data:
            csum ^= ord(item)

        return bytes(chr(csum))

    def to_hex(self, number, size):
        hex_chars = hex(number)[2:].upper()
        return ('0' * (size - len(hex_chars))) + hex_chars

    def to_hex_binary(self, number, size):
        hex_string = '%x' % number
        return binascii.unhexlify(hex_string.zfill(size + (size & 1)))
