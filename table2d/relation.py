from random import choice
from numpy import *
from numpy.random import multinomial, sample
from scipy.stats import *
from itertools import *
from planar import Vec2, Affine
from planar.line import LineSegment, Ray
from functools import partial
from landmark import Landmark, PointRepresentation

class Relation(object):

    def __init__(self, degree):
        self.degree = degree
        self.descriptions = {}

    def get_description(self):
        preposition_keys, preposition_scores = zip( *[(key,key[1][self.degree]) for key in self.descriptions.keys()] )
        preposition_scores = array(preposition_scores)
        preposition_probabilities = preposition_scores/sum(preposition_scores)
        preposition_index = preposition_probabilities.cumsum().searchsorted( sample(1) )[0]
        preposition_key = preposition_keys[preposition_index]
        preposition = preposition_key[0]

        adverbs, adverb_scores = zip( *self.descriptions[preposition_key][self.degree] )
        adverb_scores = array(adverb_scores)
        adverb_probabilities = adverb_scores/sum(adverb_scores)
        adverb_index = adverb_probabilities.cumsum().searchsorted( sample(1) )[0]
        adverb = adverbs[adverb_index]
        return adverb + preposition

    def get_all_descriptions(self):
        descriptions = []

        for key in self.descriptions.keys():
            prep = key[0]
            for adv_k in self.descriptions[key][self.degree]:
                adverb = adv_k[0]
                descriptions.append(adverb + prep)

        return descriptions


class RelationSet(object):
    def __init__(self):
        pass



class Measurement(object):
    def __init__(self, direction):
        self.direction = direction
        self.words = {'far': (0.9, 0.05, 1),
                      'close': (0.5, 0.05, -1),
                      'near': (0.5, 0.05, -1)}
        self.degrees = {'very ': 1.5, '': 1, 'somewhat ': 0.75}

    def evaluate(self, adverb, word, distance):
        mu,std,sign = self.words[word]
        mult = self.degrees[adverb]

        p = norm.cdf(distance, mu * mult, std)
        if sign < 0: p = 1 - p
        return p

    def get_description(self, distance):
        probs = []

        for word in self.words:
            for adverb in self.degrees:
                p = self.evaluate(adverb, word, distance)
                probs.append([p, adverb + word])

        return sorted(probs, reverse=True)[0][1]



class DistanceRelation(Relation):
    def __init__(self, words):
        self.measurement = Measurement(None)
        self.words = words

        self.perspective = None
        self.landmark = None
        self.poi = None

    def evaluate(self, perspective, landmark, poi):
        self.perspective = perspective
        self.poi = poi

        p_segment = LineSegment.from_points( [perspective, landmark.representation.middle] )

        self.distance = p_segment.end.distance_to(poi)
        return 1.0

    def get_distance(self, perspective, landmark, poi):
        if not (self.perspective == perspective 
                and self.landmark == landmark 
                and self.poi == poi):
            self.evaluate(perspective, landmark, poi)
        return self.distance

    def get_description(self, perspective, landmark, poi):
        distance = self.get_distance(perspective, landmark, poi)

        return self.measurement.get_description(distance) + ' ' + choice(self.words)

from_rel = DistanceRelation(['from'])
to       = DistanceRelation(['to'])

class VeryCloseDistanceRelation(DistanceRelation):
    def __init__(self, words):
        super(VeryCloseDistanceRelation,self).__init__(words)
        self.word = 'close'
        self.adverb = 'very '

    def evaluate(self, perspective, landmark, poi):
        super(VeryCloseDistanceRelation,self).evaluate(perspective, landmark, poi)
        return self.measurement.evaluate( self.word, self.adverb, self.distance)

    def get_description(self, perspective, landmark, poi):
        return choice(self.words)

next_to = VeryCloseDistanceRelation(['next to'])
at      = VeryCloseDistanceRelation(['at'])
by      = VeryCloseDistanceRelation(['by'])

class DistanceRelationSet(RelationSet):
    def __init__(self):
        self.epsilon = 0.000001
        self.relations = [from_rel, to, next_to, at, by]

    def sample_landmark(self, landmarks, poi):
        distances = array([lmk.distance_to(poi) for lmk in landmarks])
        scores = 1.0/(array(distances)**1.5 + self.epsilon)
        lm_probabilities = scores/sum(scores)
        index = lm_probabilities.cumsum().searchsorted( random.sample(1) )[0]
        return index

    def sample_relation(self, sampled_landmark, poi):
        rel_scores = []
        for relation in self.relations:
            rel_scores.append( relation.probability(poi, sampled_landmark) )
        rel_scores = array(rel_scores)
        rel_probabilities = rel_scores/sum(rel_scores)
        index = rel_probabilities.cumsum().searchsorted( random.sample(1) )[0]
        return self.relations[index]




class ContainmentRelation(Relation):
    pass

class OrientationRelation(Relation):
    def __init__(self, orientation, words):
        self.standard = Vec2(0,1)
        self.orientation = orientation
        self.measurement = Measurement(orientation)
        self.words = words

        self.perspective = None
        self.landmark = None
        self.poi = None

    def evaluate(self, perspective, landmark, poi):
        self.perspective = perspective
        self.landmark = landmark
        self.poi = poi

        p_segment = LineSegment.from_points( [perspective, landmark.representation.middle] )

        angle = self.standard.angle_to(p_segment.vector)
        rotation = Affine.rotation(angle)
        o = [self.orientation]
        rotation.itransform(o)
        direction = o[0]
        orientation = Ray(p_segment.end, direction)

        projected = orientation.line.project(poi)
        self.distance = orientation.start.distance_to(projected)
        if orientation.contains_point(projected):
            return 1.0
        else:
            return 0.0

    def get_distance(self, perspective, landmark, poi):
        if not (self.perspective == perspective 
                and self.landmark == landmark 
                and self.poi == poi):
            self.evaluate(perspective, landmark, poi)
        return self.distance

    def get_description(self, perspective, landmark, poi):
        distance = self.get_distance(perspective, landmark, poi)

        return self.measurement.get_description(distance) + ' ' + choice(self.words)

in_front = OrientationRelation( Vec2(0,1), ['in front of'] )
behind   = OrientationRelation( Vec2(0,-1), ['behind'] )
left     = OrientationRelation( Vec2(-1,0), ['left of'] )
right    = OrientationRelation( Vec2(1,0), ['right of'] ) 


if __name__ == '__main__':
    print in_front.get_description(Vec2(0,0), Landmark('thing', PointRepresentation(Vec2(0,1)), None, []), Vec2(-1,1))
    # print behind.get_description(LineSegment(Vec2(0,0), Vec2(0,1)), Vec2(-1,1))
    # print left.get_description(LineSegment(Vec2(0,0), Vec2(0,1)), Vec2(-1,1))
    # print right.get_description(LineSegment(Vec2(0,0), Vec2(0,1)), Vec2(-1,1))
