#!/usr/bin/env python3


'''
- https://github.com/matplotlib/mplfinance/blob/master/examples/addplot.ipynb
'''

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

if __name__ == '__main__':
    spy_iwm_cmp(); sys.exit(0)
    v  = VisualizeKLine()
    v.draw()
    sys.exit(0)
