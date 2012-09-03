#!/usr/bin/env python
# coding: utf-8

from __future__ import division

from operator import itemgetter

import utils
from utils import (get_meaning,
                   categorical_sample,
                   parent_landmark,
                   lmk_id,
                   rel_type,
                   m2s,
                   get_lmk_ori_rels_str,
                   logger,
                   NONTERMINALS)
from models import Word, Production, CProduction, CWord

from location_from_sentence import get_sentence_posteriors, get_sentence_meaning_likelihood
from table2d.run import construct_training_scene

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
            lmk_color = (lmk.color if lmk else None)
            rel_class = rel_type(rel)
            dist_class = (rel.measurement.best_distance_class if hasattr(rel, 'measurement') else None)
            deg_class = (rel.measurement.best_degree_class if hasattr(rel, 'measurement') else None)

            cp_db = CProduction.get_production_counts(lhs=n,
                                                      parent=parent,
                                                      lmk_class=lmk_class,
                                                      lmk_ori_rels=lmk_ori_rels,
                                                      lmk_color=lmk_color,
                                                      rel=rel_class,
                                                      dist_class=dist_class,
                                                      deg_class=deg_class)

            if cp_db.count() <= 0:
                logger('Could not expand %s (parent: %s, lmk_class: %s, lmk_ori_rels: %s, lmk_color: %s, rel: %s, dist_class: %s, deg_class: %s)' % (n, parent, lmk_class, lmk_ori_rels, lmk_color, rel_class, dist_class, deg_class))
                terminals.append( n )
                continue

            ckeys, ccounts = zip(*[(cprod.rhs,cprod.count) for cprod in cp_db.all()])

            ccounter = {}
            for cprod in cp_db.all():
                if cprod.rhs in ccounter: ccounter[cprod.rhs] += cprod.count
                else: ccounter[cprod.rhs] = cprod.count

            ckeys, ccounts = zip(*ccounter.items())

            # print 'ckeys', ckeys
            # print 'ccounts', ccounts

            ccounts = np.array(ccounts, dtype=float)
            ccounts /= ccounts.sum()

            cprod, cprod_prob, cprod_entropy = categorical_sample(ckeys, ccounts)
            # print cprod, cprod_prob, cprod_entropy

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

def update_expansion_counts(update, lhs, rhs, parent=None, lmk_class=None, lmk_ori_rels=None, lmk_color=None, rel=None):
    CProduction.update_production_counts(update=update,
                                         lhs=lhs,
                                         rhs=rhs,
                                         parent=parent,
                                         lmk_class=lmk_class,
                                         lmk_ori_rels=lmk_ori_rels,
                                         lmk_color=lmk_color,
                                         rel=rel_type(rel),
                                         dist_class=(rel.measurement.best_distance_class if hasattr(rel, 'measurement') else None),
                                         deg_class=(rel.measurement.best_degree_class if hasattr(rel, 'measurement') else None))

def update_word_counts(update, pos, word, prev_word='<no prev word>', lmk_class=None, lmk_ori_rels=None, lmk_color=None, rel=None):
    CWord.update_word_counts(update=update,
                             pos=pos,
                             word=word,
                             prev_word=prev_word,
                             lmk_class=lmk_class,
                             lmk_ori_rels=lmk_ori_rels,
                             lmk_color=lmk_color,
                             rel=rel_type(rel),
                             rel_dist_class=(rel.measurement.best_distance_class if hasattr(rel, 'measurement') else None),
                             rel_deg_class=(rel.measurement.best_degree_class if hasattr(rel, 'measurement') else None))

