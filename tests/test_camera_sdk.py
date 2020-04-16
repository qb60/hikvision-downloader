import unittest
from datetime import timedelta

from src.camera_sdk import CameraSdk


class TestParseTimeInfo(unittest.TestCase):
    def test_decode_timezone_plus(self):
        raw_timezone = 'CST-5:00:00'
        expected_time_offset = timedelta(hours=5)

        actual_time_offset = CameraSdk.parse_timezone(raw_timezone)
        self.assertEqual(expected_time_offset, actual_time_offset)

    def test_decode_timezone_minus(self):
        raw_timezone = 'CST+7:00:00'
        expected_time_offset = timedelta(hours=-7)

        actual_time_offset = CameraSdk.parse_timezone(raw_timezone)
        self.assertEqual(expected_time_offset, actual_time_offset)

    def test_decode_timezone_minutes_and_seconds(self):
        raw_timezone = 'CST+7:30:10'
        expected_time_offset = timedelta(hours=-7, minutes=-30, seconds=-10)

        actual_time_offset = CameraSdk.parse_timezone(raw_timezone)
        self.assertEqual(expected_time_offset, actual_time_offset)

    def test_decode_timezone_plus_minutes_and_seconds(self):
        raw_timezone = 'CST-5:45:20'
        expected_time_offset = timedelta(hours=5, minutes=45, seconds=20)

        actual_time_offset = CameraSdk.parse_timezone(raw_timezone)
        self.assertEqual(expected_time_offset, actual_time_offset)


if __name__ == '__main__':
    unittest.main()
