#!/usr/bin/env python3
# coding=utf-8
#from ib_insync import *
# import pandas as pd
# import numpy as np
# from IPython.display import display, HTML
# from datetime import datetime,timedelta,date
# import matplotlib.pyplot as plt
# import logging
#
# from ibapi import wrapper,client, contract,scanner
# from ibapi.ticktype import TickTypeEnum,TickType
#
# import threading,queue
# import socket
#
# from pyhocon import ConfigFactory
#
# import sys,time,inspect,os
# currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
# parentdir = os.path.dirname(currentdir)
# sys.path.insert(0, parentdir)
# from Log import logInit
# from gw.BaseGateway import BaseGateway
# from gw.HistoricalDataLimitations import HistoricalDataLimitations
#
# import click,glob


from functools import wraps
from math import sqrt
import sys,time


class B:
    callsCurSec = []
    @classmethod
    def speedControl(cls, function, maxCalls =3, seconds=1):
        def refreshAndWait():
            total = len(cls.callsCurSec)
            while total >= maxCalls:
                tm = time.time()
                while total > 0 and  (tm - cls.callsCurSec[0]) >= seconds:
                    del cls.callsCurSec[0]
                    total = len(cls.callsCurSec)
                time.sleep(0.1)
            return total
        @wraps(function)
        def wrapper(*args, **kwargs):
            print(f'before call {function.__name__}, totalSecondCalls= {len(cls.callsCurSec)}')
            refreshAndWait()
            tm = time.time()
            ret =  function(*args, **kwargs)
            cls.callsCurSec.append(tm)
            print(f'After call {function.__name__}, totalSecondCalls= {len(cls.callsCurSec)}')
            return ret

        return wrapper
    def __init__(self):
        self.p = B.speedControl(self.p,3)
        pass
    def p(self):
        print(' call p')
    def run(self):
        self.p()
        self.p()
        self.p()
        time.sleep(1)
        self.p()
        self.p()
        self.p()



if __name__ == '__main__':
    b  = B()
    b.run()
    sys.exit(0)
