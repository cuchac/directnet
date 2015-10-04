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
        self.serial.write(b'K' + chr(0x20 + self.client_id) + ControlCodes.ENQ)
        ack = self.serial.read(size=3)
        assert ack == b'K' + chr(0x20 + self.client_id) + ControlCodes.ACK, "ACK not received. Instead got: "+repr(ack)

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

    def read_int(self, address):
        data = self.read_value(address, 2)
        return int(data[::-1].encode('hex'))

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
        print('read bit data', data)

        self.write_ack()
        self.end_transaction()

        return ord(data[0]) % 2 != 0

    def read_ack(self):
        ack = self.serial.read(1)
        assert ack == ControlCodes.ACK, repr(ack) + ' != ACK'

    def write_ack(self):
        self.serial.write(ControlCodes.ACK)

    def end_transaction(self):
        eot = self.serial.read(1)
        assert eot == ControlCodes.EOT, 'Not received EOT: '+repr(eot)
        self.serial.write(ControlCodes.EOT)

    def parse_data(self, size, additional=0):
        data = self.serial.read(4+size*2+4)  # STX + DATA + ETX + CSUM
        print('recieved data', data)
        return data[6:-4 + additional]

    def calc_csum(self, data):
        csum = 0

        for item in data:
            csum ^= ord(item)

        return bytes(chr(csum))

    def to_hex(self, number, size):
        hex_string = '%x' % number
        return binascii.unhexlify(hex_string.zfill(size*2 + (size*2 & 1)))
