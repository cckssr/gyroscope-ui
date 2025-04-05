import unittest
from unittest.mock import patch, Mock, call
import sys
import io
from serial import SerialException
from src.arduino import Arduino, GMCounter

class TestArduino(unittest.TestCase):
    """Test cases for the Arduino class."""

    @patch('src.arduino.Serial')
    def test_init_successful(self, mock_serial):
        """Test successful initialization of Arduino connection."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True

        # Execute
        arduino = Arduino(port='/dev/ttyUSB0', rate=9600)

        # Assert
        mock_serial.assert_called_once_with(port='/dev/ttyUSB0', baudrate=9600)
        self.assertEqual(arduino.port, '/dev/ttyUSB0')
        self.assertEqual(arduino.rate, 9600)
        self.assertEqual(arduino.arduino, mock_serial_instance)

    @patch('src.arduino.Serial')
    def test_init_failed(self, mock_serial):
        """Test failed initialization of Arduino connection."""
        # Setup the mock to raise an exception
        mock_serial.side_effect = SerialException("Could not open port")
        
        # Redirect stdout to capture print statements
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # Execute
        arduino = Arduino(port='/dev/ttyUSB0')
        
        # Reset redirect
        sys.stdout = sys.__stdout__

        # Assert
        self.assertIn("Error: Could not open port", captured_output.getvalue())
        self.assertIsNone(arduino.arduino)

    @patch('src.arduino.Serial')
    def test_reconnect_successful(self, mock_serial):
        """Test successful reconnection to Arduino."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        
        # Execute
        arduino = Arduino(port='/dev/ttyUSB0')
        arduino.reconnect()
        
        # Assert
        self.assertEqual(mock_serial.call_count, 2)  # Once in __init__ and once in reconnect
        self.assertEqual(arduino.arduino, mock_serial_instance)

    @patch('src.arduino.Serial')
    def test_reconnect_with_open_connection(self, mock_serial):
        """Test reconnection when a connection is already open."""
        # Setup the mocks
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        
        # Execute
        arduino = Arduino(port='/dev/ttyUSB0')
        arduino.reconnect()
        
        # Assert
        mock_serial_instance.close.assert_called_once()
        self.assertEqual(mock_serial.call_count, 2)  # Once in __init__ and once in reconnect

    @patch('src.arduino.Serial')
    def test_status_connected(self, mock_serial):
        """Test status method when connected."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        
        # Execute
        arduino = Arduino(port='/dev/ttyUSB0')
        status = arduino.status()
        
        # Assert
        self.assertTrue(status)
        mock_serial_instance.isOpen.assert_called_once()

    @patch('src.arduino.Serial')
    def test_status_not_connected(self, mock_serial):
        """Test status method when not connected."""
        # Setup the mock
        mock_serial.side_effect = SerialException("Could not open port")
        
        # Execute
        arduino = Arduino(port='/dev/ttyUSB0')
        status = arduino.status()
        
        # Assert
        self.assertFalse(status)

    @patch('src.arduino.Serial')
    def test_close(self, mock_serial):
        """Test close method."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        
        # Execute
        arduino = Arduino(port='/dev/ttyUSB0')
        arduino.close()
        
        # Assert
        mock_serial_instance.close.assert_called_once()

    @patch('src.arduino.Serial')
    def test_read(self, mock_serial):
        """Test read method."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.readline.return_value = b'Hello, World!'
        
        # Execute
        arduino = Arduino(port='/dev/ttyUSB0')
        data = arduino.read()
        
        # Assert
        self.assertEqual(data, b'Hello, World!')
        mock_serial_instance.readline.assert_called_once()

    @patch('src.arduino.Serial')
    def test_write(self, mock_serial):
        """Test write method."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        
        # Execute
        arduino = Arduino(port='/dev/ttyUSB0')
        arduino.write('Hello, Arduino!')
        
        # Assert
        mock_serial_instance.write.assert_called_once_with(b'Hello, Arduino!')

