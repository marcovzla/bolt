from random import choice
from numpy import *
from numpy.random import multinomial, sample
from scipy.stats import *
from itertools import *
from planar import Vec2, Affine
from planar.line import LineSegment, Ray
from landmark import Landmark, PointRepresentation


class Relation(object):
    def __init__(self, perspective, landmark, poi, words):
        self.perspective = perspective
        self.landmark = landmark
        self.poi = poi
        self.words = words


class RelationSet(object):
    def __init__(self):
        pass


class Measurement(object):
    def __init__(self, distance, direction=None):
        self.words = {'far': (0.9, 0.05, 1),
                      'close': (0.25, 0.05, -1),
                      'near': (0.4, 0.05, -1)}
        self.degrees = {'': 1, 'not very ': 0.6, 'somewhat ': 0.75, 'very ': 1.5}

        self.distance = distance
        self.direction = direction

        self.best = self.evaluate_all(self.distance)[0]
        self.degree = self.best[1]
        self.word = self.best[2]

    def is_applicable(self, adverb, word, distance):
        mu,std,sign = self.words[word]
        mult = self.degrees[adverb]

        p = norm.cdf(distance, mu * (mult ** sign), std)
        if sign < 0: p = 1 - p
        return p

    def evaluate_all(self, distance):
        probs = []

        for word in self.words:
            for adverb in self.degrees:
                p = self.is_applicable(adverb, word, distance)
                probs.append([p, adverb, word])

        return sorted(probs, reverse=True)

    def get_description(self):
        return self.degree + self.word


class DistanceRelation(Relation):
    def __init__(self, perspective, landmark, poi, words):
        super(DistanceRelation, self).__init__(perspective, landmark, poi, words)
        self.distance = self.landmark.distance_to(self.poi)
        self.measurement = Measurement(self.distance)

    def is_applicable(self):
        if not self.landmark.representation.contains( PointRepresentation(self.poi) ):
            return 1.0
        else:
            return 0.0

    def get_description(self):
        return self.measurement.get_description() + ' ' + choice(self.words)


class FromRelation(DistanceRelation):
    def __init__(self, perspective, landmark, poi):
        super(FromRelation, self).__init__(perspective, landmark, poi, ['from'])


class ToRelation(DistanceRelation):
    def __init__(self, perspective, landmark, poi):
        super(ToRelation, self).__init__(perspective, landmark, poi, ['to'])


class VeryCloseDistanceRelation(DistanceRelation):
    def __init__(self, perspective, landmark, poi, words):
        super(VeryCloseDistanceRelation, self).__init__(perspective, landmark, poi, words)
        self.word = 'close'
        self.adverb = 'very '

    def is_applicable(self):
        return super(VeryCloseDistanceRelation,self).is_applicable() and self.measurement.is_applicable(self.adverb, self.word, self.distance)

    def get_description(self):
        return choice(self.words)


class NextToRelation(VeryCloseDistanceRelation):
    def __init__(self, perspective, landmark, poi):
        super(NextToRelation, self).__init__(perspective, landmark, poi, ['next to'])


class AtRelation(VeryCloseDistanceRelation):
    def __init__(self, perspective, landmark, poi):
        super(AtRelation, self).__init__(perspective, landmark, poi, ['at'])


class ByRelation(VeryCloseDistanceRelation):
    def __init__(self, perspective, landmark, poi):
        super(ByRelation, self).__init__(perspective, landmark, poi, ['by'])


class ContainmentRelation(Relation):
    def __init__(self, perspective, landmark, poi, words):
        super(ContainmentRelation, self).__init__(perspective, landmark, poi, words)

    def is_applicable(self):
        return float(self.landmark.representation.contains( PointRepresentation(self.poi) ))

    def get_description(self):
        return choice(self.words)


class OnRelation(ContainmentRelation):
    def __init__(self, perspective, landmark, poi):
        super(OnRelation, self).__init__(perspective, landmark, poi, ['on'])


class InRelation(ContainmentRelation):
    def __init__(self, perspective, landmark, poi):
        super(InRelation, self).__init__(perspective, landmark, poi, ['in'])


