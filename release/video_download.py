#!/usr/bin/python3
# 2020-04-16

# ====== Parameters ======
user_name = 'admin'
user_password = 'qwer1234'
# ====================================================================
# write logs to log files (False/True)
write_logs = True

path_to_video_archive = 'video/'
base_path_to_log_file = 'video/'

MAX_BYTES_LOG_FILE_SIZE = 100000
MAX_LOG_FILES_COUNT = 20
CAMERA_REBOOT_TIME_SECONDS = 90
DELAY_BEFORE_CHECKING_AVAILABILITY_SECONDS = 30
DEFAULT_TIMEOUT_SECONDS = 10
DELAY_BETWEEN_DOWNLOADING_FILES_SECONDS = 1

video_file_extension = '.mp4'

# ====================================================================

import sys
import time
import requests
import argparse
from datetime import timedelta

# from src.camera_sdk import CameraSdk, AuthType
# ================= START camera_sdk ===================
import re
import socket
import time
import uuid

import requests
import shutil

from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from xml.etree import ElementTree
from datetime import timedelta

# from src.track import Track
# ================= START track ===================
from datetime import datetime
# from src.time_interval import TimeInterval
# ================= START time_interval ===================
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


# ================= END time_interval ===================


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
# ================= END track ===================


class AuthType:
    BASIC = 1,
    DIGEST = 2,
    UNAUTHORISED = 3


