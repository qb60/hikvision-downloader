#!/usr/bin/python3

# ====== Parameters ======
user_name = 'admin'
user_password = 'qwer1234'
# ====================================================================
# write logs to log files (False/True)
write_logs = True

path_to_media_archive = 'media/'
base_path_to_log_file = 'media/'

MAX_BYTES_LOG_FILE_SIZE = 100000
MAX_LOG_FILES_COUNT = 20
CAMERA_REBOOT_TIME_SECONDS = 90
DELAY_BEFORE_CHECKING_AVAILABILITY_SECONDS = 30
DEFAULT_TIMEOUT_SECONDS = 15
DELAY_BETWEEN_DOWNLOADING_FILES_SECONDS = 1

# ====================================================================

import sys
import time
import requests
import argparse
from datetime import timedelta

from src.camera_sdk import CameraSdk, AuthType
from src.logger import Logger
from src.time_interval import TimeInterval
from src.log_wrapper import logging_wrapper
from src.log_printer import *
from src.utils import *

MAX_NUMBER_OF_FILES_IN_ONE_REQUEST = 100  # не больше 200
log_file_name_pattern = '{}.log'
LOGGER_NAME = 'hik_video_downloader'


# ====================================================================

class ContentType:
    PHOTO = 'jpg'
    VIDEO = 'mp4'


def get_path_to_video_archive(cam_ip: str):
    return path_to_media_archive + cam_ip + '/'


def download_media(auth_handler, cam_ip, utc_time_interval, content_type):
    tracks = get_all_tracks(auth_handler, cam_ip, utc_time_interval, content_type)
    download_tracks(tracks, auth_handler, cam_ip, content_type)


@logging_wrapper(before=LogPrinter.get_all_tracks)
def get_all_tracks(auth_handler, cam_ip, utc_time_interval, content_type):
    tracks = []
    while True:
        answer = get_tracks_info(auth_handler, cam_ip, utc_time_interval, content_type)
        local_time_offset = utc_time_interval.local_time_offset
        if answer:
            new_tracks = CameraSdk.create_tracks_from_info(answer, local_time_offset)
            tracks += new_tracks
            if len(new_tracks) < MAX_NUMBER_OF_FILES_IN_ONE_REQUEST:
                break

            last_track = tracks[-1]
            utc_time_interval.start_time = last_track.get_time_interval().end_time
        else:
            tracks = []
            break

    return tracks


@logging_wrapper(after=LogPrinter.get_video_tracks_info)
def get_tracks_info(auth_handler, cam_ip, utc_time_interval, content_type):
    if content_type == ContentType.VIDEO:
        return CameraSdk.get_video_tracks_info(auth_handler, cam_ip, utc_time_interval, MAX_NUMBER_OF_FILES_IN_ONE_REQUEST)
    else:
        return CameraSdk.get_photo_tracks_info(auth_handler, cam_ip, utc_time_interval, MAX_NUMBER_OF_FILES_IN_ONE_REQUEST)


@logging_wrapper(before=LogPrinter.download_tracks)
def download_tracks(tracks, auth_handler, cam_ip, content_type):
    for track in tracks:
        # TODO retry only N times
        while True:
            if download_file_with_retry(auth_handler, cam_ip, track, content_type):
                break

        time.sleep(DELAY_BETWEEN_DOWNLOADING_FILES_SECONDS)


def download_file_with_retry(auth_handler, cam_ip, track, content_type):
    start_time_text = track.get_time_interval().to_local_time().to_filename_text()
    file_name = get_path_to_video_archive(cam_ip) + '/' + start_time_text + '.' + content_type
    url_to_download = track.url_to_download()

    create_directory_for(file_name)

    status = download_file(auth_handler, cam_ip, url_to_download, file_name)
    if status.result_type == CameraSdk.FileDownloadingResult.OK:
        return True
    else:
        if status.result_type == CameraSdk.FileDownloadingResult.DEVICE_ERROR:
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


def do_work(camera_ip, start_datetime_str, end_datetime_str, use_utc_time, content_type):
    logger = Logger.get_logger()
    try:
        logger.info('Processing cam {}: downloading {}'.format(camera_ip, content_type))
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

        download_media(auth_handler, camera_ip, utc_time_interval, content_type)

    except requests.exceptions.ConnectionError as e:
        logger.error('Connection error: {}'.format(e))

    except Exception as e:
        logger.exception(e)


def parse_parameters():
    usage = """
  %(prog)s [-u] [-p] CAM_IP START_DATE START_TIME END_DATE END_TIME"""

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
    parser.add_argument("-p", "--photo", help="download photos instead of videos", action="store_true")

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

            content_type = ContentType.PHOTO if parameters.photo else ContentType.VIDEO

            do_work(camera_ip, start_datetime_str, end_datetime_str, parameters.utc, content_type)

        except KeyboardInterrupt:
            print('')
            pass

        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
