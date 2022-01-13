#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
statsmodels包含更多的“经典”频率学派统计方法，而贝叶斯方法和机器学习模型可在其他库中找到。

'''

#from scipy.stats import pearsonr, spearmanr
from statsmodels.tsa.stattools import coint
#from statsmodels.tsa.stattools import adfuller

import pandas as pd
import numpy as np
from IPython.display import display, HTML
from datetime import datetime, timedelta
import sys,time,inspect,os
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, f'../{parentdir}')
sys.path.insert(0, parentdir)
from Log import logInit
from pyhocon import ConfigFactory
import hashlib,json
import click,logging

log = logging.getLogger('main.BigPandasTable')

def load_merged_data(file = 'data.cn/20211222.csvx'):
    global log
    msg  = f'pd.read_csv({file}, index_col=0, header=[0,1], parse_dates=True )'
    log.debug(msg)
    df  = pd.read_csv(file, index_col=0, header=[0,1], parse_dates=True )
    df = df[ ~ df.isna().any(axis=1)]
    symbols = list(set([c[0] for c in df.columns]))
    return df,symbols


if __name__ == '__main__':
    sys.exit(0)

