#!/usr/bin/env python3
# coding=utf-8
import re,os
from futu import *
from IPython.display import display, HTML
import talib
import yfinance as yf
import numpy as np
from datetime import datetime
from datetime import timedelta
curDir = os.path.abspath(os.path.dirname(__file__))
#sys.path.append("{}/lib".format(curDir))

from Log import logInit

'''
- https://openapi.futunn.com/futu-api-doc/quote/get-rehab.html
- https://openapi.futunn.com/futu-api-doc/quote/get-owner-plate.html
Use class Visualize to display the candle figures.
'''

class DataDownloadFutu:
    log = logging.getLogger("main.DataDownloadFutu")
    def __init__(self):
        self.ctx_ = OpenQuoteContext(host='127.0.0.1', port=11111)
        pass
    def close(self):
        self.ctx_.close()
        pass
    def getFileName(self,code,dataType):
        dataDir = f'{curDir}/b.data'
        if dataType == KLType.K_1M:
            t = 'K1M'
        elif dataType == KLType.K_30M:
            t = 'K30M'
        elif dataType == KLType.K_DAY:
            t = 'KD'
        elif dataType == KLType.K_WEEK:
            t = 'KW'
        elif dataType == KLType.K_MON:
            t = 'KMON'
        elif dataType == KLType.K_YEAR:
            t = 'KY'
        else:
            t = 'UNKNOWN'
        return f'{dataDir}/{code}.{t}.csv'

    def downloadKLine(self,code,ktype=KLType.K_DAY):
        '''
        分 K 提供最近 2 年数据，日 K 及以上提供最近 10 年的数据。
        美股盘前和盘后 K 线仅支持 60 分钟及以下级别。由于美股盘前和盘后时段为非常规交易时段，此时段的 K 线数据可能不足 2 年。
        '''
        #AuType.NONE
        now = datetime.now()
        start = now - timedelta(days=6*365)
        start = start.strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
        autype = AuType.QFQ
        max_count = 1024
        page_req_key = None
        code = 'HK.00700'
        ret, data, page_req_key = self.ctx_.request_history_kline(code, start=start,end= end,autype=autype, max_count=max_count,page_req_key= page_req_key,ktype=ktype)
        if ret != RET_OK:
            self.log.critical(data); assert False, f'{data} start={start} end={end}'
        dataRet = [data,]
        while page_req_key is not None:
            ret, data, page_req_key = self.ctx_.request_history_kline(code, start=start,end= end,autype=autype, max_count=max_count,page_req_key= page_req_key,ktype=ktype)
            if ret != RET_OK:
                self.log.critical(data); assert False, data
            dataRet.append(data)
        dataRet = pd.concat(dataRet,ignore_index=True)
        dataRet.set_index('time_key', inplace=True)
        csvPath = self.getFileName(code,ktype)
        dataRet.to_csv(csvPath)

        pass

        def downloadRehab(self,code):
            '''
            复权后价格 = 复权前价格 * 复权因子 A + 复权因子 B
            '''
            ret,data = self.ctx_.get_rehab(code)
            if ret != RET_OK:
                self.log.critical(data); assert False, data
            print(data)
            pass
        def getCapitalFlow(self,code):
            #ret,data = self.ctx_.get_capital_flow(code)
            #ret,data = self.ctx_.get_capital_distribution(code)
            # 所属板块
            ret,data = self.ctx_.get_owner_plate(code)
            if ret != RET_OK:
                self.log.critical(data); assert False, data
            print(data)
            pass
        pass
    pass

if __name__ == '__main__':
    logInit()
    d = DataDownloadFutu()
    #d.downloadRehab('HK.00700')
    #td.downloadKLine('HK.00700',KLType.K_DAY)
    #d.downloadKLine('HK.00700',KLType.K_1M)
    d.downloadKLine('HK.00700',KLType.K_WEEK)
    d.downloadKLine('HK.00700',KLType.K_30M)
    #d.getCapitalFlow('HK.00700')
    d.close()
