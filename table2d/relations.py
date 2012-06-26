from relation import Relation
from scipy.stats import norm

class is_adjacent(Relation):

    def __init__(self, degree):
        super(is_adjacent,self).__init__(degree)
        self.descriptions = {('near', (1.,1.,1.) ): [
                                            [('somewhat ',1.),
                                             ('pretty ',1.),
                                             ('fairly ',1.)],
                                            [('',1.),
                                             ('rather ',1.)],
                                            [('very ',1.),
                                             ('quite ',1.),
                                             ('really ',1.)]
                                         ],
                             ('close to', (1.,1.,1.) ): [
                                            [('somewhat ',1.),
                                             ('pretty ',1.),
                                             ('fairly ',1.)],
                                            [('',1),
                                             ('rather ',1.)],
                                            [('very ',1.),
                                             ('quite ',1.),
                                             ('really ',1.)]
                                         ],
                             ('at', (1.,1.,1.) ): [
                                            [('almost ',1.),
                                             ('nearly ',1.)],
                                            [('',1.)],
                                            [('squarely ',1.)]
                                         ],
                            }
        self.mus = [0.5, 0.3, 0.15]
        self.ss = [0.01, 0.01, 0.01]

    def probability(self, location, landmark):
        distance = landmark.distance_to(location)
        return self.distance_probability(distance)

    def distance_probability(self,distance):
        return 1 - norm.cdf(distance, self.mus[self.degree], self.ss[self.degree])

class not_is_adjacent(is_adjacent):

    def get_description(self):
        return "not " + super(not_is_adjacent, self).get_description()

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
                                            [('somewhat ',1.),
                                             ('pretty ',1.),
                                             ('fairly ',1.)],
                                            [('',1.),
                                             ('rather ',1.)],
                                            [('very ',1.),
                                             ('quite ',1.),
                                             ('really ',1.)]
                                         ],
                            }
        self.mus = [0.8, 0.9, 0.1]
        self.ss = [0.01, 0.01, 0.01]

    def probability(self, location, landmark):
        distance = landmark.distance_to(location)
        return self.distance_probability(distance)

    def distance_probability(self,distance):
        return norm.cdf(distance, self.mus[self.degree], self.ss[self.degree])

class not_is_not_adjacent(is_not_adjacent):

    def get_description(self):
        return "not " + super(not_is_not_adjacent, self).get_description()

    def probability(self, location, landmark):
        if self.degree == 0:
            return 0
        distance = landmark.distance_to(location)
        return self.distance_probability(distance)

    def distance_probability(self,distance):
        return 1 - super(not_is_not_adjacent, self).distance_probability(distance)

relations = [is_adjacent(0), is_adjacent(1), is_adjacent(2),
             not_is_adjacent(0), not_is_adjacent(1), not_is_adjacent(2),
             is_not_adjacent(0), is_not_adjacent(1), is_not_adjacent(2),
             not_is_not_adjacent(0), not_is_not_adjacent(1), not_is_not_adjacent(2)]
