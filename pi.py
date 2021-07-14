#!/usr/bin/env python3
# coding=utf-8
import re
from futu import *
from IPython.display import display, HTML
import random as rn
import numpy as np
import scipy.stats as st
import matplotlib.pyplot as plt


'''
- https://docs.scipy.org/doc/scipy/tutorial/index.html
-
'''



if __name__ == '__main__':
    rng = np.random.default_rng()
    N = 50000000
    r = rng.random((N,2))
    f = (r[:,0] - 0.5) ** 2 + (r[:,1] - 0.5) ** 2
    f = np.where(f <= 0.25, 1,0)
    cnt = (f.sum())
    pi = 1.0 * cnt /N /0.25
    print(pi)
    sys.exit(0)