class CameraSdk:
    default_timeout_seconds = 10
    DEVICE_ERROR_CODE = 500
    __CAMERA_AVAILABILITY_TEST_PORT = 80
    # =============================== URLS ===============================

    __TIME_URL = '/ISAPI/System/time'
    __SEARCH_VIDEO_URL = '/ISAPI/ContentMgmt/search/'
    __DOWNLOAD_VIDEO_URL = '/ISAPI/ContentMgmt/download'
    __REBOOT_URL = '/ISAPI/System/reboot'

    # =============================== URLS ===============================

    __SEARCH_VIDEO_XML = """\
<?xml version='1.0' encoding='utf-8'?>
<CMSearchDescription>
    <searchID>18cc5217-3de6-408a-ac9f-2b80af05cadf</searchID>
    <trackIDList>
        <trackID>101</trackID>
    </trackIDList>
    <timeSpanList>
        <timeSpan>
            <startTime>start_time</startTime>
            <endTime>end_time</endTime>
        </timeSpan>
    </timeSpanList>
    <maxResults>40</maxResults>
    <searchResultPostion>0</searchResultPostion>
    <metadataList>
        <metadataDescriptor>//recordType.meta.std-cgi.com</metadataDescriptor>
    </metadataList>
</CMSearchDescription>"""

    __DOWNLOAD_REQUEST_XML = """\
<?xml version='1.0'?>
<downloadRequest>
    <playbackURI></playbackURI>
</downloadRequest>"""

    @classmethod
    def init(cls, default_timeout_seconds):
        cls.default_timeout_seconds = default_timeout_seconds

    @classmethod
    def get_error_message_from(cls, answer):
        answer_text = cls.__clear_xml_from_namespaces(answer.text)
        answer_xml = ElementTree.fromstring(answer_text)

        answer_status_element = answer_xml.find('statusString')
        answer_substatus_element = answer_xml.find('subStatusCode')

        if answer_status_element is not None and answer_substatus_element is not None:
            status = answer_status_element.text
            substatus = answer_substatus_element.text
            message = 'Error {} {}: {} - {}'.format(answer.status_code, answer.reason, status, substatus)
        else:
            message = answer_text

        return message

    @classmethod
    def reboot_camera(cls, auth_handler, cam_ip):
        answer = requests.put(cls.__get_service_url(cam_ip, cls.__REBOOT_URL), auth=auth_handler, data=[], timeout=cls.default_timeout_seconds)
        if not answer:
            raise RuntimeError(cls.get_error_message_from(answer))

    @classmethod
    def get_auth_type(cls, cam_ip, user_name, password):
        auth_handler = HTTPBasicAuth(user_name, password)
        request = cls.__make_get_request(auth_handler, cam_ip, cls.__TIME_URL)
        if request.ok:
            return AuthType.BASIC

        auth_handler = HTTPDigestAuth(user_name, password)
        request = cls.__make_get_request(auth_handler, cam_ip, cls.__TIME_URL)
        if request.ok:
            return AuthType.DIGEST

        return AuthType.UNAUTHORISED

    @classmethod
    def get_time_offset(cls, auth_handler, cam_ip):
        answer = cls.__make_get_request(auth_handler, cam_ip, cls.__TIME_URL)
        if answer:
            time_info_text = cls.__clear_xml_from_namespaces(answer.text)
            time_info_xml = ElementTree.fromstring(time_info_text)
            timezone_raw = time_info_xml.find('timeZone')
            time_offset = cls.parse_timezone(timezone_raw.text)
            return time_offset
        else:
            raise RuntimeError(cls.get_error_message_from(answer))

    @staticmethod
    def parse_timezone(raw_timezone):
        timezone_text = raw_timezone.replace('CST', '')
        time_offset_parts = timezone_text.split(':')
        hours = int(time_offset_parts[0])
        minutes = int(time_offset_parts[1])
        seconds = int(time_offset_parts[2])

        if hours < 0:
            minutes = -minutes
            seconds = -seconds

        return -timedelta(hours=hours, minutes=minutes, seconds=seconds)

    @staticmethod
    def get_auth(auth_type, name, password):
        if auth_type == AuthType.BASIC:
            return HTTPBasicAuth(name, password)
        elif auth_type == AuthType.DIGEST:
            return HTTPDigestAuth(name, password)
        else:
            return None

    @classmethod
    def download_file(cls, auth_handler, cam_ip, file_uri, file_name):
        request = ElementTree.fromstring(cls.__DOWNLOAD_REQUEST_XML)
        playback_uri = request.find('playbackURI')
        playback_uri.text = file_uri
        request_data = ElementTree.tostring(request, encoding='utf8', method='xml')

        url = cls.__get_service_url(cam_ip, cls.__DOWNLOAD_VIDEO_URL)
        answer = requests.get(url=url, auth=auth_handler, data=request_data, stream=True, timeout=cls.default_timeout_seconds)
        if answer:
            with open(file_name, 'wb') as out_file:
                shutil.copyfileobj(answer.raw, out_file)
            answer.close()

        return answer

    @classmethod
    def wait_until_camera_rebooted(cls, cam_ip, camera_reboot_time_seconds, delay_before_checking_availability_seconds):
        time.sleep(delay_before_checking_availability_seconds)

        duration = camera_reboot_time_seconds - delay_before_checking_availability_seconds
        tmax = time.time() + duration
        while time.time() < tmax:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(cls.default_timeout_seconds)
            try:
                s.connect((cam_ip, int(cls.__CAMERA_AVAILABILITY_TEST_PORT)))
                s.shutdown(socket.SHUT_RDWR)
                return True
            except OSError:
                time.sleep(1)
            finally:
                s.close()
        return False

    @classmethod
    def get_video_tracks_info(cls, auth_handler, cam_ip, utc_time_interval, max_videos):
        request = ElementTree.fromstring(cls.__SEARCH_VIDEO_XML)

        search_id = request.find('searchID')
        search_id.text = str(uuid.uuid1()).upper()

        max_results_count = request.find('maxResults')
        max_results_count.text = str(max_videos)

        time_span = request.find('timeSpanList').find('timeSpan')

        start_time_tz_text, end_time_tz_text = utc_time_interval.to_tz_text()

        start_time_element = time_span.find('startTime')
        start_time_element.text = start_time_tz_text

        end_time_element = time_span.find('endTime')
        end_time_element.text = end_time_tz_text

        request_data = ElementTree.tostring(request, encoding='utf8', method='xml')
        answer = cls.__make_get_request(auth_handler, cam_ip, cls.__SEARCH_VIDEO_URL, request_data)

        return answer

    @classmethod
    def create_tracks_from_info(cls, answer, local_time_offset):
        answer_text = cls.__clear_xml_from_namespaces(answer.text)
        answer_xml = ElementTree.fromstring(answer_text)

        match_list = answer_xml.find('matchList')
        match_items = match_list.findall('searchMatchItem')

        tracks = []
        for match_item in match_items:
            media_descriptor = match_item.find('mediaSegmentDescriptor')
            playback_uri = media_descriptor.find('playbackURI')
            new_track = Track(playback_uri.text, local_time_offset)
            tracks.append(new_track)

        return tracks

    @staticmethod
    def __get_service_url(cam_ip, relative_url):
        return 'http://' + cam_ip + relative_url

    @staticmethod
    def __clear_xml_from_namespaces(xml_text):
        return re.sub(' xmlns="[^"]+"', '', xml_text, count=0)

    @classmethod
    def __make_get_request(cls, auth_handler, cam_ip, url, request_data=None):
        return requests.get(url=cls.__get_service_url(cam_ip, url), auth=auth_handler, data=request_data, timeout=cls.default_timeout_seconds)

    @staticmethod
    def __replace_subelement_with(parent, new_subelement):
        subelement_tag = new_subelement.tag
        subelement = parent.find(subelement_tag)
        parent.remove(subelement)

        parent.append(new_subelement)
        return parent

    @staticmethod
    def __replace_subelement_body_with(parent, subelement_tag, new_body_text):
        subelement = parent.find(subelement_tag)
        subelement.clear()
        inner_element = ElementTree.fromstring(new_body_text)
        subelement.append(inner_element)
        return parent
