from datetime import datetime
from src.time_interval import TimeInterval


class Track:
    def __init__(self, text, local_time_offset):
        self._text = text
        self._base_url = ''
        self._name = ''
        self._size = 0

        text = text.replace('?', '&')
        text_parts = text.split('&')

        start_time_text = ''
        end_time_text = ''

        for text_part in text_parts:
            if text_part.count('rtsp://') > 0:
                self._base_url = text_part
            elif text_part.count('=') > 0:
                param_parts = text_part.split('=')
                param_name = param_parts[0]
                param_value = param_parts[1]

                if param_name == 'starttime':
                    start_time_text = self.decode_time(param_value)
                elif param_name == 'endtime':
                    end_time_text = self.decode_time(param_value)
                elif param_name == 'name':
                    self._name = param_value
                elif param_name == 'size':
                    self._size = param_value

        self._time_interval = TimeInterval.from_string(start_time_text, end_time_text, local_time_offset)

    @staticmethod
    def decode_time(time_text):
        date_time = datetime.strptime(time_text, '%Y%m%dT%H%M%SZ')
        date_time_text = date_time.strftime('%Y-%m-%d %H:%M:%S')

        return date_time_text

    @staticmethod
    def encode_time(time_text):
        date_time = datetime.strptime(time_text, '%Y-%m-%d %H:%M:%S')
        date_time_text = date_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        return date_time_text

    def text(self):
        return self._text

    def get_time_interval(self):
        return self._time_interval

    def name(self):
        return self._name

    def size(self):
        return self._size

    def base_url(self):
        return self._base_url

    def url_to_download(self):
        return self.base_url() + '?name=' + self.name()
