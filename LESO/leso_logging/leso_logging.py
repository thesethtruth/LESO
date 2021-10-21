"""
Taken mostly from ema workbench by Jan Kwakkel. https://github.com/quaquel/EMAworkbench
"""

# from ema_workbench.util.ema_logging
import logging
from logging import DEBUG, INFO
from logging.handlers import QueueHandler
import inspect
from functools import wraps
import multiprocessing


DEFAULT_LEVEL = DEBUG
LOG_FORMAT = "[%(processName)s/%(levelname)s] %(message)s"
LOGGER_NAME = "LESO"

_rootlogger = None
_module_loggers = {}
_multi_module_loggers = {}


def create_module_logger(name=None):
    if name is None:
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
        name = mod.__name__
    logger = logging.getLogger("{}.{}".format(LOGGER_NAME, name))

    _module_loggers[name] = logger
    return logger


def get_module_logger(name):
    try:
        logger = _module_loggers[name]
    except KeyError:
        logger = create_module_logger(name)

    return logger


_logger = get_module_logger(__name__)

def method_logger(name):
    logger = get_module_logger(name)
    classname = inspect.getouterframes(inspect.currentframe())[1][3]

    def real_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # hack, because log is applied to methods, we can get
            # object instance as first arguments in args
            logger.debug('calling {} on {}'.format(func.__name__, classname))
            res = func(*args, **kwargs)
            logger.debug(
                'completed calling {} on {}'.format(
                    func.__name__, classname))
            return res
        return wrapper
    return real_decorator


def get_rootlogger():
    '''
    Returns root logger used by the EMA workbench

    Returns
    -------
    the logger of the EMA workbench

    '''
    global _rootlogger

    if not _rootlogger:
        _rootlogger = logging.getLogger(LOGGER_NAME)
        _rootlogger.handlers = []
        _rootlogger.addHandler(logging.NullHandler())
        _rootlogger.setLevel(DEBUG)

    return _rootlogger

class ExtraFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'dct') and len(record.dct) > 0:
            for k, v in record.dct.items():
                record.msg = record.msg + '\n\t' + k + ': ' + str(v)
        return super(ExtraFilter, self).filter(record)

class ExtraHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super(ExtraHandler, self).__init__(*args, **kwargs)
        self.addFilter(ExtraFilter())

def log_to_stderr(level=None):
    """
    Turn on logging and add a handler which prints to stderr

    Parameters
    ----------
    level : int
            minimum level of the messages that will be logged

    """

    if not level:
        level = DEFAULT_LEVEL

    logger = get_rootlogger()

    # avoid creation of multiple stream handlers for logging to console
    for entry in logger.handlers:
        if (isinstance(entry, logging.StreamHandler)) and (
            entry.formatter._fmt == LOG_FORMAT
        ):
            return logger

    formatter = logging.Formatter(LOG_FORMAT)
    if level == DEBUG:
        handler = ExtraHandler()
    else:
        handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False   

    return logger