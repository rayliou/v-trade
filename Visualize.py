#!/usr/bin/env python3


'''
- https://github.com/matplotlib/mplfinance/blob/master/examples/addplot.ipynb
'''

import math
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import talib
#from scipy.stats import norm,laplace
#from scipy import stats

# This allows multiple outputs from a single jupyter notebook cell:
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"
#%matplotlib inline

from IPython.display import display, HTML
import sys



import yfinance as yf
import mplfinance as mpf
import pandas as pd
import numpy as np
import seaborn as sns
import math

def spy_iwm_cmp():
    '''
    SPY S&P 500
    IWM Russell 2000
    '''
    def logDiv(x):
        prev = (x.iloc[0])
        cur  = (x.iloc[1])
        if prev is  None :
            return None
        return math.log(cur/prev)
        #return math.log(x[0]/x[1])

    data = pd.read_csv('SPY_IWM.csv',header=[0,1,])
    sns.heatmap(data.corr()); sys.exit(0)
    sns.pairplot(data)
    #print( data.corr())
    #print(data['Date','d'])
    spy = data['ES=F','Close'].rolling(window=2,min_periods=2).apply(logDiv)
    iwm = data['IWM','Close'].rolling(window=2,min_periods=2).apply(logDiv)
    d2=pd.DataFrame()
    d2['date'] = data['Date','d']
    d2['spy_log_rate'] = spy
    d2['iwm_log_rate'] = iwm
    d2.set_index('date',inplace=True)
    print(d2)

    d2.cumsum()
    d2.plot()

class VisualizeKLine:
    def __init__(self):
        mc = mpf.make_marketcolors(up='r',down='g',
                                edge='lime',
                                wick={'up':'blue','down':'orange'},
                                volume='in',
                                ohlc='black')
        self.style_  = mpf.make_mpf_style(marketcolors=mc)
        pass
    def draw(self):
        file = 'b.data/HK.00700.K30M.csv'
        file = 'b.data/HK.01810.K30M.csv'
        df = pd.read_csv(file,index_col=0,parse_dates=True)
        display(df)
        mpf.plot(df.tail(500),type='candle',mav=(5,10,20), volume=True,style=self.style_)
        pass
    pass


#t = yf.Ticker("MSFT")
# get stock info
#t.info
# get historical market data
#hist = t.history(period="max")
#mpf.plot(hist.tail(50),type='candle',mav=(5,10,20), volume=True,style=s)
def logDiv(x):
    prev = (x.iloc[0])
    cur  = (x.iloc[1])
    if prev is  None :
        return None
    return math.log(cur/prev)
    #return math.log(x[0]/x[1])

#%matplotlib inline

def visualize_stock2option_price():
    file = 'b.data/HK.01810.K1M.csv'
    df = pd.read_csv(file,index_col=0,parse_dates=True)
    timeperiod = 14
    df['atr'] = talib.ATR(df.high,df.low,df.close,timeperiod=timeperiod)
    df['sd1'] = df.close.rolling(window=timeperiod,min_periods=timeperiod).std()
    df['sd2'] = df.close.rolling(window=timeperiod,min_periods=timeperiod).apply(np.std)

    file = 'b.data/HK.MIU210729P24000.K1M.csv'
    dfP = pd.read_csv(file,index_col=0,parse_dates=True)
    file = 'b.data/HK.MIU210729C27000.K1M.csv'
    dfC = pd.read_csv(file,index_col=0,parse_dates=True)


    # - https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
    # - https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.period_range.html

    #dates = pd.date_range('2021-07-09 9:00', '2021-07-09 17:00',freq='min')
    #print(dates)
    dfD= df['2021-07-05 00:00':'2021-07-09 16:00']
    dfP= dfP['2021-07-05 00:00':'2021-07-09 16:00']
    dfC= dfC['2021-07-05 00:00':'2021-07-09 16:00']
    #d = pd.concat([dfD, dfOD.reindex(dfD.index)], axis=1)
    # - https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html#timeseries-friendly-merging

    #d = pd.merge_asof(dfD, dfOD, right_index=True, left_index=True, suffixes=('_s','_o'))
    d = pd.merge_asof(dfP, dfC, right_index=True, left_index=True, suffixes=('_P','_C'))
    d = d[['close_P','close_C']].copy()
    d['b'] = d.close_P + d.close_C
    d = pd.merge_asof(d, dfD, right_index=True, left_index=True)
    display(d)
    #fig = plt.figure(figsize = (20,15))
    fig = plt.figure(figsize = (12,8))
    ax1 = fig.add_subplot(1,1,1)  # 创建子图1
    #d[['close_s']].plot(ax=ax1)
    #d[['close_o']].plot(ax=ax1, secondary_y=True)
    d[['b']].plot(ax=ax1)
    #d[['close']].plot(ax=ax1, secondary_y=True)
    #d[['atr','sd']].plot(ax=ax1, secondary_y=True)
    d[['sd1','sd2']].plot(ax=ax1, secondary_y=True)
    plt.grid()
    plt.show()

if __name__ == '__main__':
    visualize_stock2option_price(); sys.exit(0)
    spy_iwm_cmp(); sys.exit(0)
    v  = VisualizeKLine()
    v.draw()
    sys.exit(0)
