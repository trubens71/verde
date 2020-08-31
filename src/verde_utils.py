import logging
import sys


def hello():
    return 'hello from new src.verde_utils'


def configure_logger(log_file, level=logging.INFO):
    """
    Creates a logging instance which writes to file and stdout
    :param log_file: path to logfile
    :param level: logging.DEBUG, logging.INFO (default)
    :return: logging instance
    """
    # Clear out old loggers (for Jupyter use when the handlers stay in scope between runs)
    for h in logging.getLogger('').handlers:
        logging.getLogger('').removeHandler(h)
    # configure logging to write to file and stdout with a nice format and
    # for info and above messages
    fh = logging.StreamHandler(sys.stdout)
    ch = logging.FileHandler(log_file, mode='w')
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s', "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logging.getLogger('').addHandler(fh)
    logging.getLogger('').addHandler(ch)
    logging.getLogger('').setLevel(level)
    return logging