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
