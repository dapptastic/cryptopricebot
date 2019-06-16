import logging
import logging.config
import logging.handlers
from logging.handlers import TimedRotatingFileHandler


def build_logger(name, path, loglvl='info', include_level=True):
    lg = logging.getLogger(name)

    if loglvl == 'error':
        log_level = logging.ERROR
    elif loglvl == 'debug':
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    lg.setLevel(log_level)

    if include_level:
        formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(message)s')
    else:
        formatter = logging.Formatter('%(asctime)s|%(message)s')

    fh = TimedRotatingFileHandler(path, 'midnight', 1, 365)
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    lg.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    lg.addHandler(ch)

    return lg
