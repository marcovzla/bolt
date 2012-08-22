#!/usr/bin/env python
# coding: utf-8

from __future__ import division

import sys
from operator import itemgetter

import utils
from utils import (get_meaning, categorical_sample, parent_landmark,
                   lmk_id, rel_type, m2s, get_lmk_ori_rels_str, NONTERMINALS)
from models import Word, Production, CProduction, CWord

from location_from_sentence import get_sentence_posteriors, get_sentence_meaning_likelihood

import numpy as np

np.seterr(all='raise')

def get_expansion(lhs, parent=None, lmk=None, rel=None):
    lhs_rhs_parent_chain = []
    prob_chain = []
    entropy_chain = []
    terminals = []
    landmarks = []

    for n in lhs.split():
        if n in NONTERMINALS:
            if n == parent == 'LANDMARK-PHRASE':
                # we need to move to the parent landmark
                lmk = parent_landmark(lmk)

            lmk_class = (lmk.object_class if lmk else None)
            lmk_ori_rels = get_lmk_ori_rels_str(lmk)
            rel_class = rel_type(rel)
            dist_class = (rel.measurement.best_distance_class if hasattr(rel, 'measurement') else None)
            deg_class = (rel.measurement.best_degree_class if hasattr(rel, 'measurement') else None)

            cp_db = CProduction.get_production_counts(lhs=n,
                                                      parent=parent,
                                                      lmk_class=lmk_class,
                                                      lmk_ori_rels=lmk_ori_rels,
                                                      rel=rel_class,
                                                      dist_class=dist_class,
                                                      deg_class=deg_class)

            if cp_db.count() <= 0:
                print 'Could not expand %s (parent: %s, lmk_class: %s, rel: %s, dist_class: %s, deg_class: %s)' % (n, parent, lmk_class, rel_class, dist_class, deg_class)
                terminals.append( n )
                continue

            ckeys, ccounts = zip(*[(cprod.rhs,cprod.count) for cprod in cp_db.all()])

            ccounter = {}
            for cprod in cp_db.all():
                if cprod.rhs in ccounter: ccounter[cprod.rhs] += cprod.count
                else: ccounter[cprod.rhs] = cprod.count

            ckeys, ccounts = zip(*ccounter.items())

            print 'ckeys', ckeys
            print 'ccounts', ccounts

            ccounts = np.array(ccounts, dtype=float)
            ccounts /= ccounts.sum()

            cprod, cprod_prob, cprod_entropy = categorical_sample(ckeys, ccounts)
            print cprod, cprod_prob, cprod_entropy

            lhs_rhs_parent_chain.append( ( n,cprod,parent,lmk ) )
            prob_chain.append( cprod_prob )
            entropy_chain.append( cprod_entropy )

            lrpc, pc, ec, t, ls = get_expansion( lhs=cprod, parent=n, lmk=lmk, rel=rel )
            lhs_rhs_parent_chain.extend( lrpc )
            prob_chain.extend( pc )
            entropy_chain.extend( ec )
            terminals.extend( t )
            landmarks.extend( ls )
        else:
            terminals.append( n )
            landmarks.append( lmk )

    return lhs_rhs_parent_chain, prob_chain, entropy_chain, terminals, landmarks

def remove_expansion(limit, lhs, rhs, parent=None, lmk=None, rel=None):
    return Production.delete_productions(limit, lhs=lhs, rhs=rhs, parent=parent,
                                  lmk=lmk_id(lmk), rel=rel_type(rel))

def update_expansion_counts(update, lhs, rhs, parent=None, lmk_class=None, lmk_ori_rels=None, rel=None):
    CProduction.update_production_counts(update=update,
                                         lhs=lhs,
                                         rhs=rhs,
                                         parent=parent,
                                         lmk_class=(lmk_class if lmk_class else None),
                                         lmk_ori_rels=lmk_ori_rels,
                                         rel=rel_type(rel),
                                         dist_class=(rel.measurement.best_distance_class if hasattr(rel, 'measurement') else None),
                                         deg_class=(rel.measurement.best_degree_class if hasattr(rel, 'measurement') else None))

