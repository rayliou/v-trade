#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML


'''
- HK https://openapi.futunn.com/futu-api-doc/trade/get-position-list.html
- US https://github.com/ranaroussi/yfinance/
'''

class History:
    def __init__(self):
        #self.ctx_ = OpenUSTradeContext(host='127.0.0.1', port=11111, is_encrypt=None, security_firm=SecurityFirm.FUTUSECURITIES)
        self.ctx_ = OpenHKTradeContext(host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES)

        pass
    pass

if __name__ == '__main__':
    h = History()
    sys.exit(0)
