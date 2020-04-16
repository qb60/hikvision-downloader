import unittest

from tests.test_utils import TestUtils
from src.time_interval import TimeInterval
from datetime import timedelta


class TestTimeInterval(unittest.TestCase):
    def test_interval_to_tz_text(self):
        start_time_text = '2020-02-12 17:05:21'
        end_time_text = '2020-02-13 17:05:21'

        start_time = TestUtils.time_from_text(start_time_text)
        end_time = TestUtils.time_from_text(end_time_text)

        expected_start_time_tz_text = TestUtils.time_to_tz_text(start_time)
        expected_end_time_tz_text = TestUtils.time_to_tz_text(end_time)

        interval = TimeInterval.from_string(start_time_text, end_time_text)

        (actual_start_time_tz_text, actual_end_time_tz_text) = interval.to_tz_text()

        self.assertEqual(expected_start_time_tz_text, actual_start_time_tz_text)
        self.assertEqual(expected_end_time_tz_text, actual_end_time_tz_text)

    def test_interval_equality(self):
        start_time1 = '2020-02-12 17:05:21'
        end_time1 = '2020-02-13 17:05:21'

        start_time2 = '2021-02-12 17:05:21'
        end_time2 = '2021-02-13 17:05:21'

        interval2 = TimeInterval.from_string(start_time1, end_time1)
        interval1 = TimeInterval.from_string(start_time1, end_time1)
        interval3 = TimeInterval.from_string(start_time2, end_time2)

        self.assertEqual(interval1, interval2)
        self.assertNotEqual(interval1, interval3)

    def test_interval_to_common_text(self):
        expected_start_time_text = '2020-02-12 17:05:21'
        expected_end_time_text = '2020-02-13 17:05:21'

        interval = TimeInterval.from_string(expected_start_time_text, expected_end_time_text)
        (actual_start_time_text, actual_end_time_text) = interval.to_text()

        self.assertEqual(expected_start_time_text, actual_start_time_text)
        self.assertEqual(expected_end_time_text, actual_end_time_text)

    def test_interval_to_filename_text(self):
        start_time_text = '2020-02-12 17:05:21'
        end_time_text = '2020-02-13 17:05:21'
        expected_filename = '2020-02-12/17_05_21'

        interval = TimeInterval.from_string(start_time_text, end_time_text)
        actual_filename = interval.to_filename_text()

        self.assertEqual(expected_filename, actual_filename)

    def test_interval_to_local_time(self):
        time_offset = timedelta(hours=5)
        time_interval = TimeInterval.from_string('2020-02-12 10:00:00', '2020-02-13 11:00:00', time_offset)
        expected_interval = TimeInterval.from_string('2020-02-12 15:00:00', '2020-02-13 16:00:00')

        actual_interval = time_interval.to_local_time()

        self.assertEqual(expected_interval, actual_interval)

    def test_interval_to_utc(self):
        time_offset = timedelta(hours=5)
        time_interval = TimeInterval.from_string('2020-02-12 04:00:00', '2020-02-12 16:00:00', time_offset)
        expected_interval = TimeInterval.from_string('2020-02-11 23:00:00', '2020-02-12 11:00:00')

        actual_interval = time_interval.to_utc()

        self.assertEqual(expected_interval, actual_interval)

    def test_interval_to_local_from_utc(self):
        time_offset = timedelta(hours=5)
        expected_interval = TimeInterval.from_string('2020-02-12 04:00:00', '2020-02-12 16:00:00', time_offset)

        actual_interval = expected_interval.to_utc().to_local_time()

        self.assertEqual(expected_interval, actual_interval)


if __name__ == '__main__':
    unittest.main()
