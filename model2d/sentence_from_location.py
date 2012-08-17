#!/usr/bin/env python
# coding: utf-8

from __future__ import division

import sys
from operator import itemgetter

from utils import (get_meaning, categorical_sample, parent_landmark,
                   lmk_id, rel_type, m2s, count_lmk_phrases)
from models import Word, Production

from location_from_sentence import get_sentence_posteriors

NONTERMINALS = ('LOCATION-PHRASE', 'RELATION', 'LANDMARK-PHRASE', 'LANDMARK')



def get_expansion(lhs, parent=None, lmk=None, rel=None):
    p_db = Production.get_productions(lhs=lhs, parent=parent,
                                      lmk=lmk_id(lmk), rel=rel_type(rel))
    num_prod = p_db.count()
    production = categorical_sample(p_db, [1/num_prod] * num_prod)
    print 'expanding:', production
    return production.rhs



def get_words(expn, parent, lmk=None, rel=None):
    words = []
    for n in expn.split():
        if n in NONTERMINALS:
            if n == parent == 'LANDMARK-PHRASE':
                # we need to move to the parent landmark
                lmk = parent_landmark(lmk)
            # we need to keep expanding
            expansion = get_expansion(n, parent, lmk, rel)
            words += get_words(expansion, n, lmk, rel)
        else:
            # get word for POS
            w_db = Word.get_words(pos=n, lmk=lmk_id(lmk), rel=rel_type(rel))
            num_w = w_db.count()
            w = categorical_sample(w_db, [1/num_w] * num_w)
            words.append(w.word)
    print 'expanding %s to %s' % (expn, words)
    return words



def generate_sentence(loc, consistent):
    # get meaning for location
    lmk, rel = get_meaning(loc=loc)
    print m2s(lmk, rel)
    meaning1 = m2s(lmk, rel)

    while True:
        # generate sentence
        rel_exp = get_expansion('RELATION', rel=rel)
        lmk_exp = get_expansion('LANDMARK-PHRASE', lmk=lmk)
        rel_words = get_words(rel_exp, 'RELATION', rel=rel)
        lmk_words = get_words(lmk_exp, 'LANDMARK-PHRASE', lmk=lmk)
        sentence = ' '.join(rel_words + lmk_words)

        if consistent:
            # get the most likely meaning for the generated sentence
            try:
                posteriors = get_sentence_posteriors(sentence, iterations=10,
                                                     extra_meaning=(lmk,rel))
            except:
                print 'try again ...'
                continue

            meaning2 = max(posteriors, key=itemgetter(1))[0]

            # is the original meaning the best one?
            if meaning1 != meaning2:
                print
                print 'sentence:', sentence
                print 'original:', meaning1
                print 'interpreted:', meaning2
                print 'try again ...'
                print
                continue

            for m,p in sorted(posteriors, key=itemgetter(1)):
                print m, p

        return sentence



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

    sentence = generate_sentence(args.location.xy, args.consistent)

    print 'sentence:', sentence
