#!/usr/local/bin/python3
from futu import *
import logging,json

from IPython import display

from logging.handlers import TimedRotatingFileHandler

# 获取logger实例，如果参数为空则返回root logger,不同模块最好使用不同实例名字
debugLogger = logging.getLogger("quotation_push")
dataLogger =  logging.getLogger("quotation_push.data")

def loggerSetup():
    global debugLogger, dataLogger
    # 指定日志的最低输出级别，默认为WARN级别
    LOG_NAME = 'quotation_push'
    debugLogger.setLevel(logging.DEBUG)
    # 指定debugLogger输出格式
    formatter = logging.Formatter(
        '%(asctime)s %(filename)s [line:%(lineno)d] %(funcName)s %(levelname)s %(message)s %(process)d ')
    # 文件日志
    log_path = os.path.realpath(os.getcwd()) + '/log/'
    # 控制台日志
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.formatter = formatter  # 也可以直接给formatter赋值
    # 日志轮转--与file_handler同时存在时会造成日志重复打印--具体详情见下面日志重复问题
    # S-M-H-D
    timeRotatingHandler = TimedRotatingFileHandler(log_path + '%s.log' % (LOG_NAME), when='H')
    #remove extra info
    formatter = logging.Formatter()
    timeRotatingHandler.setFormatter(formatter)
    #timeRotatingHandler.suffix = "_%Y%m%d-%H%M%S.log"
    timeRotatingHandler.suffix = "_%Y%m%d-%H.log"
    # 为debugLogger添加的日志处理器
    debugLogger.addHandler(console_handler)
    dataLogger.addHandler(timeRotatingHandler)
    ## 输出不同级别的log
    #debugLogger.debug('this is debug info')
    #time.sleep(1)
    #dataLogger.info('this is information')
    #time.sleep(1)
    #dataLogger.warning('this is warning message')
    #time.sleep(1)
    #dataLogger.error('this is error message')
    #time.sleep(1)
    #dataLogger.fatal('this is fatal message, it is same as logger.critical')
    #time.sleep(1)
    #dataLogger.critical('this is critical message')
    #time.sleep(1)
    #dataLogger.error('this is error message')
    #time.sleep(1)
    #dataLogger.fatal('this is fatal message, it is same as logger.critical')
    #time.sleep(1)
    pass







'''
    BrokerImpl <class 'list'>
    CurKlineImpl <class 'pandas.core.frame.DataFrame'>
    OrderBookImpl <class 'dict'>
    RTDataImpl <class 'pandas.core.frame.DataFrame'>
    StockQuoteImpl <class 'pandas.core.frame.DataFrame'>
    TickerImpl <class 'pandas.core.frame.DataFrame'>
'''

class Writer4DataFram:
    '''
    https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_csv.html
    '''

    def write(self, data,ret_code):
        if ret_code != RET_OK:
            debugLogger.warning("{}: error, msg: {}".format(self.__class__.__name__, data))
            return RET_ERROR, data

        s = data.to_csv(path_or_buf=self.path_
            ,sep=','
            ,  float_format=self.float_format_
            , columns=self.columns_
            , header=True
            , index=False, index_label=None
            , mode='w')
        clsName = self.__class__.__name__
        dataLogger.info('{} {}'.format(clsName,s))
        return RET_OK, data

    pass


class StockQuoteImpl(StockQuoteHandlerBase,Writer4DataFram):
    ''' 实时报价
    https://openapi.futunn.com/futu-api-doc/quote/update-stock-quote.html

    code,data_date,data_time,last_price,open_price,high_price,low_price,prev_close_price,volume,turnover,turnover_rate,amplitude,suspension,listing_date,price_spread,sec_status
    HK.00700,2021-06-07,15:18:41,600.5,611.0,611.5,600.0,611.5,15648804,9466549010.0,0.163,1.881,False,2004-06-16,0.5,NORMAL


    '''
    def __init__(self):
        #super(StockQuoteImpl, self).init_format()
        self.path_ = None
        self.float_format_ = None
        self.columns_ = ["code","data_date","data_time","last_price","open_price","high_price","low_price","prev_close_price","volume","turnover","turnover_rate","amplitude","suspension"
            ,"listing_date","price_spread"
            #,"dark_status"
            ,"sec_status",
            ]
        pass

    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(StockQuoteImpl,self).on_recv_rsp(rsp_pb)
        return self.write(data,ret_code)


