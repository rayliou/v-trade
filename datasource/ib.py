#!/usr/bin/env python3
# coding=utf-8
from ib_insync import *
import sys
import pandas as pd
import numpy as np
from IPython.display import display, HTML
from datetime import datetime,timedelta,date
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


'''
- https://ib-insync.readthedocs.io/api.html#module-ib_insync.ib
    https://ib-insync.readthedocs.io/api.html#ib_insync.ib.IB.reqHistoricalData
    + https://interactivebrokers.github.io/tws-api/historical_bars.html
    + https://interactivebrokers.github.io/tws-api/historical_limitations.html
    + https://www.interactivebrokers.com/cn/software/api/apiguide/api/historical_data_limitations.htm


    Duration	        Allowed Bar Sizes
    60 S    	        1 sec - 1 mins
    120 S   	        1 sec - 2 mins
    1800 S (30 mins)	1 sec - 30 mins
    3600 S (1 hr)	    5 secs - 1 hr
    14400 S (4hr)	    10 secs - 3 hrs
    28800 S (8 hrs)	    30 secs - 8 hrs
    1 D	                1 min - 1 day
    2 D	                2 mins - 1 day
    1 W	                3 mins - 1 week
    1 M	                30 mins - 1 month
    1 Y	                1 day - 1 month




'''

class IBKR:
    def __init__(self, port=4002):
        self.ib_ = IB()
        port = 7497
        port = 4002
        self.ib_.connect(readonly=True,port=port)
        pass

    def genContractsFromSymsList(self, symList):
        symList = symList.replace(',',' ').split()
        cList = [Stock(sym, 'SMART','USD') for sym in symList]
        return cList

    def reqMktData(self, symList):
        cList = self.genContractsFromSymsList(symList)
        self.ib_.qualifyContracts(*cList)
        tList = []
        for c in cList:
            t = self.ib_.reqMktData(c, genericTickList='221,104,106,105,101,', snapshot=False, regulatorySnapshot=False)
            tList.append(t)
        wait = True
        s = datetime.now() #- timedelta(minutes=1111113)
        while wait and (datetime.now() -s).seconds < 3 * 60 :
            self.ib_.sleep(0.1)
            #bList = [t.markPrice  > 0.1 and t.close  > 0.1 for t in tList]
            bList = [t.close  > 0.1 for t in tList]
            wait = not all(bList)
        df = util.df(tList)[['markPrice','close', 'histVolatility', 'impliedVolatility' ]]
        df.index = pd.Index(
            [t.contract.symbol for t in tList]
        )
        #df.to_csv('./abc.csv')
        return df

    def get_M_HistoryData(self, symList,
            durationStr='6 M', barSizeSetting='30 mins', years=2,useRTH=True ):
        dictWhatToShow = { 'HISTORICAL_VOLATILITY': 'hv',
                'OPTION_IMPLIED_VOLATILITY': 'iv',
                }
        df = self.getHistoryData( symList, durationStr, barSizeSetting, years,'TRADES',useRTH )
        for k,v in dictWhatToShow.items():
            dfk = self.getHistoryData( symList, durationStr, barSizeSetting, years,k,useRTH )
            dfk = dfk[['close']].rename(columns={"close":v })
            df  = pd.merge_asof(df, dfk, right_index=True, left_index=True, suffixes=('',''))

        df.set_index('date', inplace=True)
        display(df)

        fig = plt.figure(figsize = (12,8))
        ax1  = fig.add_subplot(211)

        ax2  = fig.add_subplot(212)
        df['iv/hv'] = df.iv/df.hv
        #df.to_csv(symList + '.csv', index=False)

        def qNearest(series):
            q = series.quantile(np.arange(0.05,1.05,0.05)) #if data is not None else q
            qRet  = []
            for d in series:
                idxSorted = (q - d).abs().argsort().iloc[:1]
                qRet.append( q.iloc[idxSorted].index[0])
            return qRet
        df['q_iv'] = qNearest(df.iv)
        df['q_IHV'] = qNearest(df['iv/hv'])

        df[['close']].plot(ax=ax1)
        df[['q_iv','q_IHV' ]].plot(ax=ax1,secondary_y=True)
        ax1.set_title(f'Close q_iv and q_iv/hv  of {symList}')

        df[['iv','hv' ]].plot(ax=ax2)
        ax2.set_title(f'iv,hv of {symList}')
        ax2.set_ylabel('iv,hv')

        plt.show()

        pass


    def getHistoryData(self, symList,
            durationStr='6 M', barSizeSetting='30 mins', years=2,whatToShow='TRADES',useRTH=True ):
        '''
        - TRADES:  date  open  high   low  close   volume  average  barCount
        '''
        cList = self.genContractsFromSymsList(symList)
        self.ib_.qualifyContracts(*cList)
        c = cList[0]
        now = datetime.now()
        curTime  = now
        start = now - timedelta(days=365*years)
        dt  = ''
        endDateTime='20100101 00:00:00 EST',
        barsList  = []
        #print(f'whatToShow:{whatToShow}')
        while curTime > start:
            print(f' start curTime:{curTime}')
            bars = self.ib_.reqHistoricalData(
                    c, endDateTime=dt,
                    durationStr=durationStr,
                    barSizeSetting=barSizeSetting,
                    whatToShow=whatToShow,
                    useRTH=useRTH,
                    formatDate=1)
            if len(bars) == 0:
                break
            print(bars[-1:])
            barsList.append(bars)
            dt  = bars[0].date
            self.ib_.sleep(0.1)
            curTime = datetime.strptime(dt.strftime('%Y%m%d'), '%Y%m%d') if isinstance(dt,date) else dt
            print(f' end curTime:{curTime}')
            if len(bars) < 10:
                break

        allBars = [b for bars in reversed(barsList) for b in bars]
        df = util.df(allBars)
        #display(df)
        return df

    def t(self, symList,
            durationStr='6 M', barSizeSetting='30 mins', years=2,whatToShow='TRADES',useRTH=True ):
        symList = symList.replace(',',' ').split()
        sym = symList[0]
        c = Stock(sym, 'SMART','USD')
        d  = date(2019, 5, 10)
        curTime = datetime.strptime(d.strftime('%Y%m%d'), '%Y%m%d')

        bars = self.ib_.reqHistoricalData(
                c, endDateTime=curTime,
                durationStr=durationStr,
                barSizeSetting=barSizeSetting,
                whatToShow=whatToShow,
                useRTH=useRTH,
                formatDate=1)
        print(len(bars))
        assert  not bars
        print(bars[-1:])
    pass


