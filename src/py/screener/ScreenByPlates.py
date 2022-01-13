#!/usr/bin/env python3
# coding=utf-8
#from futu import *
from IPython.display import display, HTML
from google.protobuf.descriptor_pool import Default
from pyhocon import ConfigFactory
import os.path,os,sys,time
import json
#analysis stocks in the same plate.

from futu import *
from functools import wraps
import click

import sys,time,inspect,os,logging
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from Log import logInit
from screener.SpeedControl import SpeedControl



class StockWithPlates:
    log = logging.getLogger("main.StockWithPlates")
    plateCodeToCnName = dict()
    stocks = dict()
    def __init__(self, code, stock_name, list_time):
        self.code_ = code
        self.stock_name_ = stock_name
        self.list_time_ = list_time
        self.plates_ = dict() #pl1: weight; pl2: weight........
        pass
    def __repr__(self):
        plates = ';'.join([f'{StockWithPlates.plateCodeToCnName[p]}:{w}' for p,w in self.plates_.items()])
        return f'{self.code_},{self.stock_name_},{self.list_time_},{plates} '
    @classmethod
    def to_json(cls, fp=None):
        stocks = dict()
        for k,v in cls.stocks.items():
            stock = {'code':v.code_, 'stock_name':v.stock_name_, 'list_time':v.list_time_, 'plates': v.plates_}
            stocks[k] = stock
        j = dict()
        j['plateCodeToCnName'] = cls.plateCodeToCnName
        j['stocks'] = stocks
        if fp is not None:
            json.dump(j, fp)
            return None
        else:
            return json.dumps(j)


    @classmethod
    def read_json_(cls, j):
        cls.plateCodeToCnName = j['plateCodeToCnName']
        cls.stocks = dict()
        for k,v in j['stocks'].items():
            if v['code']  not in cls.stocks:
                stock = StockWithPlates(v['code'], v['stock_name'],v['list_time'])
                cls.stocks[k] = stock
            else:
                stock = cls.stocks[k]
            stock.plates_ = v['plates']
        pass
    @classmethod
    def read_json_file(cls, file):
        with open(file,'r' ) as fp:
            j = json.load(fp)
            cls.read_json_(j)
        fp.close()
        pass

    @classmethod
    def read_json_str(cls, s):
        j = json.loads(s)
        cls.read_json_(j)
        pass
    @classmethod

    def fromFutu(cls, quote_ctx, maxPlates = -1):
        '''
        - https://openapi.futunn.com/futu-api-doc/quote/get-plate-stock.html
        '''
        # pl = Plate.REGION
        df = None
        for pl in [Plate.CONCEPT, Plate.INDUSTRY]:
            ret, data = quote_ctx.get_plate_list(Market.US,pl)
            assert ret == RET_OK , data
            df = data if df is None else pd.concat([df, data])
        if maxPlates > 0:
            df = df.head(maxPlates)
        for index,row in df.iterrows():
            cls.plateCodeToCnName[row.code] = row.plate_name
            ret, data = quote_ctx.get_plate_stock(row.code)
            assert ret == RET_OK,data
            data.code = data.code.str.replace('^US\.','' ,regex=True)
            for i,r in data.iterrows():
                if r.code  not in cls.stocks:
                    stock = cls(r.code, r.stock_name,r.list_time)
                    cls.stocks[r.code] = stock
                else:
                    stock = cls.stocks[r.code]
                stock.plates_[row.code] = 1.0

        pass


@click.command()
@click.argument('dst')
@click.option('--max_plates',  help='', default = -1)
def fromFutu(dst, max_plates):
    logInit()
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    callLimitList = []
    quote_ctx.get_plate_stock = SpeedControl.controlMaxCallsPerPeriod(quote_ctx.get_plate_stock,callLimitList, maxCalls=10,seconds=30)
    StockWithPlates.fromFutu(quote_ctx,max_plates)
    j = StockWithPlates.to_json()
    StockWithPlates.read_json(j)
    assert dst.endswith('.json') , f'dst:{dst} does not end with .json'
    with open(dst, "w") as fp:
        StockWithPlates.to_json(fp)
    fp.close()
    quote_ctx.close() # 结束后记得关闭当条连接，防止连接条数用尽
    pass

@click.group()
def cli():
    pass


if __name__ == '__main__':
    logInit()
    cli.add_command(fromFutu)
    cli(); sys.exit(0)
