#!/usr/bin/env python3


'''
- https://github.com/matplotlib/mplfinance/blob/master/examples/addplot.ipynb
'''

# This allows multiple outputs from a single jupyter notebook cell:
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"
#%matplotlib inline



import yfinance as yf
import mplfinance as mpf

mc = mpf.make_marketcolors(up='r',down='g',
                           edge='lime',
                           wick={'up':'blue','down':'orange'},
                           volume='in',
                           ohlc='black')
s  = mpf.make_mpf_style(marketcolors=mc)


t = yf.Ticker("MSFT")
# get stock info
#t.info
# get historical market data
hist = t.history(period="max")
mpf.plot(hist.tail(50),type='candle',mav=(5,10,20), volume=True,style=s)

if __name__ == '__main__':
    sys.exit(0)
