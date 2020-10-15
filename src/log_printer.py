from src.logger import Logger
from src.camera_sdk import CameraSdk


class LogPrinter:
    @staticmethod
    def get_all_tracks(_1, _2, utc_time_interval, _3):
        start_time_text, end_time_text = utc_time_interval.to_local_time().to_text()

        Logger.get_logger().info('Start time: {}'.format(start_time_text))
        Logger.get_logger().info('End time: {}'.format(end_time_text))
        Logger.get_logger().info('Getting track list...')

    @staticmethod
    def get_video_tracks_info(result):
        if not result:
            error_message = CameraSdk.get_error_message_from(result)
            Logger.get_logger().error('Error occurred during getting track list')
            Logger.get_logger().error(error_message)

    @staticmethod
    def download_tracks(tracks, _1, _2, _3):
        Logger.get_logger().info('Found {} files'.format(len(tracks)))

    @staticmethod
    def download_file_before(_1, _2, _3, file_name):
        Logger.get_logger().info('Downloading {}'.format(file_name))

    @staticmethod
    def download_file_after(result):
        if result.result_type != CameraSdk.FileDownloadingResult.OK:
            if result.result_type == CameraSdk.FileDownloadingResult.TIMEOUT:
                Logger.get_logger().error("Timeout during file downloading")
            else:
                Logger.get_logger().error(result.text)

    @staticmethod
    def reboot_camera(_1, _2):
        Logger.get_logger().info('Rebooting camera...')

    @staticmethod
    def wait_until_camera_rebooted(result):
        if result:
            Logger.get_logger().info('Camera is up, continue downloading')
        else:
            Logger.get_logger().info('Camera is still down')
