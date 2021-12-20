#!/usr/bin/env python3
# coding=utf-8
#from ib_insync import *
import sys,time

import BaseGateway
import yfinance as yf
import numpy as np
import pandas as pd

class GwYahoo(BaseGateway.BaseGateway):
    def __init__(self):
        BaseGateway.BaseGateway.__init__(self)
        pass
    pass


if __name__ == '__main__':
    sys.exit(0)
