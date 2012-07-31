#!/usr/bin/env python

from __future__ import division

import sys
import random
from itertools import product

import numpy as np
from planar import Vec2, BoundingBox

# import stuff from table2d
sys.path.append('..')
from table2d.landmark import RectangleRepresentation, Scene, Landmark
from table2d.relation import (DistanceRelationSet,
                              ContainmentRelationSet,
                              OrientationRelationSet,
                              VeryCloseDistanceRelation)



def parent_landmark(lmk):
    if lmk:
        parent = lmk.parent
        if parent and not isinstance(parent, Landmark):
            parent = parent.parent_landmark
        return parent



# FIXME this is a copy of `Speaker.get_head_on_viewpoint`
# ideally, i should be able to access it directly from `Speaker`
def get_head_on_viewpoint(landmark, reference):
    axes = landmark.get_primary_axes()
    idx = np.argmin([axis.distance_to(reference) for axis in axes])
    axis = axes[idx]
    head_on = axis.project(reference)
    return head_on



class ModelScene(object):
    def __init__(self):
        self.scene = Scene(3)

        # not a very furnished scene, we only have one table
        table = Landmark('table',
                         RectangleRepresentation(rect=BoundingBox([Vec2(5,5), Vec2(6,7)])),
                         None,
                         Landmark.TABLE)

        self.scene.add_landmark(table)
        self.table = table

        # there is a person standing at this location
        # he will be our reference
        self.speaker = Vec2(5.5, 4.5)

        # NOTE we need to keep around the list of landmarks so that we can
        # access them by id, which is the index of the landmark in this list

        # we will use the middle of the table to generate the landmark list
        loc = (Vec2(5,5) + Vec2(6,7)) * 0.5

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

        # these are the different kinds of relationships we support
        RelSets = [DistanceRelationSet, ContainmentRelationSet, OrientationRelationSet]

        while True:
            # what kind of relationship do we want?
            RelSet = random.choice(RelSets)
            relset = RelSet()

            try:
                # sample everything
                index = relset.sample_landmark(landmarks, loc)
                sampled_lmk = landmarks[index]
                head_on = get_head_on_viewpoint(sampled_lmk, self.speaker)
                sampled_rel = relset.sample_relation(head_on, sampled_lmk, loc)
                return sampled_lmk, sampled_rel
            except:
                # if we restrict the list of landmarks by the number of ancestors
                # we may get a list with landmarks that the sampled RelSet does not like
                # so we remove that RelSet from the RelSets list and try again
                for RelSet in RelSets:
                    if isinstance(relset, RelSet):
                        break
                RelSets.pop(RelSets.index(RelSet))
                continue



# we will use this instance of the scene
scene = ModelScene()

def lmk_id(lmk):
    if lmk: return scene.get_landmark_id(lmk)

def rel_type(rel):
    if rel: return rel.__class__.__name__

def get_meaning(loc=None, num_ancestors=None):
    if not loc:
        loc = scene.get_rand_loc()

    lmk, rel = scene.sample_lmk_rel(loc, num_ancestors)
    # print 'landmark: %s (%s)' % (lmk, lmk_id(lmk))
    # print 'relation:', rel_type(rel)
    return lmk, rel




def categorical_sample(values, probs):
    index = np.random.multinomial(1, probs).nonzero()[0][0]
    value = values[index]
    return value



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

