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
        self.ctx_ = None
        self.df_ = None
        pass

    def open(self):
        if self.ctx_ is not None:
            return
        self.ctx_ = OpenQuoteContext(host='127.0.0.1', port=11111)
        pass

    def close(self):
        if self.ctx_ is  None:
            return
        self.ctx_.close()
        pass
    def getFileName(self,code,dataType):
        dataDir = f'{curDir}/b.data'
        if dataType == KLType.K_1M:
            t = 'K1M'
        elif dataType == KLType.K_5M:
            t = 'K5M'
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

    def ohlcv(self,df=None):
        df = self.df_ if df is None else df
        o,h,l,c,v = df.open,df.close, df.high,df.low,df.volume
        return o,h,l,c,v

    def readKLineFromCsv(self,code,ktype=KLType.K_DAY):
        csvPath = self.getFileName(code,ktype)
        self.df_ = pd.read_csv(csvPath,index_col=0,parse_dates=True)
        return self.df_

    def downloadKLine(self,code,ktype=KLType.K_DAY,days=6*365):
        self.getKLine(code,ktype,days)
        csvPath = self.getFileName(code,ktype)
        self.df_.to_csv(csvPath)
        h = self.df_.head(1).index[0]
        t = self.df_.tail(1).index[0]
        print(f'f,h,t:({csvPath,h,t}) downloaded!')

        pass

    def getKLine(self,code,ktype=KLType.K_DAY, days=6*365):
        '''
        分 K 提供最近 2 年数据，日 K 及以上提供最近 10 年的数据。
        美股盘前和盘后 K 线仅支持 60 分钟及以下级别。由于美股盘前和盘后时段为非常规交易时段，此时段的 K 线数据可能不足 2 年。
        '''
        #AuType.NONE
        self.open()
        now = datetime.now()
        start = now - timedelta(days=days)
        start = start.strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
        autype = AuType.QFQ
        max_count = 1024
        page_req_key = None
        ret, data, page_req_key = self.ctx_.request_history_kline(code, start=start,end= end,autype=autype, max_count=max_count,page_req_key= page_req_key,ktype=ktype)
        if ret != RET_OK:
            self.log.critical(data); assert False, f'{data} start={start} end={end}'
        dataRet = [data,]
        while page_req_key is not None:
            ret, data, page_req_key = self.ctx_.request_history_kline(code, start=start,end= end,autype=autype, max_count=max_count,page_req_key= page_req_key,ktype=ktype)
            if ret != RET_OK:
                self.log.critical(data); assert False, f'ktype:{ktype}   {data}'
            dataRet.append(data)
        dataRet = pd.concat(dataRet,ignore_index=True)
        dataRet.time_key  = dataRet.time_key.astype(np.datetime64)
        dataRet.set_index('time_key', inplace=True)
        self.df_ = dataRet
        return dataRet
        pass

    def downloadRehab(self,code):
        '''
        复权后价格 = 复权前价格 * 复权因子 A + 复权因子 B
        '''
        self.open()
        ret,data = self.ctx_.get_rehab(code)
        if ret != RET_OK:
            self.log.critical(data); assert False, data
        print(data)
        pass
    def getCapitalFlow(self,code):
        #ret,data = self.ctx_.get_capital_flow(code)
        #ret,data = self.ctx_.get_capital_distribution(code)
        # 所属板块
        self.open()
        ret,data = self.ctx_.get_owner_plate(code)
        if ret != RET_OK:
            self.log.critical(data); assert False, data
        print(data)
        pass
    def aggrOHLC(self, rule='5T'):
        df1= self.df_.resample(rule).agg({
            'open':'first'
            ,'close':'last'
            ,'high':'max'
            ,'low':'min'
            ,'volume':'sum'
            })
        #df1= self.df_.resample(rule).ohlc()
        return df1
        pass
    pass

def t_aggr():
    code  = 'HK.00700'
    d = DataDownloadFutu()
    df = d.readKLineFromCsv(code,KLType.K_1M)
    display(df.tail(15))
    df1 = d.aggrOHLC('5T')
    display(df1.tail(15))
    d.close()
    sys.exit(0)
    pass

def t_download():
    code  = 'HK.00700'
    d = DataDownloadFutu()
    days = 30
    d.downloadKLine(code,KLType.K_5M,days)
    d.downloadKLine(code,KLType.K_1M,days)
    d.close()
    sys.exit(0)
    pass

if __name__ == '__main__':
    logInit()
    t_download()
    t_aggr()
    d = DataDownloadFutu()
    #d.downloadRehab('HK.00700')
    code  = 'HK.03690'
    code  = 'HK.MIU210729P24000'
    code  = 'HK.01810'
    code  = 'HK.MIU210729C27000'
    code  = 'HK.01211' #比亚迪股份
    #d.downloadKLine(code,KLType.K_DAY)
    df  = d.getKLine(code,KLType.K_1M,50)
    display(df); d.close(); sys.exit(0)

    d.downloadKLine(code,KLType.K_1M)
    d.close()
    sys.exit(0)
    d.downloadKLine(code,KLType.K_WEEK)
    d.downloadKLine(code,KLType.K_30M)
    #d.getCapitalFlow(code)
