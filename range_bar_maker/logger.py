import logging
import os
from datetime import datetime


def get_logger():
    """
    Simple logger.
    """
    # logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # create folder for logs
    if not os.path.isdir("Logs"):
        os.mkdir("Logs")

    # file logging
    file = logging.FileHandler("Logs/range_bar_%s.log" % datetime.now().strftime("%y%m%d_%H%M%S"))
    file.setLevel(logging.INFO)
    fileformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s", datefmt="%H:%M:%S")
    file.setFormatter(fileformat)
    logger.addHandler(file)

    # console logging
    stream = logging.StreamHandler()
    stream.setLevel(logging.INFO)
    streamformat = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
    stream.setFormatter(streamformat)
    logger.addHandler(stream)

    return logger
