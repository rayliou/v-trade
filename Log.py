#!/usr/bin/env python3
# coding=utf-8
import datetime,sys
import logging,json
from IPython.display import display, HTML

log = logging.getLogger("main" )
class ColorLogFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    warning = "\x1b[48;5;88m"
    reset = "\x1b[0m"

    #format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format = '%(levelname)s %(asctime)s [%(filename)s:%(lineno)d] %(funcName)s %(message)s %(process)d '

    ##fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: warning + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def logInit(level=logging.DEBUG):
    global log
    log.setLevel(level)
    fmt = logging.Formatter(
        '%(levelname)s %(asctime)s [%(filename)s:%(lineno)d] %(funcName)s %(message)s %(process)d ')

    fmt = ColorLogFormatter()
    s = logging.StreamHandler(sys.stderr)
    s.setFormatter(fmt)
    #s.setLevel(logging.DEBUG)
    log.addHandler(s)
    #log.critical('setup')
    #log.error('llllllllllllog')
    #log.fatal('Done')
    #log.warning('WARNING')
    #log.info('info')
    #log.debug('debug')
    pass

def showColors():
    '''
        Build your own Command Line with ANSI escape codes
        https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
    '''
    print('show background color')
    for i in range(0, 16):
        for j in range(0, 16):
            code = str(i * 16 + j)
            FCOLOR = u"\u001b[38;5;" + code + "m "
            BCOLOR = u"\u001b[48;5;" + code + "m "
            sys.stdout.write(BCOLOR+ code.ljust(4))
        print (u"\u001b[0m")
    pass

if __name__ == '__main__':
    showColors()
    logInit()
    sys.exit(0)