def update_word_counts(update, pos, word, lmk_class=None, lmk_ori_rels=None, rel=None):
    CWord.update_word_counts(update=update,
                             pos=pos,
                             word=word,
                             lmk_class=(lmk_class if lmk_class else None),
                             lmk_ori_rels=lmk_ori_rels,
                             rel=rel_type(rel),
                             rel_dist_class=(rel.measurement.best_distance_class if hasattr(rel, 'measurement') else None),
                             rel_deg_class=(rel.measurement.best_degree_class if hasattr(rel, 'measurement') else None))

def get_words(terminals, landmarks, rel=None):
    words = []
    probs = []
    entropy = []

    for n,lmk in zip(terminals, landmarks):
        # if we could not get an expansion for the LHS, we just pass down the unexpanded nonterminal symbol
        # it gets the probability of 1 and entropy of 0
        if n in NONTERMINALS:
            words.append(n)
            probs.append(1.0)
            entropy.append(0.0)
            continue

        lmk_class = (lmk.object_class if lmk else None)
        rel_class = rel_type(rel)
        dist_class = (rel.measurement.best_distance_class if hasattr(rel, 'measurement') else None)
        deg_class = (rel.measurement.best_degree_class if hasattr(rel, 'measurement') else None)

        cp_db = CWord.get_word_counts(pos=n,
                                      lmk_class=lmk_class,
                                      lmk_ori_rels=get_lmk_ori_rels_str(lmk),
                                      rel=rel_class,
                                      rel_dist_class=dist_class,
                                      rel_deg_class=deg_class)

        if cp_db.count() <= 0:
            print 'Could not expand %s (lmk_class: %s, rel: %s, dist_class: %s, deg_class: %s)' % (n, lmk_class, rel_class, dist_class, deg_class)
            terminals.append( n )
            continue

        ckeys, ccounts = zip(*[(cword.word,cword.count) for cword in cp_db.all()])

        ccounter = {}
        for cword in cp_db.all():
            if cword.word in ccounter: ccounter[cword.word] += cword.count
            else: ccounter[cword.word] = cword.count

        ckeys, ccounts = zip(*ccounter.items())

        print 'ckeys', ckeys
        print 'ccounts', ccounts

        ccounts = np.array(ccounts, dtype=float)
        ccounts /= ccounts.sum()

        w, w_prob, w_entropy = categorical_sample(ckeys, ccounts)
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

    (lmk, lmk_prob, lmk_ent), (rel, rel_prob, rel_ent) = get_meaning(loc=loc)
    meaning1 = m2s(lmk, rel)
    print meaning1

    while True:
        rel_exp_chain, rele_prob_chain, rele_ent_chain, rel_terminals, rel_landmarks = get_expansion('RELATION', rel=rel)
        lmk_exp_chain, lmke_prob_chain, lmke_ent_chain, lmk_terminals, lmk_landmarks = get_expansion('LANDMARK-PHRASE', lmk=lmk)
        rel_words, relw_prob, relw_ent = get_words(rel_terminals, landmarks=rel_landmarks, rel=rel)
        lmk_words, lmkw_prob, lmkw_ent = get_words(lmk_terminals, landmarks=lmk_landmarks)
        sentence = ' '.join(rel_words + lmk_words)

        print 'rel_exp_chain', rel_exp_chain
        print 'lmk_exp_chain', lmk_exp_chain

        meaning = Meaning((lmk, lmk_prob, lmk_ent,
                           rel, rel_prob, rel_ent,
                           rel_exp_chain, rele_prob_chain, rele_ent_chain, rel_terminals, rel_landmarks,
                           lmk_exp_chain, lmke_prob_chain, lmke_ent_chain, lmk_terminals, lmk_landmarks,
                           rel_words, relw_prob, relw_ent,
                           lmk_words, lmkw_prob, lmkw_ent))

        if consistent:
             # get the most likely meaning for the generated sentence
            try:
                posteriors = get_sentence_posteriors(sentence, iterations=10, extra_meaning=(lmk,rel))
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

        return meaning, sentence


