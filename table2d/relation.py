from random import choice
from numpy import array, random
from scipy.stats import norm
from planar import Vec2, Affine
from planar.line import LineSegment, Ray
from landmark import PointRepresentation


class Relation(object):
    def __init__(self, perspective, landmark, trajector):
        self.perspective = perspective
        self.landmark = landmark
        self.trajector = trajector


class RelationSet(object):
    def __init__(self):
        pass


class Degree(object):
    NONE = 2001
    # NOT_VERY = 2002
    SOMEWHAT = 2003
    VERY = 2004


class Measurement(object):
    NONE = 1001
    FAR = 1002
    CLOSE = 1003
    NEAR = 1004

    def __init__(self, distance, required=True):
        self.distance_class = {
            Measurement.FAR: (0.9, 0.05, 1),
            Measurement.CLOSE: (0.25, 0.05, -1),
            Measurement.NEAR: (0.4, 0.05, -1)
        }

        if not required:
            self.distance_class[Measurement.NONE] = (-100, 0.05, 1)

        self.degree_class = {
            Degree.NONE: 1,
            # Degree.NOT_VERY: 0.6,
            Degree.SOMEWHAT: 0.75,
            Degree.VERY: 1.5
        }

        self.required = required
        self.distance = distance
        self.best = self.evaluate_all()
        self.best_distance_class = self.best[2]

        if self.best_distance_class == Measurement.NONE:
            self.best_degree_class = Degree.NONE
        else:
            self.best_degree_class = self.best[1]

    def is_applicable(self, degree_class=None, distance_class=None):
        if degree_class is None:
            degree_class = self.best_degree_class
        if distance_class is None:
            distance_class = self.best_distance_class

        mu,std,sign = self.distance_class[distance_class]
        mult = self.degree_class[degree_class]

        p = norm.cdf(self.distance, mu * (mult ** sign), std)
        if sign < 0: p = 1 - p
        return p

    def evaluate_all(self):
        probs = []

        for dist in self.distance_class:
            for degree in self.degree_class:
                p = self.is_applicable(degree, dist)
                probs.append([p, degree, dist])

        ps, degrees, dists = zip(*probs)
        ps = array(ps)
        ps /= sum(ps)
        index = ps.cumsum().searchsorted( random.sample(1) )[0]
        return probs[index]

    def __repr__(self):
        return 'Measurement< req: %i, bdegree: %i, bdistance: %i >' % (self.required, self.best_degree, self.best_distance)


class DistanceRelation(Relation):
    def __init__(self, perspective, landmark, trajector):
        super(DistanceRelation, self).__init__(perspective, landmark, trajector)
        self.distance = self.landmark.distance_to(self.trajector)
        self.measurement = Measurement(self.distance)

    def is_applicable(self):
        if not self.landmark.representation.contains( self.trajector ):
            return self.measurement.is_applicable()
        else:
            return 0.0


class FromRelation(DistanceRelation):
    def __init__(self, perspective, landmark, trajector):
        super(FromRelation, self).__init__(perspective, landmark, trajector)


class ToRelation(DistanceRelation):
    def __init__(self, perspective, landmark, trajector):
        super(ToRelation, self).__init__(perspective, landmark, trajector)


class VeryCloseDistanceRelation(DistanceRelation):
    def __init__(self, perspective, landmark, trajector):
        super(VeryCloseDistanceRelation, self).__init__(perspective, landmark, trajector)
        self.measurement.best_degree_class = Degree.VERY
        self.measurement.best_distance_class = Measurement.CLOSE

    def is_applicable(self):
        return super(VeryCloseDistanceRelation,self).is_applicable() and self.measurement.is_applicable()


class NextToRelation(VeryCloseDistanceRelation):
    def __init__(self, perspective, landmark, trajector):
        super(NextToRelation, self).__init__(perspective, landmark, trajector)


class AtRelation(VeryCloseDistanceRelation):
    def __init__(self, perspective, landmark, trajector):
        super(AtRelation, self).__init__(perspective, landmark, trajector)


class ByRelation(VeryCloseDistanceRelation):
    def __init__(self, perspective, landmark, trajector):
        super(ByRelation, self).__init__(perspective, landmark, trajector)


class ContainmentRelation(Relation):
    def __init__(self, perspective, landmark, trajector):
        super(ContainmentRelation, self).__init__(perspective, landmark, trajector)

    def is_applicable(self):
        return float(self.landmark.representation.contains( self.trajector ))


class OnRelation(ContainmentRelation):
    def __init__(self, perspective, landmark, trajector):
        super(OnRelation, self).__init__(perspective, landmark, trajector)


class InRelation(ContainmentRelation):
    def __init__(self, perspective, landmark, trajector):
        super(InRelation, self).__init__(perspective, landmark, trajector)


