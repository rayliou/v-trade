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

if __name__ == '__main__':
    v  = VisualizeKLine()
    v.draw()
    sys.exit(0)