def confidence(p, H):
    return (H + np.log(p)) / H


def accept_correction( meaning, correction ):
    (lmk, lmk_prob, lmk_ent,
     rel, rel_prob, rel_ent,
     rel_exp_chain, rele_prob_chain, rele_ent_chain, rel_terminals, rel_landmarks,
     lmk_exp_chain, lmke_prob_chain, lmke_ent_chain, lmk_terminals, lmk_landmarks,
     rel_words, relw_prob, relw_ent,
     lmk_words, lmkw_prob, lmkw_ent) = meaning.args

    old_meaning_prob, old_meaning_entropy, lrpc, tps = get_sentence_meaning_likelihood( correction, lmk, rel )

    scale = 10
    learning_factor = 1000
    c1 = confidence(lmk_prob * rel_prob, lmk_ent + rel_ent)
    c2 = confidence(old_meaning_prob, old_meaning_entropy)

    if c1 + c2 <= 0: return # update the semantics

    update = (c1 + c2) * scale * learning_factor
    print 'lmk_prob, lmk_ent, rel_prob, rel_ent, old_meaning_prob, old_meaning_entropy, c1, c2, update', lmk_prob, lmk_ent, rel_prob, rel_ent, old_meaning_prob, old_meaning_entropy, c1, c2, update
    print lmk.object_class, type(rel)

    dec_update = -update

    for lhs,rhs,parent,_ in rel_exp_chain:
        print 'Decrementing production - lhs: %s, rhs: %s, parent: %s' % (lhs,rhs,parent)
        update_expansion_counts( dec_update, lhs, rhs, parent, rel=rel )

    for lhs,rhs,parent,lmk in lmk_exp_chain:
        print 'Decrementing production - lhs: %s, rhs: %s, parent: %s' % (lhs,rhs,parent)
        update_expansion_counts( dec_update, lhs, rhs, parent, lmk_class=(lmk.object_class if lmk else None), lmk_ori_rels=get_lmk_ori_rels_str(lmk) )

    for term,word in zip(rel_terminals,rel_words):
        print 'Decrementing word - pos: %s, word: %s, rel: %s' % (term, word, rel)
        update_word_counts( dec_update, term, word, rel=rel )

    for term,word,lmk in zip(lmk_terminals,lmk_words,lmk_landmarks):
        print 'Decrementing word - pos: %s, word: %s, lmk_class: %s' % (term, word, lmk.object_class)
        update_word_counts( dec_update, term, word, lmk_class=lmk.object_class, lmk_ori_rels=get_lmk_ori_rels_str(lmk) )

    # reward new words with old meaning
    for lhs,rhs,parent,lmk,rel in lrpc:
        print 'Incrementing production - lhs: %s, rhs: %s, parent: %s' % (lhs,rhs,parent)
        update_expansion_counts( update, lhs, rhs, parent, rel=rel, lmk_class=(lmk.object_class if lmk else None), lmk_ori_rels=get_lmk_ori_rels_str(lmk) )

    for lhs,rhs,lmk,rel in tps:
        print 'Incrementing word - pos: %s, word: %s, lmk_class: %s' % (lhs, rhs, (lmk.object_class if lmk else None) )
        update_word_counts( update, lhs, rhs, lmk_class=(lmk.object_class if lmk else None), rel=rel, lmk_ori_rels=get_lmk_ori_rels_str(lmk) )


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

    meaning, sentence = generate_sentence(args.location.xy, args.consistent)
    print 'sentence:', sentence
    correction = raw_input('Correction? ')
    accept_correction( meaning, correction)
