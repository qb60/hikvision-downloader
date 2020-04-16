import unittest
from datetime import datetime


class TestUtils:
    tz_format = '%Y-%m-%dT%H:%M:%SZ'
    common_format = '%Y-%m-%d %H:%M:%S'

    @classmethod
    def time_from_text(cls, text):
        return datetime.strptime(text, cls.common_format)

    @classmethod
    def time_to_text(cls, time):
        return time.strftime(cls.common_format)

    @classmethod
    def time_to_tz_text(cls, time):
        return time.strftime(cls.tz_format)


class TestTestUtils(unittest.TestCase):
    def test_time_converting_methods(self):
        expected_time_text = '2020-02-12 17:05:21'
        expected_time = datetime.strptime(expected_time_text, TestUtils.common_format)

        actual_time = TestUtils.time_from_text(expected_time_text)
        self.assertEqual(expected_time, actual_time)

        actual_time_text = TestUtils.time_to_text(expected_time)
        self.assertEqual(expected_time_text, actual_time_text)

        expected_time_tz_text = expected_time.strftime(TestUtils.tz_format)
        actual_time_tz_text = TestUtils.time_to_tz_text(expected_time)
        self.assertEqual(expected_time_tz_text, actual_time_tz_text)


if __name__ == '__main__':
    unittest.main()
