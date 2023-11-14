import os
import logging

def create_logger(logger_name, log_path=None, append=False, simple_fmt=False):
    """Create a logger for any actions.
    Parameters
    ----------
    logger_name : str
        Name of the logger
    log_path : str
        If `None` print log to the console, else print log to a file specified by `log_path`.
    append : bool
        If `True`, append log to existing `log_path`.
    simple_fmt : bool
        If `True`, use simple format of logging (e.g. without date & time).

    Return
    ------
    logger : a `logger` object.
    """
    if not append and os.path.isfile(log_path):
        with open(log_path, 'w') as f: pass
    # If append is False and the file exists, clear the content of the file.

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if log_path is None:
        handler = logging.StreamHandler() # show log in console
    else:
        handler = logging.FileHandler(log_path) # print log in file
    
    handler.setLevel(logging.DEBUG)
    if simple_fmt:
        handler.setFormatter(
            logging.Formatter(
                fmt = "%(message)s"
            )
        )
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt = '%(asctime)s %(levelname)s:  %(message)s',
                datefmt ='%m-%d %H:%M'
            )
        )
    logger.addHandler(handler)

    return logger