if __name__ == '__main__':
    import  doctest
    doctest.testmod();sys.exit(0)

    ibkr = IBKR()
    symList = 'UBER BBY TSLA AMD NVDA'
    symList = sys.argv[1]
    #df  = ibkr.reqMktData(symList); display(df); sys.exit(0)
    #ibkr.getHistoryData('NVDA,TSLA',durationStr='6 M', barSizeSetting='30 mins')
    #ibkr.get_M_HistoryData('BBY,TSLA',durationStr='1 M', barSizeSetting='30 mins',years=1)
    df = ibkr.get_M_HistoryData(symList,durationStr='1 Y', barSizeSetting='1 day',years=3)
    #ibkr.t(sys.argv[1],durationStr='1 Y', barSizeSetting='1 day',years=3)
    display(df); sys.exit(0)


    # util.startLoop()  # uncomment this line when in a notebook

    ib = IB()
    #help(ib.connect)
    ib.connect(readonly=True)
    #print( f'reqMktDepthExchanges:{  util.df(ib.reqMktDepthExchanges())}\n{"-"*10}\n'  )
    contract = Stock('DIDI', 'SMART', 'USD')

    print( f'reqHistogramData:  {  util.df(ib.reqHistogramData(contract,True, "3 days"))}\n{"-"*10}\n'  )
    spx = Index('SPX', 'CBOE')
    print(
        ib.qualifyContracts(spx)
    )
    a  = Stock('AAPL', 'SMART','USD')
    n  = Stock('NVDA', 'SMART','USD')
    #reference
    sys.exit(0)
    #[cd] = ib.reqContractDetails(n)
    #print(cd)
    sys.exit(0)

    ib.qualifyContracts(c)
    print( f'reqSecDefOptParams({c.symbol},{c.secType},{c.conId}) :  \n{  util.df(ib.reqSecDefOptParams(c.symbol,"", c.secType, c.conId))}\n{"-"*10}\n'  )
    df  = util.df(ib.reqSecDefOptParams(c.symbol,"", c.secType, c.conId))
    #df.to_csv('./abc.csv')
    bars = ib.reqHistoricalData(
            c,
            endDateTime='20210722 00:00:00 EST',
            durationStr='5 D', #durationStr='1800 S',
            barSizeSetting='1 day', #barSizeSetting='5 secs',
            whatToShow='TRADES',
            #whatToShow='ADJUSTED_LAST',
            useRTH=True,
            formatDate=1)
    df = util.df(bars)
    display(df)
    sys.exit(0)

    #s = f'''accountValues:{  util.df(ib.accountValues())};  '''
    #print(s)



    bars = ib.reqRealTimeBars(contract,5, whatToShow ='TRADES', useRTH=False)
    df = util.df(bars)
    print('reqRealTimeBars')
    display(df)
    sys.exit(0)

    func  = 'reqRealTimeBars'
    print( f'''\n{func}\n:{  util.df(ib.reqRealTimeBars(   )).head(20)};  ''')




    arint( f'''\naccountSummary\n:{  util.df(ib.accountSummary()).head(20)};  ''')

    print( f'''\nnewsBulletins\n:{  ib.newsBulletins()};  ''')
    sys.exit(0)

    '''
    def testWatchDog():
        def onConnected():
            print(ib.accountValues())

        ibc = IBC(974, gateway=True, tradingMode='paper')
        ib = IB()
        ib.connectedEvent += onConnected
        watchdog = Watchdog(ibc, ib, port=4002)
        watchdog.start()
        ib.run()
        sys.exit(0)
        pass


    testWatchDog()
    '''

    contract = Stock('ABNB')
    bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr='60 D',
            barSizeSetting='1 hour',
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1)
    df = util.df(bars)

    display(df)
    print('-'*30)

    cds  = ib.reqContractDetails(contract)
    print(cds)


    #s = ib.reqHeadTimeStamp(contract, whatToShow='TRADES', useRTH=True)
    #s = util.df(s)
    #display(s)
    sys.exit(0)