# ================= END camera_sdk ===================
# from src.logger import Logger
# ================= START logger ===================
import logging
import logging.handlers


class Logger:
    LOGGER_NAME = 'hik_video_downloader'

    @staticmethod
    def init_logger(write_logs, path_to_log_file, max_bytes_log_size, max_log_files_count):
        logger = Logger.get_logger()
        logger.setLevel(logging.DEBUG)

        console_formatter = logging.Formatter(fmt='%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        if write_logs:
            file_formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

            # file_handler = logging.handlers.WatchedFileHandler(path_to_log_file)
            file_handler = logging.handlers.RotatingFileHandler(path_to_log_file, maxBytes=max_bytes_log_size, backupCount=max_log_files_count)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

    @staticmethod
    def get_logger():
        return logging.getLogger(Logger.LOGGER_NAME)
# ================= END logger ===================
# from src.log_wrapper import logging_wrapper
# ================= START log_wrapper ===================
def logging_wrapper(before=None, after=None):
    def log_decorator(func):
        def wrapper_func(*args, **kwargs):
            if before is not None:
                before(*args, **kwargs)

            result = func(*args, **kwargs)

            if after is not None:
                after(result)

            return result

        return wrapper_func

    return log_decorator
# ================= END log_wrapper ===================
# from src.log_printer import *
# ================= START log_printer ===================


class LogPrinter:
    @staticmethod
    def get_all_tracks(_1, _2, utc_time_interval):
        start_time_text, end_time_text = utc_time_interval.to_local_time().to_text()

        Logger.get_logger().info('Start time: {}'.format(start_time_text))
        Logger.get_logger().info('End time: {}'.format(end_time_text))
        Logger.get_logger().info('Getting tracks list...')

    @staticmethod
    def get_video_tracks_info(result):
        if not result:
            error_message = CameraSdk.get_error_message_from(result)
            Logger.get_logger().error('Error occurred during getting tracks list')
            Logger.get_logger().error(error_message)

    @staticmethod
    def download_tracks(tracks, _1, _2):
        Logger.get_logger().info('Found {} files'.format(len(tracks)))

    @staticmethod
    def download_file_before(_1, _2, _3, file_name):
        Logger.get_logger().info('Downloading {}'.format(file_name))

    @staticmethod
    def download_file_after(result):
        if not result:
            error_message = CameraSdk.get_error_message_from(result)
            Logger.get_logger().error(error_message)

    @staticmethod
    def reboot_camera(_1, _2):
        Logger.get_logger().info('Rebooting camera...')

    @staticmethod
    def wait_until_camera_rebooted(result):
        if result:
            Logger.get_logger().info('Camera is up, continue downloading')
        else:
            Logger.get_logger().info('Camera is still down')
# ================= END log_printer ===================
# from src.utils import *
# ================= START utils ===================
import os


def create_directory_for(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
# ================= END utils ===================

MAX_VIDEOS_NUMBER_IN_ONE_REQUEST = 100  # не больше 200
log_file_name_pattern = '{}.log'
LOGGER_NAME = 'hik_video_downloader'


# ====================================================================


def get_path_to_video_archive(cam_ip: str):
    return path_to_video_archive + cam_ip + '/'


def download_videos(auth_handler, cam_ip, utc_time_interval):
    tracks = get_all_tracks(auth_handler, cam_ip, utc_time_interval)
    download_tracks(tracks, auth_handler, cam_ip)


@logging_wrapper(before=LogPrinter.get_all_tracks)
def get_all_tracks(auth_handler, cam_ip, utc_time_interval):
    tracks = []
    while True:
        answer = get_video_tracks_info(auth_handler, cam_ip, utc_time_interval)
        local_time_offset = utc_time_interval.local_time_offset
        if answer:
            new_tracks = CameraSdk.create_tracks_from_info(answer, local_time_offset)
            tracks += new_tracks
            if len(new_tracks) < MAX_VIDEOS_NUMBER_IN_ONE_REQUEST:
                break

            last_track = tracks[-1]
            utc_time_interval.start_time = last_track.get_time_interval().end_time
        else:
            tracks = []
            break

    return tracks


@logging_wrapper(after=LogPrinter.get_video_tracks_info)
def get_video_tracks_info(auth_handler, cam_ip, utc_time_interval):
    return CameraSdk.get_video_tracks_info(auth_handler, cam_ip, utc_time_interval, MAX_VIDEOS_NUMBER_IN_ONE_REQUEST)


@logging_wrapper(before=LogPrinter.download_tracks)
def download_tracks(tracks, auth_handler, cam_ip):
    for track in tracks:
        # TODO retry only N times
        while True:
            if download_file_with_retry(auth_handler, cam_ip, track):
                break

        time.sleep(DELAY_BETWEEN_DOWNLOADING_FILES_SECONDS)


def download_file_with_retry(auth_handler, cam_ip, track):
    start_time_text = track.get_time_interval().to_local_time().to_filename_text()
    file_name = get_path_to_video_archive(cam_ip) + '/' + start_time_text + video_file_extension
    url_to_download = track.url_to_download()

    create_directory_for(file_name)
    answer = download_file(auth_handler, cam_ip, url_to_download, file_name)
    if answer:
        return True
    else:
        if answer.status_code == CameraSdk.DEVICE_ERROR_CODE:
            reboot_camera(auth_handler, cam_ip)
            wait_until_camera_rebooted(cam_ip)
        return False


@logging_wrapper(before=LogPrinter.download_file_before, after=LogPrinter.download_file_after)
def download_file(auth_handler, cam_ip, url_to_download, file_name):
    return CameraSdk.download_file(auth_handler, cam_ip, url_to_download, file_name)


@logging_wrapper(before=LogPrinter.reboot_camera)
def reboot_camera(auth_handler, cam_ip):
    CameraSdk.reboot_camera(auth_handler, cam_ip)


@logging_wrapper(after=LogPrinter.wait_until_camera_rebooted)
def wait_until_camera_rebooted(cam_ip):
    CameraSdk.wait_until_camera_rebooted(cam_ip, CAMERA_REBOOT_TIME_SECONDS, DELAY_BEFORE_CHECKING_AVAILABILITY_SECONDS)


def init(cam_ip):
    path_to_log_file = base_path_to_log_file + log_file_name_pattern.format(cam_ip)

    create_directory_for(path_to_log_file)
    create_directory_for(get_path_to_video_archive(cam_ip))

    Logger.init_logger(write_logs, path_to_log_file, MAX_BYTES_LOG_FILE_SIZE, MAX_LOG_FILES_COUNT)

    CameraSdk.init(DEFAULT_TIMEOUT_SECONDS)


def do_work(camera_ip, start_datetime_str, end_datetime_str, use_utc_time):
    logger = Logger.get_logger()
    try:
        logger.info('Processing cam {}:'.format(camera_ip))
        logger.info('{} time is used'.format("UTC" if use_utc_time else "Camera's local"))

        auth_type = CameraSdk.get_auth_type(camera_ip, user_name, user_password)
        if auth_type == AuthType.UNAUTHORISED:
            raise RuntimeError('Unauthorised! Check login and password')

        auth_handler = CameraSdk.get_auth(auth_type, user_name, user_password)

        if use_utc_time:
            local_time_offset = timedelta()
        else:
            local_time_offset = CameraSdk.get_time_offset(auth_handler, camera_ip)

        utc_time_interval = TimeInterval.from_string(start_datetime_str, end_datetime_str, local_time_offset).to_utc()

        download_videos(auth_handler, camera_ip, utc_time_interval)

    except requests.exceptions.ConnectionError as e:
        logger.error('Connection error: {}'.format(e))

    except Exception as e:
        logger.exception(e)


def parse_parameters():
    usage = """
  %(prog)s [-u] CAM_IP START_DATE START_TIME END_DATE END_TIME"""

    epilog = """
Examples:
  %(prog)s 10.145.17.202 2020-04-15 00:30:00 2020-04-15 10:59:59
  %(prog)s -u 10.145.17.202 2020-04-15 00:30:00 2020-04-15 10:59:59
        """

    parser = argparse.ArgumentParser(usage=usage, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("IP", help="camera's IP address")
    parser.add_argument("START_DATE", help="start date of interval")
    parser.add_argument("START_TIME", help="start time of interval")
    parser.add_argument("END_DATE", help="end date of interval")
    parser.add_argument("END_TIME", help="end time of interval")
    parser.add_argument("-u", "--utc", help="use parameters as UTC time, otherwise use as camera's local time", action="store_true")

    if len(sys.argv) == 1:
        parser.print_help()
        return None
    else:
        args = parser.parse_args()
        return args


def main():
    parameters = parse_parameters()
    if parameters:
        try:
            camera_ip = parameters.IP
            init(camera_ip)

            start_datetime_str = parameters.START_DATE + ' ' + parameters.START_TIME
            end_datetime_str = parameters.END_DATE + ' ' + parameters.END_TIME

            do_work(camera_ip, start_datetime_str, end_datetime_str, parameters.utc)

        except KeyboardInterrupt:
            print('')
            pass

        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
