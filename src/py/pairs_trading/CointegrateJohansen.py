#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
statsmodels包含更多的“经典”频率学派统计方法，而贝叶斯方法和机器学习模型可在其他库中找到。

'''
import pandas as pd
import numpy as np
from IPython.display import display, HTML
from datetime import datetime, timedelta

MIN_DAYS = 14
MAX_TIMES = 3
#MIN_DAYS = 5
#MAX_TIMES = 10
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from statsmodels.tsa.stattools import coint
from scipy import stats
import time,click
import matplotlib.pyplot as plt


import sys,logging,json
pyRoot = "/Users/henry/stock/v-trade/src/py"
sys.path.insert(0,pyRoot)
from Log import logInit
log = logging.getLogger("main")

def get_hurst_exponent(time_series, max_lag=20):
    """
    https://www.analyticsvidhya.com/blog/2021/06/using-hurst-exponent-to-analyse-the-stock-and-crypto-market-with-python/
    Returns the Hurst Exponent of the time series
    """
    lags = range(2, max_lag)
    # variances of the lagged differences
    tau = [np.std(np.subtract(time_series[lag:], time_series[:-lag])) for lag in lags]
    # calculate the slope of the log plot -> the Hurst Exponent
    reg = np.polyfit(np.log(lags), np.log(tau), 1)
    return reg[0]

def getHalflife(s):
    s_lag = s.shift(1)
    s_lag.iloc[0] = s_lag.iloc[1]
    s_ret = s - s_lag
    s_ret.iloc[0] = s_ret.iloc[1]
#     s_lag2 = sm.add_constant(s_lag)
#     model = sm.OLS(s_ret,s_lag2)
#     res = model.fit()
#     # print(res.summary())
#     halflife = round(-np.log(2) / list(res.params)[1],0)
    res = stats.linregress(s_lag, s_ret)
    halflife = round(-np.log(2) /res.slope,2)
    return halflife




def get_johansen(y, p):
    """
    https://nbviewer.org/github/mapsa/seminario-doc-2014/blob/master/cointegration-example.ipynb
    Get the cointegration vectors at 95% level of significance
    given by the trace statistic test.
    """
    N, l = y.shape
    jres = coint_johansen(y, 0, p)
    trstat = jres.lr1                       # trace statistic
    tsignf = jres.cvt                       # critical values
    r = 0
    for i in range(l):
        if trstat[i] > tsignf[i, 1]:     # 0: 90%  1:95% 2: 99%
            r = i + 1
    jres.r = r
    jres.evecr = jres.evec[:, :r]
    return jres

def plotReverse(X0,Y0, c):
    X = X0
    Y = Y0
    #start = X0.index[-1] - timedelta(days=14)
    #X0 = X0[start:]
    #Y0 = Y0[start:]
    interval = (X0.index[1] -X0.index[0]).total_seconds()
    fig = plt.figure(figsize = (20,16))
    ax = fig.add_subplot(111)
    cnt = 0
    df = pd.DataFrame()
    def calDiffStd(slope,name=""):
        nonlocal cnt
        nonlocal df
        diff = (Y -  slope *X)
        if df is None:
            df = pd.DataFrame({name: diff})
        else:
            df[name] = diff
        intercept = diff.mean()
        df[name] -= intercept
        std = diff.std()
        return intercept, std

    #plot_ols(c['beta'], None, "JS_coint")
    o = c['ols_by_coint_days']
    #calDiffStd(o['lr_xy_s'], None, "ols_by_coint_days_lr_xy")
    #calDiffStd(o['fast_s'],  "ols_by_coint_days_fast")
    o = c['ols_by_halflife']
    #calDiffStd(o['lr_xy_s'], None, "ols_by_halflife_lr_xy")
    #calDiffStd(o['fast_s'],  "ols_by_halflife_fast")
    i,s = calDiffStd( 0.5* (c['ols_by_coint_days']['lr_xy_s'] + c['ols_by_halflife']['lr_xy_s']), "ols_by_halflife& coint")
    df.plot(ax=ax)
    ax.axhline(s*2, color='r', linestyle='--', label= f'2std')
    ax.axhline(0, color='g', linestyle='--', label= f'2std')
    ax.axhline(-s*2, color='r', linestyle='--', label= f'-2std')

    plt.legend()
    plt.show()
    pass


def plot(X0,Y0, c):
    """
    {'beta': 0.5340465255023173, 'coint_days': 42, 'he_0': 0.5120089729967078,
    'hl_bars_0': 1197.57,
    'ols_by_coint_days': {'he': 0.5120089729967078, 'hl_bars': 1197.57, 'lr_xy_s': 0.4244194185703321, 'lr_xy_i': 91.80953271820749,
        'fast_s': 1.6932738247863868, 'fast_i': 0.4096130060590514, 'start': Timestamp('2021-12-02 15:59:00'), 'end': Timestamp('2022-01-13 15:59:00')},
    'ols_by_halflife': {'he': 0.5294817132023034, 'hl_bars': 329.83, 'lr_xy_s': 0.6585682048356386, 'lr_xy_i': 84.58765252433656,
        'fast_s': 1.7897907639947161, 'fast_i': 0.072324905537769, 'start': Timestamp('2022-01-10 15:32:00'), 'end': Timestamp('2022-01-13 15:59:00')}}

    """
    X = X0
    Y = Y0
    #start = X0.index[-1] - timedelta(days=14)
    #X0 = X0[start:]
    #Y0 = Y0[start:]
    interval = (X0.index[1] -X0.index[0]).total_seconds()
    #print(interval.total_seconds())
    #https://chris35wills.github.io/courses/PythonPackages_matplotlib/matplotlib_scatter/
    fig = plt.figure(figsize = (20,16))
    ax = fig.add_subplot(111)
    cbData = X0.index - X0.index[0]
    cbData = cbData.total_seconds()/3600
    #display(cbData)
    s = ax.scatter(X0,Y0,c=cbData)
    cb = fig.colorbar(s,ax=ax)
    cb.set_label("base hours")
    #https://www.w3schools.com/python/matplotlib_markers.asp
    colors = "rgbcmyk"
    cnt = 0
    def plot_ols(slope, intercept = None, name=""):
        nonlocal cnt;
        if intercept is None:
            diff = (Y -  slope *X)
            intercept = diff.mean()
            std = diff.std()
        Y1 = slope *X + intercept
        ax.plot(X,Y1, f"{colors[cnt]}-", label=f"name:{name},beta:{slope}")
        ax.plot(X,Y1-2*std, f"{colors[cnt]}--", label=f"2std-:name:{name},beta:{slope}")
        ax.plot(X,Y1+2*std, f"{colors[cnt]}--", label=f"2std+:name:{name},beta:{slope}")

        cnt +=1
        return

    #plot_ols(c['beta'], None, "JS_coint")
    o = c['ols_by_coint_days']
    #plot_ols(o['lr_xy_s'], None, "ols_by_coint_days_lr_xy")
    plot_ols(o['fast_s'], None, "ols_by_coint_days_fast")
    o = c['ols_by_halflife']
    #plot_ols(o['lr_xy_s'], None, "ols_by_halflife_lr_xy")
    plot_ols(o['fast_s'], None, "ols_by_halflife_fast")

    plt.legend()
    plt.show()

def _ols(X,Y):
    #Fast
    b = (X*Y).sum()/(X*X).sum()
    i = (Y-X*b).mean()
    #REG

    res2 = stats.linregress(X,Y)
    diff = X*res2.slope + res2.intercept - Y
    he = get_hurst_exponent(diff.values)
    hl = getHalflife(diff)
    o = {"he":he,"hl_bars":hl,'lr_xy_s':res2.slope, 'lr_xy_i':res2.intercept,'lr_xy_std': diff.std()
         , 'fast_s': b , "fast_i":i,'start': X.index[0], 'end': X.index[-1],}
    return o

def cointegrate(v, thresholdHE, thresholdHalflifeHrs):
    '''
     ['s_0', 's_coint_days_lrxy', 's_coint_days_fast', 's_halflife_0_lrxy', 's_halflife_0_fast']:
    '''
    X0,Y0 = v['xm'],v['ym'] # x,y of model
    if X0.iloc[-1] < 5.0 or Y0.iloc[-1] < 5.0:
        return None
    data = pd.DataFrame({"x":X0, "y":Y0 })
    oList = []
    interval = (X0.index[1] -X0.index[0]).total_seconds()
    for dTimes in range(1,MAX_TIMES+1):
        days = MIN_DAYS * dTimes
        start = X0.index[-1] - timedelta(days=days)
        #print(f"dTime:{dTimes},days:{days},start:{start}")
        d = data[start:]
        #display(d[d.isna().any(axis=1)])
        #log.debug(f'{v["n1"]}_{v["n2"]}')
        jres= get_johansen(d,1)
        #print(f"There are {jres.r} coint")
        if jres.r >0 :
            beta = jres.evecr[0,0]/jres.evecr[1,0]
            o = {'days' :days, 'lambda_0': jres.eig[0], "beta": beta, 'c0': jres.evecr[0,0], "c1": jres.evecr[1,0], 'lambda_1': jres.eig[1],}
            #_, pxy, _ = coint(d.x, d.y)
            #_, pyx, _ = coint(d.y,d.x)
            #o.update({'pxy': pxy, "pyx":pyx})
            o.update({'start':d.index[0], 'end': d.index[-1]})
            oList.append(o)
    if len(oList) == 0:
        return None
    dfO = pd.DataFrame(oList)
    dfO= dfO.sort_values(by='lambda_0',ascending=False)
    #log.debug(dfO)
    beta,days = -1*dfO.iloc[0].beta, int(dfO.iloc[0].days)

    start = X0.index[-1] - timedelta(days=days)
    #bars = int(days * 6.5 * 3600/interval)
    X = X0[start:]
    Y = Y0[start:]
    oOLS_0=  _ols(X,Y)
    std_rate_xy = oOLS_0['lr_xy_std']/(X.iloc[-1] * oOLS_0['lr_xy_s']+Y.iloc[-1])
    he = oOLS_0['he']
    if he > thresholdHE:
        return None
    hlBars = oOLS_0['hl_bars']
    hlHrs  = (hlBars *interval)/3600.
    if hlHrs > thresholdHalflifeHrs:
        return None
    #log.debug(f'Half life:{hlHrs} hrs , HE:{he}')
    X = X0.iloc[-round(hlBars):]
    Y = Y0.iloc[-round(hlBars):]
    oOLS_1 =  _ols(X,Y)
    c= {'pair': f"{v['n1']}_{v['n2']}",
       's_0':beta,
        's_dayslr': oOLS_0['lr_xy_s'] ,
        's_daysfast': oOLS_0['fast_s'],
        's_hllr': oOLS_1['lr_xy_s'],
        's_hlfast': oOLS_1['fast_s'],
        'std_rate':std_rate_xy * 100,
        'coint_days':days, "interval_secs": interval, "he_0":he,"hl_bars_0":hlBars,
        'start': dfO.iloc[0].start,
        'end': dfO.iloc[0].end,
    }
    ok = True
    for k,v in c.items():
        #all slope should be gt 0.01
        if k.startswith('s_') and v < 0.01:
            ok  = False
            break
        pass
    return c if ok else None

#################################


def ols(X0, Y0,beta,coint_days):
    oList = []
    #print(f"coint_days:{coint_days},he:{he},hl(mins):{hl}")
    #mean = diff.mean()
    #print(f', {X}')
    for winHrs in range(40*24, 0, -3): #from 3 hrs to 5 days.
        days = winHrs /24.
        bars = int(winHrs * 3600 /interval)
        X = X0.iloc[-bars:]
        Y = Y0.iloc[-bars:]
        #print(f'{bars},{X.index[0]}')
        o = {'days': days,"win_hrs":winHrs,}
        o.update( _ols(X,Y))
        oList.append(o)

    dfO = pd.DataFrame(oList)
    dfO= dfO.sort_values(by='days')
    dfO.set_index('days', inplace=True)
    fig = plt.figure(figsize = (20,16))
    ax = fig.add_subplot(111)
    #dfO[['fast','x~y', '1/(y~x)' ]] [dfO.index >5].plot(ax=ax)
    dfO[['fast','x~y',]].plot(ax=ax)
    dfO[['he']].plot(ax=ax, secondary_y=True)
    ax.axhline(beta, color='r', linestyle='--', label= f'beta 0')
    #plt.legend()
    plt.show()
    display(dfO)


def splitData(dfSrc,n1,n2, modelTime):
    X0 = dfSrc[n1].close
    Y0 = dfSrc[n2].close
    Xm = X0[:modelTime]
    Ym = Y0[:modelTime]
    #bt data, netxt 3 days.
    days =  1.5
    interval = (X0.index[1] -X0.index[0]).total_seconds()
    bars = int(days *6.5 * 3600/interval)
    df = dfSrc[modelTime:].iloc[0:bars]
    Xbt = df[n1].close
    Ybt = df[n2].close
    o = {
        'x0': X0, 'y0':Y0,
        'xm': Xm, 'ym':Ym,
        'xbt': Xbt, 'ybt':Ybt,
        'n1':n1, 'n2': n2,
        'modelTime':modelTime,
    }
    return o

def _js_coint(src, dst, modelTime,thresholdHE, thresholdHalflifeHrs):
    logInit()
    dfSrc  = pd.read_csv(src, index_col=0, header=[0,1], parse_dates=True )
    symbolsSrc = list(set([c[0] for c in dfSrc.columns]))
    ignored = ['RIVN',]
    for s in ignored:
        symbolsSrc.remove(s)
    #modelTime = '2021-12-18'
    #modelTime = '2022-1-27'
    N = len(symbolsSrc)
    P = np.zeros((N,N))
    P  = pd.DataFrame(P)
    P.index = P.columns = symbolsSrc
    #loop
    cnt,cntOk  = 0,0
    totalCnt =  int(N *(N-1) /2)
    cList = []
    for i in range(N):
        for j in range(i+1,N):
            cnt += 1
            k1 = symbolsSrc[i]
            k2 = symbolsSrc[j]
            #v = {'pair': f'{k1}_{k2}', }
            v = splitData(dfSrc,k1,k2,modelTime)
            tm0 = time.time()
            c = cointegrate(v, thresholdHE, thresholdHalflifeHrs)
            if c is None:
                continue
            tm1 = time.time()
            cList.append(c)
            #print(f"time of cointegrate:{tm1-tm0} secs ")
            cntOk +=1
            log.debug(f'[{modelTime}]:[{totalCnt}/{cnt}/{cntOk}]:\t{c}')
            #json.dump(c,sys.stdout)
    df = pd.DataFrame(cList).sort_values(by='he_0')
    print("")
    #https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_json.html
    df.to_json(dst,orient="records",double_precision=5,lines=True)
    log.warning(f"Wrote {dst}")
    pass

@click.command()
@click.argument('bigcsv')
@click.argument('dst')
@click.option('--model_time',  help='')
@click.option('--thrshld_he',  help='',default=0.49)
@click.option('--thrshld__halflife_hrs',  help='',default=6.5)
def js_coint(bigcsv, dst, model_time,thrshld_he, thrshld__halflife_hrs):
    _js_coint(bigcsv, dst, model_time,thrshld_he, thrshld__halflife_hrs)
    pass


@click.group()
def cli():
    pass


if __name__ == '__main__':

    cli.add_command(js_coint)
    cli(); sys.exit(0)

