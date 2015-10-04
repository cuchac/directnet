import unittest
from directnet import KSClient, DNClient


class KSequenceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(KSequenceTestCase, cls).setUpClass()
        cls.client = KSClient('rfc2217://10.0.0.6:12345')

    @classmethod
    def tearDownClass(cls):
        super(KSequenceTestCase, cls).tearDownClass()
        cls.client.disconnect()

    def test_hex(self):
        self.assertEqual(self.client.to_hex(10, 1), '\x0A')
        self.assertEqual(self.client.to_hex(10, 3), '\x00\x00\x0A')
        self.assertEqual(self.client.to_hex(72, 3), '\x00\x00\x48')
        self.assertEqual(self.client.to_hex(int('40400', base=8), 2), '\x41\x00')

    def test_csum(self):
        self.assertEqual(self.client.calc_csum(b'\x30\x31\x30\x31\x30\x46\x45\x45\x30\x30\x30\x36\x30\x30'), b'\x70')

    def test_read(self):
        print repr(self.client.read_int('V1520'))
        print repr(self.client.read_int('V1767'))
        print repr(self.client.read_int('V2162'))
        print repr(self.client.read_int('V2166'))
        print repr(self.client.read_value('V1200', 4))
        print repr(self.client.read_value('V1202', 2))

    def test_bits(self):
        self.client.write_bit('C60', False)
        self.client.write_bit('C61', True)
        self.client.write_bit('C62', False)
        self.client.write_bit('C63', True)
        self.client.write_bit('C64', False)

        self.assertEqual(self.client.read_bit('C60'), False)
        self.assertEqual(self.client.read_bit('C61'), True)
        self.assertEqual(self.client.read_bit('C62'), False)
        self.assertEqual(self.client.read_bit('C63'), True)
        self.assertEqual(self.client.read_bit('C64'), False)


class DirectNetTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(DirectNetTestCase, cls).setUpClass()
        cls.client = DNClient('rfc2217://10.0.0.6:12345')

    @classmethod
    def tearDownClass(cls):
        super(DirectNetTestCase, cls).tearDownClass()
        cls.client.disconnect()

    def test_hex(self):
        self.assertEqual(self.client.to_hex(10, 1), 'A')
        self.assertEqual(self.client.to_hex(10, 3), '00A')
        self.assertEqual(self.client.to_hex(72, 3), '048')

    def test_csum(self):
        self.assertEqual(self.client.calc_csum(b'\x30\x31\x30\x31\x30\x46\x45\x45\x30\x30\x30\x36\x30\x30'), b'\x70')

    def test_read(self):
        print self.client.read_int('V1520')
        print self.client.read_int('V1767')
        print self.client.read_int('V2162')


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
