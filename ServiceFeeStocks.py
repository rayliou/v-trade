#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
import datetime,sys
import logging,json
from IPython.display import display, HTML


import math,sys
#reload(sys)  # Reload does the trick!
#sys.setdefaultencoding('UTF8')

'''
https://support.futuhk.com/en-us/topic283?from_platform=1&platform_langArea=&lang=en-us
class ServiceFeeStocksUS:
class ServiceFeeStocksHK:

'''

class ServiceFeeStocksUS:
    log = logging.getLogger("main.ServiceFeeStocksUS")
    DATE_FORMAT = '%Y%m%d'
    TIME_FORMAT = '%H%M%S'
    def __init__(self):
        pass

    def cmpComission(self, quantity):
        v0  = self.comissionV0(quantity)
        v1  = self.comissionV1(quantity)
        v2  = self.comissionV2(quantity)
        self.log.debug('Quantity,V0,V1,V2:\t {},{},{},{}'.format(quantity, v0,v1,v2))
        pass

    def comissionV0(self, quantity):
        # < 200 shares  1.99
        fee = platformFee = 0.0
        comission  = quantity * 0.01
        comission  = max(1.99, comission)
        #self.log.debug('V0:comission/Platform Fee\t {},{}'.format(comission,platformFee))
        fee  += comission
        return fee

    def comissionV1(self, quantity):
        fee =  0.0
        platformFee = 0.005 * quantity
        platformFee = max(platformFee,1.00)
        fee += platformFee
        comission  = quantity * 0.0049
        comission  = max(0.99, comission)
        #self.log.debug('V1:comission/Platform Fee\t {},{}'.format(comission,platformFee))
        fee  += comission
        return fee

    def comissionV2(self, quantity):
        fee =  0.0
        # Less than 500 orders
        platformFee = 0.01 * quantity
        # 501 - 1k
        #platformFee = 0.008 * quantity
        platformFee = max(platformFee,1.00)
        fee += platformFee
        comission  = quantity * 0.0049
        comission  = max(0.99, comission)
        #self.log.debug('V1:comission/Platform Fee\t {},{}'.format(comission,platformFee))
        fee  += comission
        return fee




    def regulatoryFee(self, quantity, price, isSell=True):
        fee  = 0.0
        #Clear Fee 交收费	0.003/股	美国结算机构
        # Settlement Fee
        clearingFee = quantity * 0.003
        self.log.debug('clearingFee\t {}'.format(clearingFee))
        fee += clearingFee
        if not isSell:
            return fee

        #证监会规费（仅卖出订单收取）	0.0000051*交易金额，最低0.01	美国证监会
        #注：交收日在2021年02月25日及以后的交易，适用于证监会规费费率「0.0000051*交易金额，最低0.01」。
        secFee = max(quantity* price * 0.0000051, 0.01)
        self.log.debug('secFee\t {}'.format(secFee))
        fee += secFee
        #交易活动费（仅卖出订单收取）	0.000119/股，最低0.01，最高5.95	美国金融业监管局
        taf = max( 0.000119 * quantity, 0.01)
        taf = min(taf, 5.95)
        self.log.debug('TAF Fee\t {}'.format(taf))
        fee += taf
        return fee

    def fee(self, quantity, price, isSell=True):
        fee  = self.regulatoryFee(quantity,price,isSell)
        fee  += self.comissionV0(quantity)
        return fee

    pass

'''
https://support.futuhk.com/en-us/topic335?from_platform=1&platform_langArea=
'''

