#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML
import numpy as np
import matplotlib.pyplot as plt
from futu import *

from pyhocon import ConfigFactory

import sys,time,inspect,os
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from Log import logInit
from gw.BaseGateway import BaseGateway
from datetime import datetime,timedelta

import click


class GwFutu(BaseGateway):
    log = logging.getLogger("main.GwFutu")
    def __init__(self,config):
        BaseGateway.__init__(self,config)
        self.source_ = 'Yahoo'
        self.futuCtx_ = OpenQuoteContext(host='127.0.0.1', port=11111)
        pass
    def getSnapshot(self, hkCodeList):
        quote_ctx = self.futuCtx_
        ret, data = quote_ctx.get_market_snapshot(hkCodeList)
        if ret != RET_OK:
            self.log.error(data)
            return
        return data

    def mdownloadByWatchList(self,watchList):
        ret, data = self.futuCtx_.get_user_security(watchList)
        if ret != RET_OK:
            self.log.critical(data); assert False, data
            return None
        dfO = None
        data  = data[data.stock_type == 'STOCK']
        cnt  = 0
        totalCnt =  data.shape[0]
        display(data)
        for index,row in data.iterrows():
            code  = row.code
            name  = row['name']
            cnt += 1
            df = self.getKLine(code)
            df.columns = pd.MultiIndex.from_product([[code],df.columns, ])
            if dfO  is None:
                dfO = df
            else:
                dfO  =  pd.merge_asof(dfO , df, right_index=True, left_index=True, suffixes=('',''))
            self.log.debug(f'{cnt}/{totalCnt} {code}-{name} finished ')
        return dfO

    def disconnect(self):
        self.futuCtx_.close()
        self.futuCtx_ = None
        pass
    def getKLine(self,code,ktype=KLType.K_5M, days=90):
        '''
        分 K 提供最近 2 年数据，日 K 及以上提供最近 10 年的数据。
        美股盘前和盘后 K 线仅支持 60 分钟及以下级别。由于美股盘前和盘后时段为非常规交易时段，此时段的 K 线数据可能不足 2 年。
        '''
        #AuType.NONE
        now = datetime.now()
        start = now - timedelta(days=days)
        start = start.strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
        autype = AuType.QFQ
        max_count = 1024
        page_req_key = None
        ret, data, page_req_key = self.futuCtx_.request_history_kline(code, start=start,end= end,autype=autype, max_count=max_count,page_req_key= page_req_key,ktype=ktype)
        if ret != RET_OK:
            self.log.critical(data); assert False, f'{data} start={start} end={end}'
        dataRet = [data,]
        while page_req_key is not None:
            ret, data, page_req_key = self.futuCtx_.request_history_kline(code, start=start,end= end,autype=autype, max_count=max_count,page_req_key= page_req_key,ktype=ktype)
            if ret != RET_OK:
                self.log.critical(data); assert False, f'ktype:{ktype}   {data}'
            dataRet.append(data)
        dataRet = pd.concat(dataRet,ignore_index=True)
        dataRet.time_key  = dataRet.time_key.astype(np.datetime64)
        dataRet.set_index('time_key', inplace=True)
        dataRet = dataRet[['open', 'high', 'low', 'close', 'volume']]
        self.df_ = dataRet
        return dataRet
    pass

@click.command()
@click.argument('dst')
@click.option('--interval',  help='5m,1m etc', default='5m')
def mdownload(dst, interval):
    confPath = '../conf/v-trade.utest.conf'
    c = ConfigFactory.parse_file(confPath)
    gw = GwFutu(c)
    df  = gw.mdownloadByWatchList('hk_top100')
    df.to_csv(dst)
    gw.disconnect()
    pass



@click.command()
def test():
    import doctest; doctest.testmod();
    sys.exit(0)
    pass

@click.group()
def cli():
    pass

if __name__ == '__main__':
    logInit()

    cli.add_command(mdownload)
    cli.add_command(test)
    cli()
    '''


def downloadAllOptionHKSecurities():
    us = UserSecurity()
    d = DataDownloadFutu()
    df =us.getSecuritiesList('optionHK')[['code', 'name']]
    dfRet = pd.DataFrame()
    for r in df.iterrows():
        num = r[0]
        name = f'{r[1][1]}@{r[1][0]}'
        code = r[1][0]
        dfO = d.getKLine(code, ktype=KLType.K_60M ,days=2*365)[['open','high','low','close','volume']]
        if dfRet.index.size ==0:
            dfRet  = dfO.add_suffix(f'_{name}')
        else:
            dfRet = pd.merge_asof(dfRet, dfO, right_index=True, left_index=True, suffixes=('',f'_{name}'))
        print(f'finish {num} {name} ')
        if num == 3:
            display(dfRet)
        pass
    print("to_csv('./optionHK_securities_1h.csv'")
    d.close()
    dfRet.to_csv('./optionHK_securities_1h.csv')
    print("Done:to_csv('./optionHK_securities_1h.csv'")
    pass

downloadAllOptionHKSecurities();sys.exit(0)
    '''