class OrientationRelation(Relation):
    def __init__(self, perspective, landmark, trajector, orientation):
        super(OrientationRelation, self).__init__(perspective, landmark, trajector)
        self.standard = Vec2(0,1)
        self.orientation = orientation

        top_primary_axes = landmark.get_top_parent().get_primary_axes()

        our_axis = None
        for axis in top_primary_axes:
            if axis.contains_point(perspective):
                our_axis = axis
        assert( our_axis != None )

        new_axis = our_axis.parallel(self.landmark.representation.middle)
        new_perspective = new_axis.project(perspective)

        p_segment = LineSegment.from_points( [new_perspective, self.landmark.representation.middle] )

        angle = self.standard.angle_to(p_segment.vector)
        rotation = Affine.rotation(angle)
        o = [self.orientation]
        rotation.itransform(o)
        direction = o[0]
        self.ori_ray = Ray(p_segment.end, direction)
        # TODO make sure this works using .middle
        self.projected = self.ori_ray.line.project(trajector.middle)

        self.distance = self.ori_ray.start.distance_to(self.projected)
        self.measurement = Measurement(self.distance, required=False)

    def is_applicable(self):
        if self.ori_ray.contains_point(self.projected) and not \
            self.landmark.representation.contains(PointRepresentation(self.projected)):
            return self.measurement.is_applicable()
        else:
            return 0.0


class InFrontRelation(OrientationRelation):
    def __init__(self, perspective, landmark, trajector):
        super(InFrontRelation, self).__init__(perspective, landmark, trajector, Vec2(0,-1))


class BehindRelation(OrientationRelation):
    def __init__(self, perspective, landmark, trajector):
        super(BehindRelation, self).__init__(perspective, landmark, trajector, Vec2(0,1))


class LeftRelation(OrientationRelation):
    def __init__(self, perspective, landmark, trajector):
        super(LeftRelation, self).__init__(perspective, landmark, trajector, Vec2(-1,0))


class RightRelation(OrientationRelation):
    def __init__(self, perspective, landmark, trajector):
        super(RightRelation, self).__init__(perspective, landmark, trajector, Vec2(1,0))


class DistanceRelationSet(RelationSet):

    epsilon = 0.000001
    relations = [FromRelation, ToRelation, NextToRelation, AtRelation, ByRelation]

    @classmethod
    def sample_landmark(class_, landmarks, trajector):
        distances = array([lmk.distance_to(trajector) for lmk in landmarks])
        scores = 1.0/(array(distances)**1.5 + class_.epsilon)
        scores[distances == 0] = 0
        lm_probabilities = scores/sum(scores)
        index = lm_probabilities.cumsum().searchsorted( random.sample(1) )[0]
        return index

    @classmethod
    def sample_relation(class_, perspective, sampled_landmark, trajector):
        rel_scores = []
        rel_instances = []

        for relation in class_.relations:
            rel_instances.append( relation(perspective, sampled_landmark, trajector) )
            rel_scores.append( rel_instances[-1].is_applicable() )

        rel_scores = array(rel_scores)
        rel_probabilities = rel_scores/sum(rel_scores)
        index = rel_probabilities.cumsum().searchsorted( random.sample(1) )[0]
        return rel_instances[index]


class ContainmentRelationSet(RelationSet):

    relations = [OnRelation, InRelation]

    @classmethod
    def sample_landmark(class_,landmarks, trajector):
        on_lmks = []
        for i,lmk in enumerate(landmarks):
            if class_.relations[0](None, lmk, trajector).is_applicable():
                on_lmks.append( i )
        return choice(on_lmks)

    @classmethod
    def sample_relation(class_, perspective, sampled_landmark, trajector):
        return choice(class_.relations)(perspective, sampled_landmark, trajector)


class OrientationRelationSet(RelationSet):

    relations = [InFrontRelation, BehindRelation, LeftRelation, RightRelation]

    @staticmethod
    def sample_landmark(landmarks, trajector):
        on_lmks = []

        for i,lmk in enumerate(landmarks):
            if not lmk.representation.contains( trajector ):
                on_lmks.append( i )

        return choice(on_lmks)

    @classmethod
    def sample_relation(class_, perspective, sampled_landmark, trajector):
        return choice( class_.get_applicable_relations(perspective,sampled_landmark,trajector,True) )

    @classmethod
    def get_applicable_relations(class_, perspective, sampled_landmark, trajector, use_distance):
        rels = []

        for rel in class_.relations:
            rel_instance = rel(perspective, sampled_landmark, trajector)
            if not use_distance:
                rel_instance.measurement.best_distance = Measurement.NONE
                rel_instance.measurement.best_degree = Degree.NONE
            if rel_instance.is_applicable():
                rels.append(rel_instance)

        return rels