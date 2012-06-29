from random import choice
from numpy import *
from numpy.random import multinomial, sample
from scipy.stats import *
from itertools import *



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
