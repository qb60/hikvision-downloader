import unittest

from src.time_interval import TimeInterval
from src.track import Track
from datetime import timedelta


class TestParseTrackInfo(unittest.TestCase):
    default_track_text = 'rtsp://10.226.39.51/Streaming/tracks/101/?starttime=20191111T042406Z&endtime=20191111T042415Z&name=ch01_00000000036000001&size=377108'
    default_local_time_offset = timedelta(hours=3)

    def test_base_url(self):
        track = Track(self.default_track_text, self.default_local_time_offset)
        expected_url = 'rtsp://10.226.39.51/Streaming/tracks/101/'

        self.assertEqual(expected_url, track.base_url())

    def test_all_text(self):
        track = Track(self.default_track_text, self.default_local_time_offset)
        self.assertEqual(self.default_track_text, track.text())

    def test_time_interval(self):
        track = Track(self.default_track_text, self.default_local_time_offset)
        expected_time_interval = TimeInterval.from_string('2019-11-11 04:24:06', '2019-11-11 04:24:15', self.default_local_time_offset)

        self.assertEqual(expected_time_interval, track.get_time_interval())

    def test_file_name(self):
        track = Track(self.default_track_text, self.default_local_time_offset)
        expected_name = 'ch01_00000000036000001'

        self.assertEqual(expected_name, track.name())

    def test_file_size(self):
        track = Track(self.default_track_text, self.default_local_time_offset)
        expected_name = '377108'

        self.assertEqual(expected_name, track.size())

    def test_url_to_download(self):
        track = Track(self.default_track_text, self.default_local_time_offset)
        expected_url = self.default_track_text

        self.assertEqual(expected_url, track.url_to_download())


if __name__ == '__main__':
    unittest.main()
