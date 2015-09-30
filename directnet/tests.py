import unittest
from directnet.client import Client


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(MyTestCase, cls).setUpClass()
        cls.client = Client('rfc2217://10.0.0.6:12345')

    def test_hex(self):
        self.assertEqual(self.client.to_hex(10, 1), 'A')
        self.assertEqual(self.client.to_hex(10, 3), '00A')
        self.assertEqual(self.client.to_hex(72, 3), '048')

    def test_csum(self):
        self.assertEqual(self.client.calc_csum(b'\x30\x31\x30\x31\x30\x46\x45\x45\x30\x30\x30\x36\x30\x30'), b'\x70')

    def test_read(self):
        print repr(self.client.read_value('V7756', 6))
        print repr(self.client.read_value('V1206', 20))
        print repr(self.client.read_value('V1242', 50))


if __name__ == '__main__':
    unittest.main()
