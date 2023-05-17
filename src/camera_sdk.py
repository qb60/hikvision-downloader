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

from src.track import Track


class AuthType:
    BASIC = 1
    DIGEST = 2
    UNAUTHORISED = 3


class CameraSdk:
    class FileDownloadingResult:
        OK = 1
        ERROR = 2
        DEVICE_ERROR = 3
        TIMEOUT = 4

        def __init__(self, result_type, text=""):
            self.result_type = result_type
            self.text = text

        @classmethod
        def ok(cls):
            return cls(cls.OK)

        @classmethod
        def error(cls, text):
            return cls(cls.ERROR, text)

        @classmethod
        def device_error(cls, text):
            return cls(cls.DEVICE_ERROR, text)

        @classmethod
        def timeout(cls):
            return cls(cls.TIMEOUT)

    default_timeout_seconds = 10
    __DEVICE_ERROR_CODE = 500

    __CAMERA_AVAILABILITY_TEST_PORT = 80
    __VIDEO_TRACK_ID = 101
    __PHOTO_TRACK_ID = 103

    # =============================== URLS ===============================

    __TIME_URL = '/ISAPI/System/time'
    __SEARCH_MEDIA_URL = '/ISAPI/ContentMgmt/search'
    __DOWNLOAD_MEDIA_URL = '/ISAPI/ContentMgmt/download'
    __REBOOT_URL = '/ISAPI/System/reboot'

    # =============================== URLS ===============================

    __SEARCH_MEDIA_XML = """\
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

        url = cls.__get_service_url(cam_ip, cls.__DOWNLOAD_MEDIA_URL)
        try:
            answer = requests.get(url=url, auth=auth_handler, data=request_data, stream=True, timeout=cls.default_timeout_seconds)
            if answer:
                with open(file_name, 'wb') as out_file:
                    shutil.copyfileobj(answer.raw, out_file)
                answer.close()
                return cls.FileDownloadingResult.ok()
            else:
                return cls.get_file_downloading_result_error(answer)

        except (requests.exceptions.Timeout, requests.packages.urllib3.exceptions.TimeoutError):
            return cls.FileDownloadingResult.timeout()

    @classmethod
    def get_file_downloading_result_error(cls, answer):
        error_text = cls.get_error_message_from(answer)
        if answer.status_code == CameraSdk.__DEVICE_ERROR_CODE:
            return cls.FileDownloadingResult.device_error(error_text)
        else:
            return cls.FileDownloadingResult.error(error_text)

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
    def get_tracks_info(cls, auth_handler, cam_ip, utc_time_interval, max_videos, track_id):
        request = ElementTree.fromstring(cls.__SEARCH_MEDIA_XML)

        search_id = request.find('searchID')
        search_id.text = str(uuid.uuid1()).upper()

        max_results_count = request.find('maxResults')
        max_results_count.text = str(max_videos)

        track_id_element = request.find('trackIDList').find('trackID')
        track_id_element.text = str(track_id)

        time_span = request.find('timeSpanList').find('timeSpan')

        start_time_tz_text, end_time_tz_text = utc_time_interval.to_tz_text()

        start_time_element = time_span.find('startTime')
        start_time_element.text = start_time_tz_text

        end_time_element = time_span.find('endTime')
        end_time_element.text = end_time_tz_text

        request_data = ElementTree.tostring(request, encoding='utf8', method='xml')
        answer = cls.__make_post_request(auth_handler, cam_ip, cls.__SEARCH_MEDIA_URL, request_data)

        return answer

    @classmethod
    def get_video_tracks_info(cls, auth_handler, cam_ip, utc_time_interval, max_videos):
        return cls.get_tracks_info(auth_handler, cam_ip, utc_time_interval, max_videos, cls.__VIDEO_TRACK_ID)

    @classmethod
    def get_photo_tracks_info(cls, auth_handler, cam_ip, utc_time_interval, max_videos):
        return cls.get_tracks_info(auth_handler, cam_ip, utc_time_interval, max_videos, cls.__PHOTO_TRACK_ID)

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
    def __make_get_request(cls, auth_handler, cam_ip, url):
        return requests.get(url=cls.__get_service_url(cam_ip, url), auth=auth_handler, timeout=cls.default_timeout_seconds)

    @classmethod
    def __make_post_request(cls, auth_handler, cam_ip, url, request_data):
        return requests.post(url=cls.__get_service_url(cam_ip, url), auth=auth_handler, data=request_data, timeout=cls.default_timeout_seconds)

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
