#!/usr/bin/env python3
# coding=utf-8
#from ib_insync import *

import click,glob

from functools import wraps
import sys,time,inspect,os,logging
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from Log import logInit



class SpeedControl:
    log = logging.getLogger("main.SpeedControl")
    callsCurSec = []
    @classmethod
    def controlMaxCallsPerPeriod(cls, function, callsList, maxCalls =3, seconds=1):
        def refreshAndWait():
            total = len(callsList)
            while total >= maxCalls:
                tm = time.time()
                while total > 0 and  (tm - callsList[0]) >= seconds:
                    del callsList[0]
                    total = len(callsList)
                time.sleep(0.1)
            return total
        @wraps(function)
        def wrapper(*args, **kwargs):
            cls.log.debug(f'before call {function.__name__}, totalSecondCalls= {len(callsList)}')
            refreshAndWait()
            tm = time.time()
            ret =  function(*args, **kwargs)
            callsList.append(tm)
            cls.log.debug(f'After call {function.__name__}, totalSecondCalls= {len(callsList)}')
            return ret

        return wrapper
    def __init__(self, config):
        pass

if __name__ == '__main__':
    logInit()
    sys.exit(0)
