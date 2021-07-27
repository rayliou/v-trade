#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997

'''

from IPython.display import display, HTML
from sklearn.cluster import KMeans
from sklearn.cluster import SpectralClustering

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, HTML
import json,sys
from datetime import datetime
#from sklearn.metrics import calinski_harabaz_score
'''
- https://scikit-learn.org/stable/modules/clustering.html#clustering-evaluation
'''
from sklearn.metrics import davies_bouldin_score,calinski_harabasz_score,silhouette_score

class CorrelationTopN:
    '''
    uncorrelatable or not
    '''
    def __init__(self,topN=10, csvFile='./optionHK_securities_1h.csv'):
        self.topN_ = topN
        df = pd.read_csv(csvFile,index_col=0,parse_dates=True)
        df = df[ '2021-01-01 10:30:00':]
        self.df_ = pd.DataFrame()
        rowLabeels = [c[len('open_'):] for c in df.columns.values if c.startswith('open_') ]
        self.rowLabeels_ = rowLabeels
        for r in rowLabeels:
            m = (df[f'open_{r}'] + df[f'high_{r}'] + df[f'low_{r}']+ df[f'close_{r}'])/4
            m = np.log(m/m.shift())
            m[np.isinf(m)] = np.nan
            m = m.fillna(0)
            if m.isnull().any() or np.isinf(m).any()  :
                print(m.T)
            self.df_[r] =m
        pass
    def corr(self,uncorrelatable=False):
        ret  = dict()
        corrABS = self.df_.corr().abs()  if   uncorrelatable else self.df_.corr().abs() * -1
        for c in corrABS:
            indexes = corrABS[c].argsort().iloc[:self.topN_]
            ret[c] = [i for i in corrABS[c].iloc[indexes].index]
        ret  = json.dumps(ret)
        print(ret)
    pass

def cluster(n_clusters = 7,gamma=1.):

    df = pd.read_csv('./optionHK_securities_1h.csv',index_col=0,parse_dates=True)
    #df = df[ '2021-07-07 10:30:00':]
    df = df[ '2021-01-01 10:30:00':]

    rowLabeels = [c[len('open_'):] for c in df.columns.values if c.startswith('open_') ]
    #print(rowLabeels)
    samples = []
    for r in rowLabeels:
        sdict = dict()
        for d in ['open', 'high', 'low', 'close', 'volume']:
            s = df[f'{d}_{r}']
            s = np.log(s/s.shift())
            s[np.isinf(s)] = np.nan
            s = s.fillna(0)
            if s.isnull().any() or np.isinf(s).any()  :
                print(s.T)
            sdict[d] = s
        #features = np.concatenate((sdict['open'],sdict['high'],sdict['low'],sdict['close'],sdict['volume'],)  )
        features = np.concatenate((sdict['open'],sdict['high'],sdict['low'],sdict['close'],)  )
        samples.append(features)

    samples = np.array(samples)
    #print(samples.shape)
    #display(samples)

    #cluster = KMeans(n_clusters=n_clusters, random_state=0).fit(samples)
    cluster = SpectralClustering(n_clusters=n_clusters, gamma=gamma).fit(samples)

    #重要属性labels_，查看聚好的类别，每个样本所对应的类
    y_pred = cluster.labels_
    _silhouette_score = silhouette_score(samples, y_pred, metric='euclidean')
    _davies_bouldin_score = davies_bouldin_score(samples, y_pred)
    _calinski_harabasz_score = calinski_harabasz_score(samples, y_pred)


    #display(y_pred)
    #centroid = cluster.cluster_centers_
    #centroid
    #centroid.shape
    clusterDict = dict()
    clusterNumDict = dict()


    for i in range(len(y_pred)):
        c = str(y_pred[i])
        l = rowLabeels[i]
        if c not in clusterDict:
            clusterDict[c] = []
        clusterDict[c].append(l)
    for k,v in clusterDict.items():
        v.sort()

    for k,v in clusterDict.items():
        clusterNumDict[len(v)] = k
    #print(clusterNumDict)
    ks = [k for k in clusterNumDict.keys() ]
    ks.sort(reverse=True)
    return clusterDict,ks, _silhouette_score, _davies_bouldin_score, _calinski_harabasz_score

def bestClustNum():
    ret = []
    silhouette_score = []
    davies_bouldin_score = []
    calinski_harabasz_score = []
    ks_ratio = []
    df  = pd.DataFrame()
    kRange  = range(2,25)
    for n in kRange:
        clusterDict,ks, _silhouette_score, _davies_bouldin_score, _calinski_harabasz_score = cluster(n)
        silhouette_score.append(_silhouette_score)
        davies_bouldin_score.append(_davies_bouldin_score)
        calinski_harabasz_score.append(_calinski_harabasz_score)
        minNum = 4 if len(ks) >=5 else len(ks) -1
        ratio = ks[0]/ks[minNum]
        ks_ratio.append(ratio)
        s = f'{n}:{ratio}'
        ret.append(s)
    ret  = '\n'.join(ret)
    print(ret)
    #df['silhouette_score'] = silhouette_score
    df['davies_bouldin_score'] = davies_bouldin_score
    df['calinski_harabasz_score'] = calinski_harabasz_score
    df['ks_ratio'] = ks_ratio
    df.index = kRange

    fig = plt.figure(figsize = (12,8))
    ax = fig.add_subplot(111)
    df[['davies_bouldin_score','calinski_harabasz_score' ]].plot(ax=ax)
    df[["ks_ratio"]].plot(ax=ax,secondary_y=True)

    #df.plot(ax=ax)
    plt.show()
    sys.exit(0)
    pass


if __name__ == '__main__':
    corrTopN = CorrelationTopN()
    corrTopN.corr();sys.exit(0)
    #bestClustNum()
    # 8, 15
    num = 15 if len(sys.argv) <=1 else int(sys.argv[1])

    clusterDict,ks, _silhouette_score, _davies_bouldin_score, _calinski_harabasz_score  = cluster(num)
    print(json.dumps(clusterDict))
    pass