class CurKlineImpl(CurKlineHandlerBase, Writer4DataFram):
    ''' 实时K
    https://openapi.futunn.com/futu-api-doc/quote/update-kl.html
    '''
    def __init__(self):
        #super(StockQuoteImpl, self).init_format()
        self.path_ = None
        self.float_format_ = None
        self.columns_ = None
        pass
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(CurKlineImpl,self).on_recv_rsp(rsp_pb)
        return self.write(data,ret_code)

class RTDataImpl(RTDataHandlerBase, Writer4DataFram):
    ''' 分时
    https://openapi.futunn.com/futu-api-doc/quote/update-rt.html
    '''
    def __init__(self):
        #super(StockQuoteImpl, self).init_format()
        self.path_ = None
        self.float_format_ = None
        self.columns_ = None
        pass
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(RTDataImpl, self).on_recv_rsp(rsp_pb)
        return self.write(data,ret_code)

class TickerImpl(TickerHandlerBase,Writer4DataFram):
    ''' Ticker 实时逐笔
    https://openapi.futunn.com/futu-api-doc/quote/update-ticker.html
    '''
    def __init__(self):
        #super(StockQuoteImpl, self).init_format()
        self.path_ = None
        self.float_format_ = None
        self.columns_ = None
        pass
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(TickerImpl,self).on_recv_rsp(rsp_pb)
        return self.write(data,ret_code)

class OrderBookImpl(OrderBookHandlerBase):
    ''' 实时摆盘
        https://openapi.futunn.com/futu-api-doc/quote/update-order-book.html
        'Ask': [ (ask_price1, ask_volume1，order_num, {'orderid1': order_volume1, 'orderid2': order_volume2, …… }), (ask_price2, ask_volume2, order_num, {'orderid1': order_volume1, 'orderid2': order_volume2, …… }),…]
        'Bid': [ (bid_price1, bid_volume1, order_num, {'orderid1': order_volume1, 'orderid2': order_volume2, …… }), (bid_price2, bid_volume2, order_num,  {'orderid1': order_volume1, 'orderid2': order_volume2, …… }),…]

    '''
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super(OrderBookImpl,self).on_recv_rsp(rsp_pb)
        #print('{} {}'.format(self.__class__.__name__,type(data))); return RET_OK, data
        if ret_code != RET_OK:
            print("OrderBookImpl: error, msg: %s" % data)
            return RET_ERROR, data
        print("OrderBookImpl ", data) # OrderBookImpl 自己的处理逻辑
        print(json.dumps(data))
        return RET_OK, data

class BrokerImpl(BrokerHandlerBase):
    ''' Broker 实时经纪
    https://openapi.futunn.com/futu-api-doc/quote/update-broker.html
    '''
    def on_recv_rsp(self, rsp_pb):
        ret_code, err_or_stock_code, data = super(BrokerImpl, self).on_recv_rsp(rsp_pb)
        #print('{} {}'.format(self.__class__.__name__,type(data))); return RET_OK, data
        if ret_code != RET_OK:
            print("BrokerImpl: error, msg: {}".format(err_or_stock_code))
            return RET_ERROR, data
        print("BrokerImpl: stock: {} data: {} ".format(err_or_stock_code, data))  # BrokerImpl 自己的处理逻辑
        return RET_OK, data


class QuotationPush:
    def __init__(self):
        self.ctxList_ = []
        pass
    def subscribe(self, ClsHandle, stockList, subTypeList):
        ctx =  OpenQuoteContext(host='127.0.0.1', port=11111)
        ctx.set_handler(ClsHandle())
        ctx.subscribe(stockList, subTypeList)
        self.ctxList_ .append(ctx)
        pass

    def close(self):
        for ctx in self.ctxList_:
            ctx.close()
    pass



if __name__ == '__main__':
    loggerSetup()
    stockList  = ['HK.00700']
    stockList  = ['HK.01211','HK.01810'] #比亚迪

    p = QuotationPush()
    p.subscribe(StockQuoteImpl, stockList, [SubType.QUOTE])  # 订阅实时报价类型，FutuOpenD 开始持续收到服务器的推送
    p.subscribe(CurKlineImpl, stockList, [SubType.K_1M])
    p.subscribe(RTDataImpl, stockList, [SubType.RT_DATA])
    p.subscribe(TickerImpl, stockList, [SubType.TICKER])
    #p.subscribe(OrderBookImpl, ['HK.00700'], [SubType.ORDER_BOOK])
    #p.subscribe(BrokerImpl, ['HK.00700'], [SubType.BROKER])
    time.sleep(3600*8)  #  设置脚本接收 FutuOpenD 的推送持续时间为15秒
    p.close()
    sys.exit(0)

