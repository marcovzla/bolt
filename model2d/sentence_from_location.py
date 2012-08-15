#!/usr/bin/env python
# coding: utf-8

from __future__ import division

import sys
from operator import itemgetter

from utils import (get_meaning, categorical_sample, parent_landmark,
                   lmk_id, rel_type, m2s, count_lmk_phrases)
from models import Word, Production

from location_from_sentence import get_sentence_posteriors, get_sentence_meaning_likelihood
#import collections
import numpy as np

NONTERMINALS = ('LOCATION-PHRASE', 'RELATION', 'LANDMARK-PHRASE', 'LANDMARK')



def get_expansion(lhs, parent=None, lmk=None, rel=None):
    p_db = Production.get_productions(lhs=lhs, parent=parent,
                                      lmk=lmk_id(lmk), rel=rel_type(rel))
    counter = {}
    for prod in p_db.all():
        if prod in counter: counter[prod] += 1
        else: counter[prod] = 1

    #counter = collections.Counter(p_db)
    keys, counts = zip(*counter.items())
    counts = np.array(counts)
    counts /= counts.sum()

    prod, prod_prob, prod_entropy = categorical_sample(keys, counts)
    print 'expanding:', prod, prod_prob, prod_entropy
    return prod.rhs, prod_prob, prod_entropy



def get_words(expn, parent, lmk=None, rel=None):
    words = []
    probs = []
    entropy = []

    for n in expn.split():
        if n in NONTERMINALS:
            if n == parent == 'LANDMARK-PHRASE':
                # we need to move to the parent landmark
                lmk = parent_landmark(lmk)
            # we need to keep expanding
            expansion, exp_prob, exp_ent = get_expansion(n, parent, lmk, rel)
            w, w_prob, w_ent = get_words(expansion, n, lmk, rel)
            words.append(w)
            probs.append(exp_prob * w_prob)
            entropy.append(exp_ent + w_ent)
        else:
            # get word for POS
            w_db = Word.get_words(pos=n, lmk=lmk_id(lmk), rel=rel_type(rel))

            counter = {}
            for w in w_db:
                if w in counter: counter[w] += 1
                else: counter[w] = 1

            #counter = collections.Counter(w_db)
            keys, counts = zip(*counter.items())
            counts = np.array(counts)
            counts /= counts.sum()
            w, w_prob, w_entropy = categorical_sample(keys, counts)
            words.append(w.word)
            probs.append(w.prob)
            entropy.append(w_entropy)
    p, H = np.prod(probs), np.sum(entropy)
    print 'expanding %s to %s (p: %f, H: %f)' % (expn, words, p, H)
    return words, p, H

class Meaning(object):
    def __init__(self, **args):
        self.args = args


def generate_sentence(loc, consistent):
    while True:
        (lmk, lmk_prob, lmk_ent), (rel, rel_prob, rel_ent) = get_meaning(loc=loc)
        print m2s(lmk, rel)
        rel_exp, rele_prob, rele_ent = get_expansion('RELATION', rel=rel)
        lmk_exp, lmke_prob, lmke_ent = get_expansion('LANDMARK-PHRASE', lmk=lmk)
        rel_words, relw_prob, relw_ent = get_words(rel_exp, 'RELATION', rel=rel)
        lmk_words, lmkw_prob, lmkw_ent = get_words(lmk_exp, 'LANDMARK-PHRASE', lmk=lmk)
        sentence = ' '.join(rel_words + lmk_words)

        meaning = Meaning(lmk, lmk_prob, lmk_ent,
                       lmk_exp, lmke_prob, lmke_ent,
                       lmk_words, lmkw_prob, lmkw_ent,
                       rel, rel_prob, rel_ent,
                       rel_exp, rele_prob, rele_ent,
                       rel_words, relw_prob, relw_ent)
        if consistent:
            meaning1 = m2s(lmk,rel)
            # get the most likely meaning for the generated sentence
            posteriors = get_sentence_posteriors(sentence)
            meaning2 = max(posteriors, key=itemgetter(1))[0]
            # is this what we are trying to say?
            if meaning1 != meaning2:
                continue

        return meaning, sentence

def accept_correction( meaning, correction ):
    (lmk, lmk_prob, lmk_ent,
    lmk_exp, lmke_prob, lmke_ent,
    lmk_words, lmkw_prob, lmkw_ent,
    rel, rel_prob, rel_ent,
    rel_exp, rele_prob, rele_ent,
    rel_words, relw_prob, relw_ent) = meaning.args

    old_meaning_prob = get_sentence_meaning_likelihood( correction, lmk, rel )

    print lmk_prob, rel_prob, old_meaning_prob, lmk_prob * rel_prob * old_meaning_prob

# this class is only used for the --location command line argument
class Point(object):
    def __init__(self, s):
        x, y = s.split(',')
        self.xy = (float(x), float(y))
        self.x, self.y = self.xy

    def __repr__(self):
        return 'Point(%s, %s)' % self.xy



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--location', type=Point, required=True)
    parser.add_argument('--consistent', action='store_true')
    args = parser.parse_args()

    _, sentence = generate_sentence(args.location.xy, args.consistent)

    print 'sentence:', sentence
