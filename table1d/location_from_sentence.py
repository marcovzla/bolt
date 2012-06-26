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
from ast import literal_eval
from collections import defaultdict

def uniquify_distribution(labels, probs):
   new_dist = defaultdict(float)
   for j in range(len(labels)):
       marker = str(labels[j])
       new_dist[marker] = probs[j]
   return new_dist.items()

def try_meaning():
    loc = random.uniform()
    lmk_name, lmk_loc = sample_landmark(loc)
    rel, deg = sample_reldeg(loc, lmk_loc)
    rel_ctx = RelationContext.get_by(
        relation = rel,
        degree = deg)
    lmk_ctx = LandmarkContext.get_by(
        landmark_name = lmk_name,
        landmark_location = lmk_loc)
    ctx = Context.get_by(
        relation = rel_ctx,
        landmark = lmk_ctx)
    ## print "Landmark: %s" % lmk_name
    ## print "Relation: %s" % rel
    ## print "Degree: %s" % deg
    return([rel,deg,lmk_name,lmk_loc], rel_ctx, lmk_ctx, ctx)

def get_expansions_prob(rel_ctx, lmk_ctx, ctx, role, phrase_tuples):
    prob = 1
    for phr, expn in phrase_tuples:
        phrase = Phrase.get_by(phrase = phr)
        expansion = PhraseExpansion.get_by(expansion = str(expn)).expansion
        if role == 'rel':
            possible = PhraseExpansion.query.filter_by(parent = phrase,
                                                       relation_context = rel_ctx)
            valid = PhraseExpansion.query.filter_by(parent = phrase,
                                                    relation_context = rel_ctx,
                                                    expansion = expansion)
        else:
            possible = PhraseExpansion.query.filter_by(parent = phrase,
                                                       landmark_context = lmk_ctx)
            valid = PhraseExpansion.query.filter_by(parent = phrase,
                                                    landmark_context = lmk_ctx,
                                                    expansion = expansion)
        if possible.count() == 0:
            possible = PhraseExpansion.query.filter_by(parent = phrase)
            valid = PhraseExpansion.query.filter_by(parent = phrase,
                                                    expansion = expansion)
        factor = valid.count() / possible.count()
        if factor == 0: return 0.0
        else: prob *= factor
    return prob

def get_words_prob(rel_ctx, lmk_ctx, ctx, role, word_tuples):
    prob = 1
    for word,pos,phr in word_tuples:
        tag = PartOfSpeech.get_by(pos = pos, role = role)
        phrase = Phrase.get_by(phrase = phr, role = role)
        if role == 'rel':
            possible = Word.query.filter_by(phrase = phrase,
                                            pos = tag,
                                            relation_context = rel_ctx)
            valid = Word.query.filter_by(phrase = phrase,
                                         pos = tag,
                                         relation_context = rel_ctx,
                                         word = word)
        if role == 'lmk':
            possible = Word.query.filter_by(phrase = phrase,
                                            pos = tag,
                                            landmark_context = lmk_ctx)
            valid = Word.query.filter_by(phrase = phrase,
                                         pos = tag,
                                         landmark_context = lmk_ctx,
                                         word = word)
        factor = valid.count() / possible.count()
        if factor == 0.0: return 0.0
        else: prob *= factor
    return prob

def get_sentence_posteriors(sentence, iters):
    probs = []
    meanings = []
    rel_words, lmk_words, rel_phrases, lmk_phrases = get_parse(sentence)
    for j in range(iters):
        meaning, rel_ctx, lmk_ctx, ctx = try_meaning()
        r_exp_prob = get_expansions_prob(rel_ctx, lmk_ctx, ctx, 'rel', rel_phrases)
        l_exp_prob = get_expansions_prob(rel_ctx, lmk_ctx, ctx, 'lmk', lmk_phrases)
        r_w_prob = get_words_prob(rel_ctx, lmk_ctx, ctx, 'rel', rel_words)
        l_w_prob = get_words_prob(rel_ctx, lmk_ctx, ctx, 'lmk', lmk_words)
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
   posteriors = get_sentence_posteriors(sentence,iters)
   print_posteriors(posteriors)
