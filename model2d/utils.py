#!/usr/bin/env python

from __future__ import division

import sys
import random
from functools import partial
import inspect

import numpy as np
from planar import Vec2, BoundingBox

# import stuff from table2d
sys.path.append('..')
from table2d.speaker import Speaker
from table2d.landmark import RectangleRepresentation, Scene, Landmark, PointRepresentation, ObjectClass
from table2d.relation import OrientationRelationSet
from table2d.run import construct_training_scene

NONTERMINALS = ('LOCATION-PHRASE', 'RELATION', 'LANDMARK-PHRASE', 'LANDMARK')

def get_lmk_ori_rels_str(lmk):
    return ( ','.join([rel.__name__ if rel in lmk.ori_relations else '' for rel in OrientationRelationSet.relations]) ) if lmk else None

def parent_landmark(lmk):
    """gets a landmark and returns its parent landmark
    or None if it doesn't have one"""
    if lmk:
        parent = lmk.parent
        if parent and not isinstance(parent, Landmark):
            parent = parent.parent_landmark
        return parent

def count_lmk_phrases(t):
    """gets an nltk Tree and returns the number of LANDMARK-PHRASE nodes"""
    return sum(1 for n in t.subtrees() if n.node == 'LANDMARK-PHRASE')



# a wrapper for a table2d scene
class ModelScene(object):
    def __init__(self, scene=None, speaker=None):
        self.scene = scene
        if scene is None:
            self.scene = Scene(3)

            # not a very furnished scene, we only have one table
            table = Landmark('table',
                             RectangleRepresentation(rect=BoundingBox([Vec2(5,5), Vec2(6,7)])),
                             None,
                             ObjectClass.TABLE)

            self.scene.add_landmark(table)
            self.table = table

        self.table = self.scene.landmarks['table']

        # there is a person standing at this location
        # he will be our reference
        if speaker is None:
            self.speaker = Speaker(Vec2(5.5, 4.5))
        else:
            self.speaker = speaker

        # NOTE we need to keep around the list of landmarks so that we can
        # access them by id, which is the index of the landmark in this list
        # collect all possible landmarks
        self.landmarks = []
        for scene_lmk in self.scene.landmarks.itervalues():
            self.landmarks.append(scene_lmk)

            # a scene can be represented as a plane, line, etc
            # each representation of a scene has different landmarks
            rs = [scene_lmk.representation]
            rs.extend(scene_lmk.representation.get_alt_representations())

            for r in rs:
                for lmk in r.get_landmarks():
                    self.landmarks.append(lmk)

        # FIXME we are using sentences with 1 or 2 LANDMARK-PHRASEs
        # so we need to restrict the landmarks to 0 or 1 ancestors
        self.landmarks = [l for l in self.landmarks if l.get_ancestor_count() < 2]

    def get_rand_loc(self):
        """returns a random location on the table"""
        bb = self.table.representation.get_geometry()
        xmin, ymin = bb.min_point
        xmax, ymax = bb.max_point
        return random.uniform(xmin, xmax), random.uniform(ymin, ymax)

    def get_landmark_id(self, lmk):
        return self.landmarks.index(lmk)

    def get_landmark_by_id(self, lmk_id):
        return self.landmarks[lmk_id]

    def sample_lmk_rel(self, loc, num_ancestors=None):
        """gets a location and returns a landmark and a relation
        that can be used to describe the given location"""
        landmarks = self.landmarks

        if num_ancestors is not None:
            landmarks = [l for l in landmarks if l.get_ancestor_count() == num_ancestors]

        loc = Landmark(None, PointRepresentation(loc), None, None)
        lmk, lmk_prob, lmk_entropy, head_on = self.speaker.sample_landmark( landmarks, loc )
        rel, rel_prob, rel_entropy = self.speaker.sample_relation(loc, self.table.representation.get_geometry(), head_on, lmk, step=0.5)
        rel = rel(head_on,lmk,loc)

        return (lmk, lmk_prob, lmk_entropy), (rel, rel_prob, rel_entropy)


# we will use this instance of the scene
scene = ModelScene( *construct_training_scene() )



# helper functions
def lmk_id(lmk):
    if lmk: return scene.get_landmark_id(lmk)

def rel_type(rel):
    if rel: return rel.__class__.__name__

def get_meaning(loc=None, num_ancestors=None):
    if not loc:
        loc = scene.get_rand_loc()

    lmk, rel = scene.sample_lmk_rel(Vec2(*loc), num_ancestors)
    # print 'landmark: %s (%s)' % (lmk, lmk_id(lmk))
    # print 'relation:', rel_type(rel)
    return lmk, rel

def m2s(lmk, rel):
    """returns a string that describes the gives landmark and relation"""
    return '<lmk=%s(%s, %s), rel=%s(%s,%s)>' % (repr(lmk), lmk_id(lmk), lmk.object_class if lmk else None, rel_type(rel),
                                                rel.measurement.best_degree_class if hasattr(rel,'measurement') else None,
                                                rel.measurement.best_distance_class if hasattr(rel,'measurement') else None)




def categorical_sample(values, probs):
    probs = np.array(probs)
    index = np.random.multinomial(1, probs).nonzero()[0][0]
    value = values[index]
    return value, probs[index], -np.sum( (probs * np.log(probs)) )



# based on matlab's mvnpdf
def mvnpdf(x, mu=0, sigma=None):
    """multivariate normal probability density function"""

    # number of elements in `x`
    k = len(x)

    # `x` must be a numpy array
    if not isinstance(x, np.ndarray):
        x = np.array(x)

    # if `mu` is a scalar value then convert it into a numpy array
    # with the scalar value repeated `k` times
    if isinstance(mu, (int, float)):
        mu *= np.ones(k)

    # `mu` must be a numpy array
    elif not isinstance(mu, np.ndarray):
        mu = np.array(mu)

    # if `sigma` is unspecified then create a k*k identity matrix
    if sigma is None:
        sigma = np.identity(k)

    # make sure `sigma` is a numpy array
    elif not isinstance(sigma, np.ndarray):
        sigma = np.array(sigma)

    # if `sigma` is a 1d array then convert it into a matrix
    # with the vector in the diagonal
    if sigma.ndim == 1:
        sigma = np.diag(sigma)

    # difference between `x` and the mean
    diff = x - mu

    # calculate probability density
    pd = (2*np.pi) ** (-k/2)
    pd *= np.linalg.det(sigma) ** (-1/2)
    pd *= np.exp(-1/2 * diff.dot(np.linalg.inv(sigma)).dot(diff))

    return pd



def force_unicode(s, encoding='utf-8', errors='strict'):
    """convert to unicode or die trying"""
    if isinstance(s, unicode):
        return s
    elif isinstance(s, str):
        return s.decode(encoding, errors)
    elif hasattr(s, '__unicode__'):
        return unicode(s)
    else:
        return str(s).decode(encoding, errors)


def logger(msg):
    fn, line = inspect.stack()[1][1:3]
    fn = fn[fn.rfind('/')+1:]
    print "%s:%d - %s" % (fn, line, msg)


# generates a list of tuples of size `n`
# each tuple is an ngram and includes the right number
# of start and end tokens ('<s>' and '</s>' by default)
# `tokens` is a list of tokens which could be strings (words)
# or objects like `models.Word`
def ngrams(tokens, n, start_tk='<s>', end_tk='</s>'):
    tokens = [start_tk] * (n-1) + tokens + [end_tk] * (n>1)
    return [tuple(tokens[i:i+n]) for i in xrange(len(tokens)-n+1)]

bigrams = partial(ngrams, n=2)
trigrams = partial(ngrams, n=3)