class ServiceFeeStocksHK:
    log = logging.getLogger("main.ServiceFeeStocksHK")
    DATE_FORMAT = '%Y%m%d'
    TIME_FORMAT = '%H%M%S'
    def __init__(self):
        pass

    def cmpComission(self, amount):
        v1  = self.comissionV1(amount)
        v2  = self.comissionV2(amount)
        self.log.debug('amount,V1,V2:\t {},{},{}'.format(amount, v1,v2))
        pass


    def comissionV1(self, amount):
        fee =  0.0
        #FIXME
        platformFee = 20
        fee += platformFee
        comission  = amount * 0.03 / 100
        comission  = max(3, comission)
        self.log.debug('V1:comission/Platform Fee\t {},{}'.format(comission,platformFee))
        fee  += comission
        return fee

    def comissionV2(self, amount):
        fee =  0.0
        #FIXME
        platformFee = 20
        fee += platformFee
        comission  = amount * 0.03 / 100
        comission  = max(3, comission)
        self.log.debug('V1:comission/Platform Fee\t {},{}'.format(comission,platformFee))
        fee  += comission
        return fee





    def regulatoryFee(self, quantity, price, isSell=True):
        amount = quantity * price
        fee  = 0.0
        #Trading   System Usage Fee	HK$0.50 per transaction	Hong Kong Exchanges and Clearing   Limited (「HKEX」)
        tradeSysFee  = 0.50
        self.log.debug(f'tradeSysFee:\t{tradeSysFee}')
        fee += tradeSysFee
        #Settlement Fee	0.002% * transaction amount,   minimum HK$2.00, maximum HK$100.00	HKEx
        clearingFee = amount * 0.002 /100
        clearingFee = max(clearingFee,2.00)
        clearingFee = min(clearingFee,100.00)
        self.log.debug(f'clearingFee:\t{clearingFee}')
        fee += clearingFee
        # 股票交易印花税的税率将由目前买卖双方各付0.1%提高至0.13%。有关调整会在今年8月1日生效
        # https://finance.sina.com.cn/jjxw/2021-06-03/doc-ikqciyzi7556560.shtml
        stampDutyChange = strftime = datetime.datetime.strptime("2021-8-1", "%Y-%m-%d")
        now  = datetime.datetime.now()
        assert now < stampDutyChange , f'stamp duty last day {stampDutyChange} '


        stampDuty = 0.1 /100 * amount
        stampDuty = math.ceil(stampDuty)
        self.log.debug(f'statmpDuty:\t{stampDuty}')
        fee += stampDuty
        #Trading Fee	0.005% * transaction amount,   minimum HK$0.01	HKEx
        tradeFee = 0.005 / 100 * amount
        tradeFee = max(0.01, tradeFee)
        self.log.debug(f'tradeFee:\t{tradeFee}')
        fee += tradeFee
        #Transaction levy	0.0027% * transaction amount,   minimum HK$0.01	SFC
        transactionLevy = 0.0027 / 100 * amount
        transactionLevy = max(0.01, transactionLevy)
        self.log.debug(f'transactionLevy:\t{transactionLevy}')
        fee += transactionLevy
        return fee

    def fee(self, quantity, price, isSell=True):
        fee  = self.regulatoryFee(quantity,price,isSell)
        fee  += self.comissionV2(quantity*price)
        return fee

    pass

class ColorLogFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    #format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format = '%(levelname)s %(asctime)s [%(filename)s:%(lineno)d] %(funcName)s %(message)s %(process)d '

    ##fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

if __name__ == '__main__':
    log = logging.getLogger("main" )
    log.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        '%(levelname)s %(asctime)s [%(filename)s:%(lineno)d] %(funcName)s %(message)s %(process)d ')

    fmt = ColorLogFormatter()
    s = logging.StreamHandler(sys.stderr)
    s.setFormatter(fmt)
    #s.setLevel(logging.DEBUG)
    log.addHandler(s)
    log.critical('cccc')
    log.error('cccc')
    log.fatal('cccc')

    u = ServiceFeeStocksUS()
    h = ServiceFeeStocksHK()

    u.cmpComission(2)
    u.cmpComission(20)
    u.cmpComission(120)
    u.cmpComission(199)
    u.cmpComission(200)
    u.cmpComission(201)
    u.cmpComission(500)
    h.fee(100, 600)
    #self.log.debug( f'S 500:9.18{f.fee(500, 9.18,True) } ')
    #self.log.debug( f'S Apple 20:127.21   {f.fee(20, 127.21,True) } ')
    #self.log.debug( f'B QCom 30:133.25   {f.fee(30, 133.25,False) } ')
    sys.exit(0)