class TestGMCounter(unittest.TestCase):
    """Test cases for the GMCounter class."""

    @patch('src.arduino.Serial')
    def test_init(self, mock_serial):
        """Test initialization of GMCounter."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0', rate=9600)
        
        # Assert
        self.assertEqual(gm_counter.port, '/dev/ttyUSB0')
        self.assertEqual(gm_counter.rate, 9600)
        self.assertEqual(gm_counter.arduino, mock_serial_instance)
        self.assertEqual(mock_serial.call_count, 2)  # Once in __init__ and once in reconnect

    @patch('src.arduino.Serial')
    def test_get_data_successful(self, mock_serial):
        """Test successful data retrieval from GMCounter."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        mock_serial_instance.readline.return_value = b'42,10,60,1,50,400'
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        data = gm_counter.get_data()
        
        # Assert
        expected_data = {
            "count": 42,
            "last_count": 10,
            "counting_time": 60,
            "repeat": True,
            "progress": 50,
            "voltage": 400
        }
        self.assertEqual(data, expected_data)
        mock_serial_instance.readline.assert_called_once()

    @patch('src.arduino.Serial')
    def test_get_data_parse_error(self, mock_serial):
        """Test data retrieval with parsing error."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        mock_serial_instance.readline.return_value = b'invalid,data'
        
        # Redirect stdout to capture print statements
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        data = gm_counter.get_data()
        
        # Reset redirect
        sys.stdout = sys.__stdout__
        
        # Assert
        self.assertIn("Error parsing line", captured_output.getvalue())
        self.assertEqual(data["count"], 0)  # Default values should remain

    @patch('src.arduino.Serial')
    def test_set_stream(self, mock_serial):
        """Test setting stream value."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        result = gm_counter.set_stream(3)
        
        # Assert
        self.assertTrue(result)
        mock_serial_instance.write.assert_called_once_with(b'b3')

    @patch('src.arduino.Serial')
    def test_get_information(self, mock_serial):
        """Test getting information from GMCounter."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        mock_serial_instance.readline.side_effect = [b'Copyright 2023', b'v1.0.0']
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        info = gm_counter.get_information()
        
        # Assert
        expected_info = {
            "copyright": "Copyright 2023",
            "version": "v1.0.0"
        }
        self.assertEqual(info, expected_info)
        mock_serial_instance.write.assert_has_calls([call(b'c'), call(b'v')])

    @patch('src.arduino.Serial')
    def test_set_voltage_valid(self, mock_serial):
        """Test setting valid voltage."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        result = gm_counter.set_voltage(500)
        
        # Assert
        self.assertTrue(result)
        mock_serial_instance.write.assert_called_once_with(b'j500')

    @patch('src.arduino.Serial')
    def test_set_voltage_invalid(self, mock_serial):
        """Test setting invalid voltage."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        
        # Redirect stdout to capture print statements
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        result = gm_counter.set_voltage(800)
        
        # Reset redirect
        sys.stdout = sys.__stdout__
        
        # Assert
        self.assertIsNone(result)
        self.assertIn("Error: Voltage must be between 300 and 700", captured_output.getvalue())
        mock_serial_instance.write.assert_not_called()

    @patch('src.arduino.Serial')
    def test_set_repeat(self, mock_serial):
        """Test setting repeat mode."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        result_true = gm_counter.set_repeat(True)
        result_false = gm_counter.set_repeat(False)
        
        # Assert
        self.assertTrue(result_true)
        self.assertTrue(result_false)
        mock_serial_instance.write.assert_has_calls([call(b'o1'), call(b'o0')])

    @patch('src.arduino.Serial')
    def test_set_counting(self, mock_serial):
        """Test setting counting mode."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        result_true = gm_counter.set_counting(True)
        result_false = gm_counter.set_counting(False)
        
        # Assert
        self.assertTrue(result_true)
        self.assertTrue(result_false)
        mock_serial_instance.write.assert_has_calls([call(b's1'), call(b's0')])

    @patch('src.arduino.Serial')
    def test_set_speaker(self, mock_serial):
        """Test setting speaker options."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        result1 = gm_counter.set_speaker(False, False)  # U0
        result2 = gm_counter.set_speaker(True, False)   # U1
        result3 = gm_counter.set_speaker(False, True)   # U2
        result4 = gm_counter.set_speaker(True, True)    # U3
        
        # Assert
        self.assertTrue(all([result1, result2, result3, result4]))
        mock_serial_instance.write.assert_has_calls([
            call(b'U0'), call(b'U1'), call(b'U2'), call(b'U3')
        ])

    @patch('src.arduino.Serial')
    def test_set_counting_time_valid(self, mock_serial):
        """Test setting valid counting time."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        result = gm_counter.set_counting_time(3)
        
        # Assert
        self.assertTrue(result)
        mock_serial_instance.write.assert_called_once_with(b'f3')

    @patch('src.arduino.Serial')
    def test_set_counting_time_invalid(self, mock_serial):
        """Test setting invalid counting time."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        mock_serial_instance.isOpen.return_value = True
        
        # Redirect stdout to capture print statements
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        # Execute
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        result = gm_counter.set_counting_time(10)
        
        # Reset redirect
        sys.stdout = sys.__stdout__
        
        # Assert
        self.assertIsNone(result)
        self.assertIn("Error: Counting time must be between 0 and 5", captured_output.getvalue())
        mock_serial_instance.write.assert_not_called()

    @patch('src.arduino.Serial')
    def test_check_connection_decorator(self, mock_serial):
        """Test the check_connection decorator."""
        # Setup the mock
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance
        
        # Test with connection
        mock_serial_instance.isOpen.return_value = True
        gm_counter = GMCounter(port='/dev/ttyUSB0')
        result_with_connection = gm_counter.set_stream(1)
        self.assertTrue(result_with_connection)

        # Test without connection
        mock_serial_instance.isOpen.return_value = False
        result_without_connection = gm_counter.set_stream(1)
        self.assertIsNone(result_without_connection)

if __name__ == '__main__':
    unittest.main()
