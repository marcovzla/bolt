#!/usr/bin/env python
# coding: utf-8

from __future__ import division

import sys
from operator import itemgetter

import utils
from utils import (get_meaning, categorical_sample, parent_landmark,
                   lmk_id, rel_type, m2s, count_lmk_phrases)
from models import Word, Production

from location_from_sentence import get_sentence_posteriors, get_sentence_meaning_likelihood
#import collections
import numpy as np

NONTERMINALS = ('LOCATION-PHRASE', 'RELATION', 'LANDMARK-PHRASE', 'LANDMARK')



def get_expansion(lhs, parent=None, lmk=None, rel=None):

    lhs_rhs_chain = []
    prob_chain = []
    entropy_chain = []
    terminals = []

    for n in lhs.split():
        if n in NONTERMINALS:
            if n == parent == 'LANDMARK-PHRASE':
                # we need to move to the parent landmark
                lmk = parent_landmark(lmk)
            # we need to keep expanding
            # rhs, rhs_prob, rhs_ent = get_expansion(n, parent, lmk, rel)

            p_db = Production.get_productions(lhs=n, parent=parent,
                                              lmk=lmk_id(lmk), rel=rel_type(rel))
                                              
            counter = {}
            for prod in p_db.all():
                rhs = str(prod.rhs)
                if rhs in counter: counter[rhs] += 1
                else: counter[rhs] = 1

            #counter = collections.Counter(p_db)
            keys, counts = zip(*counter.items())
            counts = np.array(counts, dtype=float)
            counts /= counts.sum()
            
            prod, prod_prob, prod_entropy = categorical_sample(keys, counts)
            print prod, prod_prob, prod_entropy
            
            lhs_rhs_chain.append( (n,prod) )
            prob_chain.append( prod_prob )
            entropy_chain.append( prod_entropy )
            
            lrc, pc, ec, t = get_expansion( lhs=prod, parent=n, lmk=lmk, rel=rel )
            lhs_rhs_chain.extend( lrc )
            prob_chain.extend( pc )
            entropy_chain.extend( ec )
            terminals.extend( t )
        else:
            terminals.append( n )
    
    return lhs_rhs_chain, prob_chain, entropy_chain, terminals

def remove_expansion(limit, lhs, rhs, parent=None, lmk=None, rel=None):
    return Production.delete_productions(limit, lhs=lhs, rhs=rhs, parent=parent,
                                  lmk=lmk_id(lmk), rel=rel_type(rel))

def get_words(terminals, lmk=None, rel=None):
    words = []
    probs = []
    entropy = []

    for n in terminals:
        # get word for POS
        w_db = Word.get_words(pos=n, lmk=lmk_id(lmk), rel=rel_type(rel))

        counter = {}
        for w in w_db:
            w = w.word
            if w in counter: counter[w] += 1
            else: counter[w] = 1
            
        #counter = collections.Counter(w_db)
        keys, counts = zip(*counter.items())
        counts = np.array(counts, dtype=float)
        counts /= counts.sum()
        
        w, w_prob, w_entropy = categorical_sample(keys, counts)
        words.append(w)
        probs.append(w_prob)
        entropy.append(w_entropy)
        
    p, H = np.prod(probs), np.sum(entropy)
    print 'expanding %s to %s (p: %f, H: %f)' % (terminals, words, p, H)
    return words, p, H
    
def delete_word(limit, terminals, words, lmk=None, rel=None):

    num_deleted = []
    for term, word in zip(terminals, words):
        # get word for POS
        num_deleted.append( Word.delete_words(limit, pos=term, word=word, lmk=lmk_id(lmk), rel=rel_type(rel)) )
    return num_deleted

class Meaning(object):
    def __init__(self, args):
        self.args = args


def generate_sentence(loc, consistent, scene=None):
    utils.scene = utils.ModelScene(scene)
    
    while True:
        (lmk, lmk_prob, lmk_ent), (rel, rel_prob, rel_ent) = get_meaning(loc=loc)
        print m2s(lmk, rel)
        rel_exp_chain, rele_prob_chain, rele_ent_chain, rel_terminals = get_expansion('RELATION', rel=rel)
        lmk_exp_chain, lmke_prob_chain, lmke_ent_chain, lmk_terminals = get_expansion('LANDMARK-PHRASE', lmk=lmk)
        rel_words, relw_prob, relw_ent = get_words(rel_terminals, rel=rel)
        lmk_words, lmkw_prob, lmkw_ent = get_words(lmk_terminals, lmk=lmk)
        sentence = ' '.join(rel_words + lmk_words)

        meaning = Meaning((lmk, lmk_prob, lmk_ent,
                       rel, rel_prob, rel_ent,
                       rel_exp_chain, rele_prob_chain, rele_ent_chain, rel_terminals,
                       lmk_exp_chain, lmke_prob_chain, lmke_ent_chain, lmk_terminals,
                       rel_words, relw_prob, relw_ent,
                       lmk_words, lmkw_prob, lmkw_ent))
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
                       rel, rel_prob, rel_ent,
                       rel_exp_chain, rele_prob_chain, rele_ent_chain, rel_terminals,
                       lmk_exp_chain, lmke_prob_chain, lmke_ent_chain, lmk_terminals,
                       rel_words, relw_prob, relw_ent,
                       lmk_words, lmkw_prob, lmkw_ent) = meaning.args
    
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