class OrientationRelation(Relation):
    def __init__(self, perspective, landmark, poi, words, orientation):
        super(OrientationRelation, self).__init__(perspective, landmark, poi, words)
        self.standard = Vec2(0,1)
        self.orientation = orientation

        p_segment = LineSegment.from_points( [self.perspective, self.landmark.representation.middle] )

        angle = self.standard.angle_to(p_segment.vector)
        rotation = Affine.rotation(angle)
        o = [self.orientation]
        rotation.itransform(o)
        direction = o[0]
        self.ori_ray = Ray(p_segment.end, direction)
        self.projected = self.ori_ray.line.project(poi)

        self.distance = self.ori_ray.start.distance_to(self.projected)
        self.measurement = Measurement(self.distance, self.orientation)

    def is_applicable(self):
        if self.ori_ray.contains_point(self.projected):
            return 1.0
        else:
            return 0.0

    def get_description(self):
        return self.measurement.get_description() + ' ' + choice(self.words)


class InFrontRelation(OrientationRelation):
    def __init__(self, perspective, landmark, poi):
        super(InFrontRelation, self).__init__(perspective, landmark, poi, ['in front of'], Vec2(0,-1))


class BehindRelation(OrientationRelation):
    def __init__(self, perspective, landmark, poi):
        super(BehindRelation, self).__init__(perspective, landmark, poi, ['behind'], Vec2(0,1))


class LeftRelation(OrientationRelation):
    def __init__(self, perspective, landmark, poi):
        super(LeftRelation, self).__init__(perspective, landmark, poi, ['to the left of'], Vec2(-1,0))


class RightRelation(OrientationRelation):
    def __init__(self, perspective, landmark, poi):
        super(RightRelation, self).__init__(perspective, landmark, poi, ['to the right of'], Vec2(1,0))


class DistanceRelationSet(RelationSet):
    def __init__(self):
        self.epsilon = 0.000001
        self.relations = [FromRelation, ToRelation, NextToRelation, AtRelation, ByRelation]

    def sample_landmark(self, landmarks, poi):
        distances = array([lmk.distance_to(poi) for lmk in landmarks])
        scores = 1.0/(array(distances)**1.5 + self.epsilon)
        lm_probabilities = scores/sum(scores)
        index = lm_probabilities.cumsum().searchsorted( random.sample(1) )[0]
        return index

    def sample_relation(self, perspective, sampled_landmark, poi):
        rel_scores = []
        rel_instances = []

        for relation in self.relations:
            rel_instances.append( relation(perspective, sampled_landmark, poi) )
            rel_scores.append( rel_instances[-1].is_applicable() )

        rel_scores = array(rel_scores)
        rel_probabilities = rel_scores/sum(rel_scores)
        index = rel_probabilities.cumsum().searchsorted( random.sample(1) )[0]
        return rel_instances[index]


class ContainmentRelationSet(RelationSet):
    def __init__(self):
        self.relations = [OnRelation, InRelation]

    def sample_landmark(self, landmarks, poi):
        on_lmks = []
        for i,lmk in enumerate(landmarks):
            if self.relations[0](None, lmk, poi).is_applicable():
                on_lmks.append( i )
        return choice(on_lmks)

    def sample_relation(self, perspective, sampled_landmark, poi):
        return choice(self.relations)(perspective, sampled_landmark, poi)

class OrientationRelationSet(RelationSet):
    def __init__(self):
        self.relations = [InFrontRelation, BehindRelation, LeftRelation, RightRelation]

    def sample_landmark(self, landmarks, poi):
        on_lmks = []

        for i,lmk in enumerate(landmarks):
            if not lmk.representation.contains( PointRepresentation(poi) ):
                on_lmks.append( i )

        return choice(on_lmks)

    def sample_relation(self, perspective, sampled_landmark, poi):
        rels = []

        for rel in self.relations:
            rel_instance = rel(perspective, sampled_landmark, poi)
            if rel_instance.is_applicable():
                rels.append(rel_instance)

        return choice(rels)


if __name__ == '__main__':
    print in_front.get_description(Vec2(0,0), Landmark('thing', PointRepresentation(Vec2(0,1)), None, []), Vec2(-1,1))
    # print behind.get_description(LineSegment(Vec2(0,0), Vec2(0,1)), Vec2(-1,1))
    # print left.get_description(LineSegment(Vec2(0,0), Vec2(0,1)), Vec2(-1,1))
    # print right.get_description(LineSegment(Vec2(0,0), Vec2(0,1)), Vec2(-1,1))
