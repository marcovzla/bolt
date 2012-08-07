'''
Created on Jul 5, 2012

@author: colinwinslow
'''
print __doc__

import numpy as np

from scipy.spatial import distance
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.datasets.samples_generator import make_blobs


def clustercost(data):
    #    data is a tuple of two dictionaries: core cluster data first, then fringe data second\
    # this func needs to return a unified list of possible clusters using both dictionaries in the style of the chain finder function
    # quick and dirty:
    output = []
    for i in data[0].viewvalues():
        output.append((len(i)*.8,i,'group'))
    return output
    
def dbscan(data):
    X,ids = zip(*data)
    D = distance.squareform(distance.pdist(X))
    S = 1 - (D / np.max(D))
    db = DBSCAN(min_samples=4).fit(S)
    core_samples = db.core_sample_indices_
    labels = db.labels_
    clusterlist = zip(labels, ids)
    shortclusterlist = zip(labels,ids)
    
    fringedict = dict()
    coredict = dict()
    
    for i in core_samples:
        ikey = int(clusterlist[i][0])
        ival = clusterlist[i][1]
        try:
            coredict[ikey].append(ival)
        except:
            coredict[ikey]=[]
            coredict[ikey].append(ival)
        shortclusterlist.remove(clusterlist[i])
    
    for i in shortclusterlist:
        try:
            fringedict[int(i[0])].append(i[1])
        except:
            fringedict[int(i[0])]=[]
            fringedict[int(i[0])].append(i[1])
    
    return (coredict,fringedict)