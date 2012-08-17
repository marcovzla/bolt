from collections import namedtuple
#from bwdb import *
import numpy as np
from uuid import uuid4
import math


def totuple(a):
    '''converts nested iterables into tuples'''
    try:
        return tuple(totuple(i) for i in a)
    except TypeError:
        return a
    
    
PhysicalObject = namedtuple('physicalObject', ['id', 'position', 'bbmin', 'bbmax'])  
ClusterParams = namedtuple("ClusterParams",['chain_distance_limit', 'angle_limit', 'min_line_length',
               'anglevar_weight', 'distvar_weight','dist_weight',
               'allow_intersection','beam_width','attempt_dnc'])
GroupAttributes = namedtuple('groupAttributes',['cost','type','density'])
successorTuple = namedtuple('successorTuple',['cost','members','uuid'])
    
    
    
def findDistance(vector1,vector2):
    '''euclidian distance between 2 points'''
    return np.round(math.sqrt(np.sum(np.square(vector2-vector1))),3) 

def findAngle(vector1, vector2):
    '''difference between two vectors, in radians'''
    preArc=np.dot(vector1, vector2) / np.linalg.norm(vector1) / np.linalg.norm(vector2)
    return np.arccos(np.round(preArc, 5))

def find_pairs(l):
    '''returns a list of all possible pairings of list elements'''
    pairs = []
    for i in range(len(l)):
        for j in range(len(l))[i + 1:]:
            pairs.append((l[i], l[j]))
    return pairs

class Bundle(object):
    def __init__(self,members,cost):
        self.members = members
        self.cost = cost
        self.cardinality = len(members)
        self.uuid = uuid4()
    def __getitem__(self,item):
        return self.members[item]
    def __iter__(self):
        for i in self.members:
            yield i
    def __str__(self):
        return 'members:'+str(members)+'cost'+str(cost)
    def __len__(self):
        return len(self.members)
        
class LineBundle(Bundle):
    def __init__(self,members,cost):
        self.bundleType='line'
        super(LineBundle,self).__init__(members,cost)
        
class SingletonBundle(Bundle):
    def __init__(self,members,cost):
        self.bundleType='singleton'
        super(SingletonBundle,self).__init__(members,cost)
        
class GroupBundle(Bundle):
    def __init__(self,members,cost):
        self.bundleType='group'
        super(GroupBundle,self).__init__(members,cost)
        

