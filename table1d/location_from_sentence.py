#!/usr/bin/env python

from __future__ import division

import os
import sys
import csv
import json
import pprint

from functools import partial

from tabledb import *
from parse_functions import get_parse
from generate_relations import *
from numpy import *
from collections import defaultdict



def uniquify_distribution(labels, probs):
    new_dist = defaultdict(float)
    for j in xrange(len(labels)):
        marker = str(labels[j])
        new_dist[marker] = probs[j]
    return new_dist.items()



def try_meaning():
    loc = random.uniform()
    lmk_name, lmk_loc = sample_landmark(loc)
    rel, deg = sample_reldeg(lmk_loc, loc)
    ## print "Landmark: %s" % lmk_name
    ## print "Relation: %s" % rel
    ## print "Degree: %s" % deg
    return lmk_loc, lmk_name, rel, deg



def get_expansions_prob(phrase_tuples, role, lmk=None, rel=None, deg=None):
    prob = 1.0
    for phr, expn in phrase_tuples:
        expn = ' '.join(expn)
        pe = Pexpansion.probability(expn, role=role, parent=phr,
                                  lmk=lmk, rel=rel, deg=deg)
        # FIXME I have to replace the code commented below
        # if possible.count() == 0:
        #     possible = PhraseExpansion.query.filter_by(parent = phrase)
        #     valid = PhraseExpansion.query.filter_by(parent = phrase,
        #                                             expansion = expansion)
        if not pe:
            return 0.0
        prob *= pe
    return prob



def get_words_prob(word_tuples, role, lmk=None, rel=None, deg=None):
    prob = 1.0
    for word,pos,phr in word_tuples:
        pw = Pword.probability(word, pos=pos, role=role, phr=phr,
                             lmk=lmk, rel=rel, deg=deg)
        if not pw:
            return 0.0
        prob *= pw
    return prob



def get_sentence_posteriors(sentence, iters):
    probs = []
    meanings = []
    rel_words, lmk_words, rel_phrases, lmk_phrases = get_parse(sentence)

    for j in xrange(iters):
        meaning = try_meaning()
        lmk, lmk_name, rel, deg = meaning

        r_exp_prob = get_expansions_prob(rel_phrases, 'rel', rel=rel, deg=deg)
        l_exp_prob = get_expansions_prob(lmk_phrases, 'lmk', lmk=lmk)

        r_w_prob = get_words_prob(rel_words, 'rel', rel=rel, deg=deg)
        l_w_prob = get_words_prob(lmk_words, 'lmk', lmk=lmk)

        likelihood = r_exp_prob * l_exp_prob * r_w_prob * l_w_prob
        #print "Meaning: %s, Likelihood: %1.6f" % (meaning[0:-1], likelihood)
        probs.append(likelihood)
        meanings.append(meaning)
        print '.'

    probs = array(probs) / sum(probs)
    return uniquify_distribution(meanings, probs)



def print_posteriors(posteriors):
   for m,p in posteriors:
      print 'Meaning: %-20s \t\t Probability: \t %0.4f' % (m,p)



if __name__ == '__main__':
   import getopt
   opts, extraparams = getopt.getopt(sys.argv[2:], 'i:', ['iterations'])
   sentence = sys.argv[1]
   verbose = False
   iters = 1
   for o,p in opts:
      if o in ['-i', '--iterations']:
         iters = int(p)
   posteriors = get_sentence_posteriors(sentence, iters)
   print_posteriors(posteriors)
