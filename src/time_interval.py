from datetime import datetime
from datetime import timedelta


class TimeInterval:
    __tz_format = '%Y-%m-%dT%H:%M:%SZ'
    __common_format = '%Y-%m-%d %H:%M:%S'
    __filename_format = '%Y-%m-%d/%H_%M_%S'

    def __init__(self, start_time, end_time, local_time_offset=timedelta()):
        self.local_time_offset = local_time_offset
        self.start_time = start_time
        self.end_time = end_time

    @classmethod
    def from_string(cls, start_str, end_str, local_time_offset=timedelta()):
        start = cls.__text_to_time(start_str)
        end = cls.__text_to_time(end_str)
        return cls(start, end, local_time_offset)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.start_time == other.start_time and self.end_time == other.end_time
        return False

    def to_tz_text(self):
        start = self.__time_to_tz_format(self.start_time)
        end = self.__time_to_tz_format(self.end_time)
        return start, end

    def to_text(self):
        start = self.__time_to_common_format(self.start_time)
        end = self.__time_to_common_format(self.end_time)
        return start, end

    @classmethod
    def __text_to_time(cls, time_text):
        try:
            return datetime.strptime(time_text, cls.__common_format)
        except ValueError:
            raise ValueError('Datetime string "{}" has wrong format'.format(time_text))

    @classmethod
    def __time_to_tz_format(cls, time):
        return time.strftime(cls.__tz_format)

    @classmethod
    def __time_to_common_format(cls, time):
        return time.strftime(cls.__common_format)

    def to_filename_text(self):
        return self.start_time.strftime(self.__filename_format)

    def to_local_time(self):
        local_start_time = self.start_time + self.local_time_offset
        local_end_time = self.end_time + self.local_time_offset
        return TimeInterval(local_start_time, local_end_time)

    def to_utc(self):
        utc_start_time = self.start_time - self.local_time_offset
        utc_end_time = self.end_time - self.local_time_offset
        return TimeInterval(utc_start_time, utc_end_time, self.local_time_offset)


