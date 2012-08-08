#!/usr/bin/env python
from __future__ import division

import os
import sys

from tabledb import *
from generate_relations import *
from numpy import *



def get_meaning(loc):
    """sample landmark and degree for given location"""
    lmk_name, lmk_loc = sample_landmark(loc)
    rel, deg = sample_reldeg(loc, lmk_loc)
    print "Landmark: %s" % lmk_name
    print "Relation: %s" % rel
    print "Degree: %s" % deg
    # we don't really care about the landmark name
    return lmk_loc, rel, deg



def get_expansion(phr, role, lmk=None, rel=None, deg=None):
    """sample an expansion from the db"""
    expansions = Phrase.get_expansions(lmk=lmk, rel=rel, deg=deg, role=role, parent=phr)
    num_exp = expansions.count()

    if num_exp == 0:
        # one more chance
        expansions = Phrase.get_expansions(parent=phr)
        num_exp = expansions.count()

    expn = categorical_sample(expansions, [1/num_exp] * num_exp).expansion
    print "Expanding %s to %s" % (phr, expn)
    return expn



def get_words(phr, role, expn, lmk=None, rel=None, deg=None):
    """returns words for `expn`"""
    words = []
    for n in expn.split():
        if n in ['REL', 'LMK', 'PP', 'OFNP', 'OFNP1', 'OFNP2', 'NP']:
            # expand!
            expansion = get_expansion(n, role, lmk, rel, deg)
            words += get_words(n, role, expansion, lmk, rel, deg)
        else:
            w_db = Word.get_words(pos=n, role=role, phr=phr, lmk=lmk, rel=rel, deg=deg)
            num_w = w_db.count()
            w = categorical_sample(w_db, [1/num_w] * num_w).word
            words.append(w)
    print "Expanding %s to %s" % (expn, words)
    return words



def generate_sentence(loc, meaning=None):
    if meaning:
        try:
            lmk, rel, deg = meaning
        except ValueError:
            raise Exception("Meaning has the wrong number of pieces")
    else:
        lmk, rel, deg = get_meaning(loc)

    # get expansion for meaning
    rs = get_expansion('REL', 'rel', rel=rel, deg=deg)
    ls = get_expansion('LMK', 'lmk', lmk=lmk)

    # get words for expansions
    rw = get_words('REL', 'rel', rs, rel=rel, deg=deg)
    lw = get_words('LMK', 'lmk', ls, lmk=lmk)

    # build sentence
    sentence = ' '.join(rw + lw)
    print sentence
    return sentence



if __name__ == '__main__':
    import getopt
    opts, extraparams = getopt.getopt(sys.argv[1:], 'm:l:', ['meaning','location'])
    location = None
    meaning = None
    for o,p in opts:
        if o in ['-m', '--meaning']:
            meaning = p
        elif o in ['-l', '--location']:
            location = float(p)
    generate_sentence(location, meaning)
