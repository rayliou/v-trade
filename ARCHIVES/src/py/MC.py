#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML
import random as rn
import numpy as np
import scipy.stats as st
import matplotlib.pyplot as plt



if __name__ == '__main__':
    h = [f for f in dir(rn) if f.endswith('variate')]
    fig, ax = plt.subplots(1, 1)
    rv = st.norm(1, scale=2.)
    rv = st. norminvgauss(2,1)
    mean, var, skew, kurt = rv.stats(moments='mvsk')
    #percent point function
    x = np.linspace(rv.ppf(0.001),
                rv.ppf(0.999), 1000)
    ax.plot(x, rv.pdf(x),
       'r-', lw=5, alpha=0.6, label='norm pdf')

    ax.plot(x, rv.cdf(x), 'k-', lw=1, label='frozen cdf')
    ax.plot(x, rv.pdf(x), 'k-', lw=2, label='frozen pdf')
    vals = rv.ppf([0.001, 0.5, 0.999])
    np.allclose([0.001, 0.5, 0.999], rv.cdf(vals))
    r = rv.rvs(size=10000)
    ax.hist(r, density=True, histtype='stepfilled', alpha=0.2)
    ax.legend(loc='best', frameon=False)
    plt.show()



    #print(h)
    #help(np.random)
