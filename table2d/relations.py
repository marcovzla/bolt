from relation import Relation
from scipy.stats import norm
from numpy import array, random
from random import choice
from landmark import PointRepresentation

class is_adjacent(Relation):

    def __init__(self, degree):
        super(is_adjacent,self).__init__(degree)
        self.descriptions = {('near', (1.,1.,1.) ): [
                                            [['somewhat ',1.],
                                             ['pretty ',1.],
                                             ['fairly ',1.]],
                                            [['',1.],
                                             ['rather ',1.]],
                                            [['very ',1.],
                                             ['quite ',1.],
                                             ['really ',1.]]
                                         ],
                             ('close to', (1.,1.,1.) ): [
                                            [['somewhat ',1.],
                                             ['pretty ',1.],
                                             ['fairly ',1.]],
                                            [['',1],
                                             ['rather ',1.]],
                                            [['very ',1.],
                                             ['quite ',1.],
                                             ['really ',1.]]
                                         ],
                             ('at', (1.,1.,1.) ): [
                                            [['almost ',1.],
                                             ['nearly ',1.]],
                                            [['',1.]],
                                            [['squarely ',1.]]
                                         ],
                            }
        self.mus = [0.5, 0.3, 0.15]
        self.ss = [0.05, 0.05, 0.05]

    def probability(self, location, landmark):
        distance = landmark.distance_to(location)
        return self.distance_probability(distance)

    def distance_probability(self,distance):
        return 1 - norm.cdf(distance, self.mus[self.degree], self.ss[self.degree])

class not_is_adjacent(is_adjacent):

    def __init__(self, degree):
        super(not_is_adjacent,self).__init__(degree)
        for key,value in self.descriptions.items():
            for degree in value:
                for adverb in degree:
                    adverb[0] = 'not '+adverb[0]

    def probability(self, location, landmark):
        # Hack to not say "not somewhat near"
        if self.degree == 0:
            return 0
        distance = landmark.distance_to(location)
        return self.distance_probability(distance)

    def distance_probability(self,distance):
        return 1 - super(not_is_adjacent, self).distance_probability(distance)

class is_not_adjacent(Relation):

    def __init__(self, degree):
        super(is_not_adjacent,self).__init__(degree)
        self.descriptions = {('far from', (1.,1.,1.) ): [
                                            [['somewhat ',1.],
                                             ['pretty ',1.],
                                             ['fairly ',1.]],
                                            [['',1.],
                                             ['rather ',1.]],
                                            [['very ',1.],
                                             ['quite ',1.],
                                             ['really ',1.]]
                                         ],
                            }
        self.mus = [0.8, 0.9, 1.0]
        self.ss = [0.05, 0.05, 0.05]

    def probability(self, location, landmark):
        distance = landmark.distance_to(location)
        return self.distance_probability(distance)

    def distance_probability(self,distance):
        return norm.cdf(distance, self.mus[self.degree], self.ss[self.degree])

class not_is_not_adjacent(is_not_adjacent):

    def __init__(self, degree):
        super(not_is_not_adjacent,self).__init__(degree)
        for key,value in self.descriptions.items():
            for degree in value:
                for adverb in degree:
                    adverb[0] = 'not '+adverb[0]

    def probability(self, location, landmark):
        if self.degree == 0:
            return 0
        distance = landmark.distance_to(location)
        return self.distance_probability(distance)

    def distance_probability(self,distance):
        return 1 - super(not_is_not_adjacent, self).distance_probability(distance)




class on(Relation):
    def __init__(self):
        pass

    def get_description(self):
        return 'on'

    def get_all_descriptions(self):
        return [self.get_description()]

    def probability(self, location, landmark):
        return float(landmark.representation.contains( PointRepresentation(location) ))


class RelationSet(object):
    def __init__(self):
        pass

class DistanceRelationSet(RelationSet):
    def __init__(self):
        self.epsilon = 0.000001
        self.relations = [is_adjacent(0), is_adjacent(1), is_adjacent(2),
                          not_is_adjacent(0), not_is_adjacent(1), not_is_adjacent(2),
                          is_not_adjacent(0), is_not_adjacent(1), is_not_adjacent(2),
                          not_is_not_adjacent(0), not_is_not_adjacent(1), not_is_not_adjacent(2)]

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

class ContainmentRelationSet(RelationSet):
    def __init__(self):
        self.relations = [on()]

    def sample_landmark(self, landmarks, poi):
        on_lmks = []
        for i,lmk in enumerate(landmarks):
            if self.relations[0].probability(poi,lmk):
                on_lmks.append( i )
        return choice(on_lmks)

    def sample_relation(self, sampled_landmark, poi):
        return self.relations[0]
