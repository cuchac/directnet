import serial
from directnet.common import ControlCodes

memory_map = {
    'V': 1,
}


class DNClient(object):
    """
    Client for accessing serial port using DirectNET protocol

    @type serial: serial.Serial
    """

    ENQUIRY_ID = b'N'

    def __init__(self, port):
        self.serial = serial.serial_for_url(port, timeout=1, parity=serial.PARITY_ODD)
        self.client_id = 1

    def test_connection(self):
        self.enquiry()

    def disconnect(self):
        self.serial.close()

    def enquiry(self):
        self.serial.write(self.ENQUIRY_ID + chr(0x20 + self.client_id) + ControlCodes.ENQ)
        ack = self.serial.read(size=3)
        assert ack == self.ENQUIRY_ID + chr(0x20 + self.client_id) + ControlCodes.ACK, "ACK not received. Instead got: "+repr(ack)

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

    def read_int(self, address):
        data = self.read_value(address, 2)
        return int(data[::-1].encode('hex'))

    def read_ack(self):
        ack = self.serial.read(1)
        assert ack == ControlCodes.ACK, repr(ack) + ' != ACK'

    def read_end_of_text(self):
        etx = self.serial.read(1)
        assert etx == ControlCodes.ETX, repr(etx) + ' != ETX'

    def write_ack(self):
        self.serial.write(ControlCodes.ACK)

    def end_transaction(self):
        eot = self.serial.read(1)
        assert eot == ControlCodes.EOT, 'Not received EOT: '+repr(eot)
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
