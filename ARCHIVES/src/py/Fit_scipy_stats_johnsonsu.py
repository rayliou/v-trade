#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997
'''

import math,sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from scipy.stats import norm,laplace,johnsonsb,johnsonsu
from scipy import stats
from IPython.display import display, HTML

#%matplotlib inline

def logDiv(x):
    prev = (x.iloc[0])
    cur  = (x.iloc[1])
    if prev is  None :
        return None
    return cur/prev
    return math.log(cur/prev)
    #return math.log(x[0]/x[1])


file = 'b.data/HK.01810.K30M.csv'
df = pd.read_csv(file,index_col=0,parse_dates=True)
m = (df.high + df.low)/2
m = m.fillna(m.mean())

r = m.shift(-1)/m

u = r.mean()
std = r.std()
r = r.fillna(u)
returnLog = np.log(r)



df1 = df[['high'] ].copy()

df1['m'] = m
df1['r'] = r
df1['rLog'] = returnLog
display(df1)
#r = returnLog


#rv = norm.rvs(u,std,size=1000)
#x = np.linspace(laplace.ppf(0.001,uL,stdL), laplace.ppf(0.999,uL,stdL), 1000)
x = np.linspace(r.values.min(),r.values.max() ,1000)
uN, stdN = norm.fit(r.values, loc=0.3, scale=0.2)
uL, stdL = laplace.fit(r.values, loc=0.3, scale=0.2)
#aJSB, bJSB = johnsonsb.fit(r.values)
jSB= johnsonsb.fit(r.values)
jSU= johnsonsu.fit(r.values)

'''输出结果中第一个为统计量，第二个为P值（注：统计量越接近0就越表明数据和标准正态分布拟合的越好，
如果P值大于显著性水平，通常是0.05，接受原假设，则判断样本的总体服从正态分布）'''
print('do johnsonsu test')
print(stats.kstest(r.values, 'johnsonsu',(jSU[0],jSU[1],jSU[2],jSU[3])))

print('do laplace test')
print(stats.kstest(r.values, 'laplace'),(uL,stdL))

sys.exit(0)

print(f'uL={uL} ,stdL={stdL}  uN/u={uN}/{u} ,stdN/std={stdN}/{std}')
df3 = pd.DataFrame({
            'yL': laplace.pdf(x, loc=uL,scale=stdL)
            #,yN': norm.pdf(x, loc=uN,scale=stdN)
            #,'yJSB': johnsonsb.pdf(x, jSB[0],jSB[1],jSB[2],jSB[3])
            ,'yJSU': johnsonsu.pdf(x, jSU[0],jSU[1],jSU[2],jSU[3])
            }, index=x )
display(df3)


rs = df1
plt.rcParams['font.size'] = 14
ex = 'r'
g = (rs
        .pipe(sns.FacetGrid, height=5,aspect=1.5)
        .map(sns.distplot,ex,   kde=False, fit=stats.norm,
            fit_kws={ 'lw':2.5, 'color':'red','label':'Norm'})
        .map(sns.distplot,  ex, kde=False, fit=stats.laplace,
            fit_kws={'linestyle':'--','color':'blue', 'lw':2.5, 'label':'Laplace'})
        .map(sns.distplot, ex,  kde=False, fit=stats.johnsonsu,
            fit_kws={'linestyle':'-','color':'black','lw':2.5, 'label':'Johnson'})
    )

g.add_legend()
sns.despine(offset=1)
plt.title(f'{ex}收益率',size=15)





#returnLog = m.rolling(window=2,min_periods=2).apply(logDiv)
print(r)
a = r.tail(5000).values

fig = plt.figure(figsize = (12,8))
ax1 = fig.add_subplot(2,1,1)  # 创建子图1
ax1.scatter(r.index, r.values)
plt.grid()

ax2 = fig.add_subplot(2,1,2)  # 创建子图2
r.hist(bins=30,alpha = 0.5,ax = ax2)
#r.plot(kind = 'kde', secondary_y=True,ax = ax2)
df3.plot(ax=ax2, secondary_y=True)

#ax3 = ax2.twinx()
#ax3.plot(x,y, 'b-', lw=2, alpha=0.6, label='laplace pdf')
#ax3.plot(x,yN, 'r-', lw=2, alpha=0.6, label='norm pdf')

plt.grid()
plt.show()


'''输出结果中第一个为统计量，第二个为P值（统计量越接近1越表明数据和正态分布拟合的好，
P值大于指定的显著性水平，接受原假设，认为样本来自服从正态分布的总体）'''
print(stats.shapiro(a))

'''输出结果中第一个为统计量，第二个为P值（注：统计量越接近0就越表明数据和标准正态分布拟合的越好，
如果P值大于显著性水平，通常是0.05，接受原假设，则判断样本的总体服从正态分布）'''
print(stats.kstest(a, 'norm'),(u,std))

'''输出结果中第一个为统计量，第二个为P值（注：p值大于显著性水平0.05，认为样本数据符合正态分布）'''
print(stats.normaltest(a))
