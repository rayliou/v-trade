#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
'''

import curses
import time
import math,sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from scipy.stats import norm
from scipy import stats
from IPython.display import display, HTML
import yfinance as yf
from Log import logInit



'''

- 1d 3d 1w 2w 1mon 2mon 4mon 0.5y 1y
    A Average
    P Parksinson1980
    G GarmaanKlass
    Y YangZhang2000
    E ewma

    1D					3D					1W					2W
avg	PK80	GK	YZ00	EWMA	avg	PK80	GK	YZ00	EWMA	avg	PK80	GK	YZ00	EWMA	avg	PK80	GK	YZ00	EWMA
FUTU
'''

class TerminalVH:
    def __init__(self):
        self.periods     = [ '1d',  '3d',  '1w',  '2w',  '1mon',  '2mon',  '4mon',  '0.5y',  '1y', ]
        self. hvAlgrithms = [ 'Average',  'Parksinson1980',  'GarmaanKlass',  'YangZhang2000',  'Ewma', ]
        self.stdscr_ = None
        
        self.symbolList = []
        pass
    def setupData(self,symbolList ):
        pass
    def updateHVR(self,period,hvFunction, symbol ):
        pass
    def show(self,stdscr):
        self.stdscr_ = stdscr
        headerPerPeriod =  '|'  + ' '.join([ a[0]  for a in self.hvAlgrithms])
        headerPerPeriod +=  ' '
        nHeaderPerPeriod =  len(headerPerPeriod)
        line = 0
        stdscr.addstr(line,0, '\t'.join([ f'{a[0]}:{a} '  for a in self.hvAlgrithms]))
        line += 1
        symbolPeriod = 'Symbol\Period'
        nSymbolPeriod = len('Symbol\Period  ')
        stdscr.addstr(line,  0, symbolPeriod)
        stdscr.addstr(line+1,0, 'Symbol\HVRatio')
        for p in range(0, len(self.periods)):
            x  = nSymbolPeriod + p *nHeaderPerPeriod
            stdscr.addstr(line,x, self.periods[p])
            stdscr.addstr(line+1,x, headerPerPeriod)
            pass
        line += 2
        stdscr.refresh()
        progress  = '-\|/'
        n = 0
        while True:
            time.sleep(1)
            stdscr.addstr(line,0, progress[n], curses.A_BOLD)
            stdscr.refresh()
            n = n + 1 if n < len(progress)-1 else 0
        stdscr.getch()
        pass

if __name__ == '__main__':
        logInit()
    #vCone = VolatilityCone('TSLA')
    #vCone = VolatilityCone('ABNB')
    code = sys.argv[1] if len(sys.argv)> 1 else 'SPY'
    isHK = code.startswith('HK.')
    #vCone = VolatilityCone(code,'1h',isHK)
    vCone = VolatilityCone(code,'5m',isHK)
    vCone.cone()
    tHV = TerminalVH()
    curses.wrapper(tHV.show)
