#!/usr/bin/env python3
# coding=utf-8
import re,io,logging
from futu import *
import datetime,sys
import json
import numpy as np
import pandas as pd
from IPython.display import display, HTML

from Log import logInit


import math,sys
#reload(sys)  # Reload does the trick!
#sys.setdefaultencoding('UTF8')

'''
https://support.futuhk.com/en-us/topic283?from_platform=1&platform_langArea=&lang=en-us
class ServiceFeeStocksUS:
class ServiceFeeStocksHK:

'''

def clipCeilFloor(data,lower= None, upper=None):
    if isinstance(data, pd.Series):
        data.clip(lower,upper,inplace=True)
    elif isinstance(clearingFee, float):
        if lower is not None:
            data = max(data,lower)
        if upper is not None:
            data = min(data,upper)
        pass
    else:
        assert False , f'Unknow type {type(data)} for {data}'
    return data

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
        comission  = clipCeilFloor(comission, 1.99)
        #self.log.debug('V0:comission/Platform Fee\t {},{}'.format(comission,platformFee))
        fee  += comission
        return fee

    def comissionV1(self, quantity):
        fee =  0.0
        platformFee = 0.005 * quantity
        platformFee = clipCeilFloor(platformFee,1.00)
        fee += platformFee
        comission  = quantity * 0.0049
        comission  = clipCeilFloor(comission,0.99)
        #self.log.debug('V1:comission/Platform Fee\t {},{}'.format(comission,platformFee))
        fee  += comission
        return fee

    def comissionV2(self, quantity):
        fee =  0.0
        # Less than 500 orders
        platformFee = 0.01 * quantity
        # 501 - 1k
        #platformFee = 0.008 * quantity
        platformFee = clipCeilFloor(platformFee,1.00)
        fee += platformFee
        comission  = quantity * 0.0049
        comission  = clipCeilFloor(comission,0.99)
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
        secFee = quantity* price * 0.0000051
        secFee = clipCeilFloor(secFee, 0.01)
        self.log.debug('secFee\t {}'.format(secFee))
        fee += secFee
        #交易活动费（仅卖出订单收取）	0.000119/股，最低0.01，最高5.95	美国金融业监管局
        taf =  0.000119 * quantity
        taf = clipCeilFloor( taf, 0.01, 5.95)
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
        comission  = clipCeilFloor(comission,3)
        self.log.debug('V1:comission/Platform Fee\t [{},{}]\n'.format(comission,platformFee))
        fee  += comission
        return fee

    def comissionV2(self, amount):
        fee =  0.0
        #FIXME
        platformFee = 20
        fee += platformFee
        comission  = amount * 0.03 / 100
        comission  = clipCeilFloor(comission,3)
        self.log.debug('V2:comission/Platform Fee\t [{},{}]\n'.format(comission,platformFee))
        fee  += comission
        return fee





    def regulatoryFee(self, quantity, price, isSell=True):
        amount = quantity * price
        fee  = 0.0
        #Trading   System Usage Fee	HK$0.50 per transaction	Hong Kong Exchanges and Clearing   Limited (「HKEX」)
        tradeSysFee  = 0.50
        self.log.debug(f'tradeSysFee:\t{tradeSysFee}')
        fee += tradeSysFee
        #Settlement Fee	0.002% * transaction amount,   minimum HK$2.00, Lagest HK$100.00	HKEx
        clearingFee = amount * 0.002 /100
        clearingFee = clipCeilFloor(clearingFee,2.00,100.00)
        self.log.debug(f'clearingFee:\t[{clearingFee}]\n')
        fee += clearingFee
        # 股票交易印花税的税率将由目前买卖双方各付0.1%提高至0.13%。有关调整会在今年8月1日生效
        # https://finance.sina.com.cn/jjxw/2021-06-03/doc-ikqciyzi7556560.shtml
        stampDutyChange = strftime = datetime.datetime.strptime("2021-8-1", "%Y-%m-%d")
        now  = datetime.datetime.now()
        assert now < stampDutyChange , f'stamp duty last day {stampDutyChange} '


        stampDuty = 0.1 /100 * amount
        if isinstance(stampDuty , pd.Series):
            stampDuty = np.ceil(stampDuty)
        elif isinstance(stampDuty , float):
            stampDuty = math.ceil(stampDuty)
        self.log.debug(f'statmpDuty:\t\n[{stampDuty}\\n')
        fee += stampDuty
        #Trading Fee	0.005% * transaction amount,   minimum HK$0.01	HKEx
        tradeFee = 0.005 / 100 * amount
        tradeFee = clipCeilFloor( tradeFee,0.01)
        self.log.debug(f'tradeFee:\t{tradeFee}')
        fee += tradeFee
        #Transaction levy	0.0027% * transaction amount,   minimum HK$0.01	SFC
        transactionLevy = 0.0027 / 100 * amount
        transactionLevy = clipCeilFloor(transactionLevy,0.01)
        self.log.debug(f'transactionLevy:\t{transactionLevy}')
        fee += transactionLevy
        return fee

    def fee(self, quantity, price, isSell=True):
        fee  = self.regulatoryFee(quantity,price,isSell)
        fee  += self.comissionV2(quantity*price)
        return fee

    pass


#log = logging.getLogger("main" )

def testFee():
    positionList = '''code,stock_name,qty,can_sell_qty,cost_price,cost_price_valid,market_val,nominal_price,pl_ratio,pl_ratio_valid,pl_val,pl_val_valid,today_buy_qty,today_buy_val,today_pl_val,today_sell_qty,today_sell_val,position_side,unrealized_pl,realized_pl
HK.09982,中原建业,2000.0,2000.0,3.0,True,4940.0,2.4699999999999998,-17.669999999999998,True,-1060.0,True,0.0,0.0,0.0,0.0,0.0,LONG,N/A,N/A
HK.06862,海底捞,200.0,200.0,44.2,True,7960.0,39.8,-9.950000000000001,True,-880.0,True,0.0,0.0,0.0,0.0,0.0,LONG,N/A,N/A
HK.02607,上海医药,100.0,100.0,17.76,True,1736.0,17.36,-2.25,True,-40.0,True,0.0,0.0,0.0,0.0,0.0,LONG,N/A,N/A
HK.01810,小米集团-W,2600.0,2600.0,29.1538,True,73190.0,28.15,-3.44,True,-2610.0,True,0.0,0.0,0.0,0.0,0.0,LONG,N/A,N/A
HK.00700,腾讯控股,200.0,200.0,607.75,True,119200.0,596.0,-1.9300000000000002,True,-2350.0,True,0.0,0.0,0.0,0.0,0.0,LONG,N/A,N/A '''

#https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.apply.html#pandas.DataFrame.apply
    p = pd.read_csv(io.StringIO(positionList))
    h = ServiceFeeStocksHK()
    #f = h.fee(p.qty, p.nominal_price)
    p2= p[['stock_name', 'qty', 'cost_price','nominal_price',]]
    #insert new coloumn
    f =  h.fee(p.qty, p.cost_price) *2
    p2.loc[:,'fee'] = f * 2
    p2.loc[:,'low_price'] = f /p.qty + p.cost_price

    display(p2)
    #p2 = pd.DataFrame()
    #p = pd.read_json(positionList,orient="index")
    pass

if __name__ == '__main__':
    logInit(logging.ERROR)
    testFee(); sys.exit(0)

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




