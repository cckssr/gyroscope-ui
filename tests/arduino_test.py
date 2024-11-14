import unittest
from unittest.mock import patch
from src.arduino import Arduino

class TestArduino(unittest.TestCase):

    @patch('src.arduino.Serial')
    def setUp(self, MockSerial):
        self.mock_serial_instance = MockSerial.return_value
        self.arduino = Arduino(port='/dev/ttyUSB0')

    def test_reconnect(self):
        self.arduino.reconnect()
        self.mock_serial_instance.close.assert_called()
        self.mock_serial_instance.open.assert_called()

    def test_status(self):
        self.mock_serial_instance.isOpen.return_value = True
        self.assertTrue(self.arduino.status())
        self.mock_serial_instance.isOpen.return_value = False
        self.assertFalse(self.arduino.status())

    def test_close(self):
        self.arduino.close()
        self.mock_serial_instance.close.assert_called()

    def test_read(self):
        self.mock_serial_instance.readline.return_value = b'Hello, Arduino!\n'
        self.assertEqual(self.arduino.read(), b'Hello, Arduino!\n')

    def test_write(self):
        self.arduino.write('Hello, Arduino!')
        self.mock_serial_instance.write.assert_called_with(b'Hello, Arduino!')

if __name__ == '__main__':
    unittest.main()