def get_words(terminals, landmarks, rel=None, prevword=None):
    words = []
    probs = []
    alphas = []
    entropy = []
    C = CWord.get_count

    for n,lmk in zip(terminals, landmarks):
        # if we could not get an expansion for the LHS, we just pass down the unexpanded nonterminal symbol
        # it gets the probability of 1 and entropy of 0
        if n in NONTERMINALS:
            words.append(n)
            probs.append(1.0)
            entropy.append(0.0)
            continue

        lmk_class = (lmk.object_class if lmk else None)
        lmk_color = (lmk.color if lmk else None)
        rel_class = rel_type(rel)
        dist_class = (rel.measurement.best_distance_class if hasattr(rel, 'measurement') else None)
        deg_class = (rel.measurement.best_degree_class if hasattr(rel, 'measurement') else None)



        meaning = dict(pos=n,
                       lmk_class=lmk_class,
                       lmk_ori_rels=get_lmk_ori_rels_str(lmk),
                       lmk_color=lmk_color,
                       rel=rel_class,
                       rel_dist_class=dist_class,
                       rel_deg_class=deg_class)

        cp_db_uni = CWord.get_word_counts(**meaning)

        ccounter = {}
        for c in cp_db_uni:
            ccounter[c.word] = ccounter.get(c.word, 0) + c.count
        ckeys, ccounts_uni = zip(*ccounter.items())
        ccounts_uni = np.array(ccounts_uni, dtype=float)
        ccounts_uni /= ccounts_uni.sum()


        prev_word = words[-1] if words else prevword
        alpha = C(prev_word=prev_word, **meaning) / C(**meaning)
        alphas.append(alpha)

        if alpha:
            cp_db_bi = CWord.get_word_counts(prev_word=prev_word, **meaning)

            ccounter = {}
            for c in cp_db_bi:
                ccounter[c.word] = ccounter.get(c.word, 0) + c.count
            ccounts_bi = np.array([ccounter.get(k,0) for k in ckeys], dtype=float)
            ccounts_bi /= ccounts_bi.sum()

            cprob = (alpha * ccounts_bi) + ((1-alpha) * ccounts_uni)

        else:
            cprob = ccounts_uni


        # if cp_db.count() <= 0:
            # logger( 'Could not expand %s (lmk_class: %s, lmk_color: %s, rel: %s, dist_class: %s, deg_class: %s)' % (n, lmk_class, lmk_color, rel_class, dist_class, deg_class) )
            # terminals.append( n )
            # continue

        # ckeys, ccounts = zip(*[(cword.word,cword.count) for cword in cp_db.all()])

        # ccounter = {}
        # for cword in cp_db.all():
        #     if cword.word in ccounter: ccounter[cword.word] += cword.count
        #     else: ccounter[cword.word] = cword.count

        # ckeys, ccounts = zip(*ccounter.items())

        # print 'ckeys', ckeys
        # print 'ccounts', ccounts

        # ccounts = np.array(ccounts, dtype=float)
        # ccounts /= ccounts.sum()

        w, w_prob, w_entropy = categorical_sample(ckeys, cprob)
        words.append(w)
        probs.append(w_prob)
        entropy.append(w_entropy)

    p, H = np.prod(probs), np.sum(entropy)
    # print 'expanding %s to %s (p: %f, H: %f)' % (terminals, words, p, H)
    return words, p, H, alphas

def delete_word(limit, terminals, words, lmk=None, rel=None):

    num_deleted = []
    for term, word in zip(terminals, words):
        # get word for POS
        num_deleted.append( Word.delete_words(limit, pos=term, word=word, lmk=lmk_id(lmk), rel=rel_type(rel)) )
    return num_deleted

class Meaning(object):
    def __init__(self, args):
        self.args = args


def generate_sentence(loc, consistent, scene=None, speaker=None):
    utils.scene = utils.ModelScene(scene, speaker)

    (lmk, lmk_prob, lmk_ent), (rel, rel_prob, rel_ent) = get_meaning(loc=loc)
    meaning1 = m2s(lmk, rel)
    logger( meaning1 )

    while True:
        rel_exp_chain, rele_prob_chain, rele_ent_chain, rel_terminals, rel_landmarks = get_expansion('RELATION', rel=rel)
        lmk_exp_chain, lmke_prob_chain, lmke_ent_chain, lmk_terminals, lmk_landmarks = get_expansion('LANDMARK-PHRASE', lmk=lmk)
        rel_words, relw_prob, relw_ent, rel_a = get_words(rel_terminals, landmarks=rel_landmarks, rel=rel)
        lmk_words, lmkw_prob, lmkw_ent, lmk_a = get_words(lmk_terminals, landmarks=lmk_landmarks, prevword=(rel_words[-1] if rel_words else None))
        sentence = ' '.join(rel_words + lmk_words)

        logger( 'rel_exp_chain: %s' % rel_exp_chain )
        logger( 'lmk_exp_chain: %s' % lmk_exp_chain )

        meaning = Meaning((lmk, lmk_prob, lmk_ent,
                           rel, rel_prob, rel_ent,
                           rel_exp_chain, rele_prob_chain, rele_ent_chain, rel_terminals, rel_landmarks,
                           lmk_exp_chain, lmke_prob_chain, lmke_ent_chain, lmk_terminals, lmk_landmarks,
                           rel_words, relw_prob, relw_ent,
                           lmk_words, lmkw_prob, lmkw_ent))
        meaning.rel_a = rel_a
        meaning.lmk_a = lmk_a

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


def compute_update_sigmoid_confidence(p_gen, p_corr, H_gen, H_corr):
    deviation_gen  = (H_gen + np.log(p_gen)) / H_gen
    deviation_corr = (H_corr + np.log(p_corr)) / H_corr
    c_gen  = 1.0 / (1.0 + np.exp(-deviation_gen))
    c_corr = 1.0 / (1.0 + np.exp(-deviation_corr))
    return np.sqrt(c_gen * c_corr)


def compute_update_geometric(p_gen, p_corr, H_gen, H_corr):
    return np.sqrt(p_gen * p_corr)


