#!/usr/bin/env python
# coding: utf-8

from __future__ import division

import sys

from utils import ModelScene, categorical_sample, parent_landmark
from models import Word, Production

NONTERMINALS = ('LOCATION-PHRASE', 'RELATION', 'LANDMARK-PHRASE', 'LANDMARK')

scene = ModelScene()



def lmk_id(lmk):
    if lmk: return scene.get_landmark_id(lmk)

def rel_type(rel):
    if rel: return rel.__class__.__name__



def get_meaning(loc):
    lmk, rel = scene.sample_lmk_rel(loc)
    print 'landmark: %s (%s)' % (lmk, lmk_id(lmk))
    print 'relation:', rel_type(rel)
    return lmk, rel



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



def generate_sentence(loc):
    lmk, rel = get_meaning(loc)
    rel_exp = get_expansion('RELATION', rel=rel)
    lmk_exp = get_expansion('LANDMARK-PHRASE', lmk=lmk)
    rel_words = get_words(rel_exp, 'RELATION', rel=rel)
    lmk_words = get_words(lmk_exp, 'LANDMARK-PHRASE', lmk=lmk)
    return ' '.join(rel_words + lmk_words)



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
    args = parser.parse_args()
    sentence = generate_sentence(args.location.xy)
    print 'sentence:', sentence
