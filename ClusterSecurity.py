#!/usr/bin/env python3
# coding=utf-8
'''
- https://docs.scipy.org/doc/scipy/reference/reference/generated/scipy.stats.johnsonsu.html#scipy.stats.johnsonsu
- https://zhuanlan.zhihu.com/p/26869997



7:5.444444444444445
10:2.1578947368421053
12:4.2727272727272725
13:6.875
14:4.357142857142857
15:3.5454545454545454
16:2.0

17:2.0



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
    #bestClustNum()
    # 8, 15
    num = 15 if len(sys.argv) <=1 else int(sys.argv[1])

    clusterDict,ks, _silhouette_score, _davies_bouldin_score, _calinski_harabasz_score  = cluster(num)
    print(json.dumps(clusterDict))
    pass