update_funcs = {
    'sigmoid_confidence': compute_update_sigmoid_confidence,
    'geometric': compute_update_geometric,
}


def accept_correction( meaning, correction, update_func='geometric', update_scale=10 ):
    (lmk, lmk_prob, lmk_ent,
     rel, rel_prob, rel_ent,
     rel_exp_chain, rele_prob_chain, rele_ent_chain, rel_terminals, rel_landmarks,
     lmk_exp_chain, lmke_prob_chain, lmke_ent_chain, lmk_terminals, lmk_landmarks,
     rel_words, relw_prob, relw_ent,
     lmk_words, lmkw_prob, lmkw_ent) = meaning.args
    rel_a = meaning.rel_a
    lmk_a = meaning.lmk_a


    old_meaning_prob, old_meaning_entropy, lrpc, tps = get_sentence_meaning_likelihood( correction, lmk, rel )

    update = update_funcs[update_func](lmk_prob * rel_prob, old_meaning_prob, lmk_ent + rel_ent, old_meaning_entropy) * update_scale

    logger('Update functions is %s and update value is: %f' % (update_func, update))
    # print 'lmk_prob, lmk_ent, rel_prob, rel_ent, old_meaning_prob, old_meaning_entropy, update', lmk_prob, lmk_ent, rel_prob, rel_ent, old_meaning_prob, old_meaning_entropy, update
    # print lmk.object_class, type(rel)

    dec_update = -update

    for lhs,rhs,parent,_ in rel_exp_chain:
        # print 'Decrementing production - lhs: %s, rhs: %s, parent: %s' % (lhs,rhs,parent)
        update_expansion_counts( dec_update, lhs, rhs, parent, rel=rel )

    for lhs,rhs,parent,lmk in lmk_exp_chain:
        # print 'Decrementing production - lhs: %s, rhs: %s, parent: %s' % (lhs,rhs,parent)
        update_expansion_counts( dec_update, lhs, rhs, parent, lmk_class=(lmk.object_class if lmk else None),
                                                               lmk_ori_rels=get_lmk_ori_rels_str(lmk),
                                                               lmk_color=(lmk.color if lmk else None) )

    data = zip(rel_terminals, rel_words)
    for i in xrange(len(data)):
        term,word = data[i]
        prev_word = data[i-1][1] if i > 0 else None
        a = rel_a[i]
        # print 'Decrementing word - pos: %s, word: %s, rel: %s' % (term, word, rel)
        update_word_counts( (1-a)*dec_update, term, word, rel=rel )
        update_word_counts(a*dec_update, term, word, rel=rel, prev_word=prev_word)

    data = zip(lmk_terminals, lmk_words, lmk_landmarks)
    for i in xrange(len(data)):
        term, word, lmk = data[i]
        prev_word = data[i-1][1] if i > 0 else rel_words[-1]
        a = lmk_a[i]
        # print 'Decrementing word - pos: %s, word: %s, lmk_class: %s' % (term, word, lmk.object_class)
        update_word_counts((1-a)*dec_update, term, word, lmk_class=lmk.object_class,
                                                         lmk_ori_rels=get_lmk_ori_rels_str(lmk),
                                                         lmk_color=(lmk.color if lmk else None))
        update_word_counts( a*dec_update, term, word, prev_word, lmk_class=lmk.object_class,
                                                                 lmk_ori_rels=get_lmk_ori_rels_str(lmk),
                                                                 lmk_color=(lmk.color if lmk else None) )

    # reward new words with old meaning
    for lhs,rhs,parent,lmk,rel in lrpc:
        # print 'Incrementing production - lhs: %s, rhs: %s, parent: %s' % (lhs,rhs,parent)
        update_expansion_counts( update, lhs, rhs, parent, rel=rel,
                                                           lmk_class=(lmk.object_class if lmk else None),
                                                           lmk_ori_rels=get_lmk_ori_rels_str(lmk),
                                                           lmk_color=(lmk.color if lmk else None) )

    for i in xrange(len(tps)):
        lhs,rhs,lmk,rel = tps[i]
        prev_word = tps[i-1][1] if i > 0 else None
        # print 'Incrementing word - pos: %s, word: %s, lmk_class: %s' % (lhs, rhs, (lmk.object_class if lmk else None) )
        update_word_counts( update, lhs, rhs, prev_word, lmk_class=(lmk.object_class if lmk else None),
                                                         rel=rel,
                                                         lmk_ori_rels=get_lmk_ori_rels_str(lmk),
                                                         lmk_color=(lmk.color if lmk else None) )


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

    scene, speaker = construct_training_scene()
    meaning, sentence = generate_sentence(args.location.xy, args.consistent, scene, speaker)
    logger('Generated sentence: %s' % sentence)
    correction = raw_input('Correction? ')
    accept_correction( meaning, correction)
