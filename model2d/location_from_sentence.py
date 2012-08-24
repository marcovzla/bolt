#!/usr/bin/env python
# coding: utf-8

from __future__ import division

from operator import itemgetter

import numpy as np
from nltk.tree import ParentedTree
from parse import get_modparse
from utils import (parent_landmark,
                   get_meaning,
                   rel_type,
                   m2s,
                   count_lmk_phrases,
                   logger,
                   get_lmk_ori_rels_str,
                   NONTERMINALS)
from models import CProduction, CWord




def get_tree_probs(tree, lmk=None, rel=None):
    lhs_rhs_parent_chain = []
    prob_chain = []
    entropy_chain = []
    term_prods = []

    lhs = tree.node

    if isinstance(tree[0], ParentedTree): rhs = ' '.join(n.node for n in tree)
    else: rhs = ' '.join(n for n in tree)

    parent = tree.parent.node if tree.parent else None

    if lhs == 'RELATION':
        # everything under a RELATION node should ignore the landmark
        lmk = None

    if lhs == 'LANDMARK-PHRASE':
        # everything under a LANDMARK-PHRASE node should ignore the relation
        rel = None

    if lhs == parent == 'LANDMARK-PHRASE':
        # we need to move to the parent landmark
        lmk = parent_landmark(lmk)

    lmk_class = (lmk.object_class if lmk and lhs != 'LOCATION-PHRASE' else None)
    lmk_ori_rels = get_lmk_ori_rels_str(lmk) if lhs != 'LOCATION-PHRASE' else None
    lmk_color = (lmk.color if lmk and lhs != 'LOCATION-PHRASE' else None)
    rel_class = rel_type(rel) if lhs != 'LOCATION-PHRASE' else None
    dist_class = (rel.measurement.best_distance_class if hasattr(rel, 'measurement') and lhs != 'LOCATION-PHRASE' else None)
    deg_class = (rel.measurement.best_degree_class if hasattr(rel, 'measurement') and lhs != 'LOCATION-PHRASE' else None)

    if lhs in NONTERMINALS:
        cp_db = CProduction.get_production_counts(lhs=lhs,
                                                  parent=parent,
                                                  lmk_class=lmk_class,
                                                  lmk_ori_rels=lmk_ori_rels,
                                                  lmk_color=lmk_color,
                                                  rel=rel_class,
                                                  dist_class=dist_class,
                                                  deg_class=deg_class)

        if cp_db.count() <= 0:
            logger('Could not expand %s (parent: %s, lmk_class: %s, lmk_ori_rels: %s, lmk_color: %s, rel: %s, dist_class: %s, deg_class: %s)' % (lhs, parent, lmk_class, lmk_ori_rels, lmk_color, rel_class, dist_class, deg_class))
        else:
            ckeys, ccounts = zip(*[(cprod.rhs,cprod.count) for cprod in cp_db.all()])

            ccounter = {}
            for cprod in cp_db.all():
                if cprod.rhs in ccounter: ccounter[cprod.rhs] += cprod.count
                else: ccounter[cprod.rhs] = cprod.count + 1

            # we have never seen this RHS in this context before
            if rhs not in ccounter: ccounter[rhs] = 1

            ckeys, ccounts = zip(*ccounter.items())

            # add 1 smoothing
            ccounts = np.array(ccounts, dtype=float)
            ccount_probs = ccounts / ccounts.sum()
            cprod_entropy = -np.sum( (ccount_probs * np.log(ccount_probs)) )
            cprod_prob = ccounter[rhs]/ccounts.sum()

            # logger('ckeys: %s' % str(ckeys))
            # logger('ccounts: %s' % str(ccounts))
            # logger('rhs: %s, cprod_prob: %s, cprod_entropy: %s' % (rhs, cprod_prob, cprod_entropy))

            prob_chain.append( cprod_prob )
            entropy_chain.append( cprod_entropy )

        lhs_rhs_parent_chain.append( ( lhs, rhs, parent, lmk, rel ) )

        for subtree in tree:
            pc, ec, lrpc, tps = get_tree_probs(subtree, lmk, rel)
            prob_chain.extend( pc )
            entropy_chain.extend( ec )
            lhs_rhs_parent_chain.extend( lrpc )
            term_prods.extend( tps )

    else:
        cw_db = CWord.get_word_counts(pos=lhs,
                                      lmk_class=lmk_class,
                                      lmk_ori_rels=lmk_ori_rels,
                                      lmk_color=lmk_color,
                                      rel=rel_class,
                                      rel_dist_class=dist_class,
                                      rel_deg_class=deg_class)

        if cw_db.count() <= 0:
            # we don't know the probability or entropy values for the context we have never seen before
            # we just update the term_prods list
            logger('Could not expand %s (lmk_class: %s, lmk_ori_rels: %s, lmk_color: %s, rel: %s, dist_class: %s, deg_class: %s)' % (lhs, lmk_class, lmk_ori_rels, lmk_color, rel_class, dist_class, deg_class))
        else:

            ckeys, ccounts = zip(*[(cword.word,cword.count) for cword in cw_db.all()])

            ccounter = {}
            for cword in cw_db.all():
                if cword.word in ccounter: ccounter[cword.word] += cword.count
                else: ccounter[cword.word] = cword.count + 1

            # we have never seen this RHS in this context before
            if rhs not in ccounter: ccounter[rhs] = 1

            ckeys, ccounts = zip(*ccounter.items())

            # logger('ckeys: %s' % str(ckeys))
            # logger('ccounts: %s' % str(ccounts))

            # add 1 smoothing
            ccounts = np.array(ccounts, dtype=float)
            ccount_probs = ccounts/ccounts.sum()

            w_prob = ccounter[rhs]/ccounts.sum()
            w_entropy = -np.sum( (ccount_probs * np.log(ccount_probs)) )

            prob_chain.append(w_prob)
            entropy_chain.append(w_entropy)

        term_prods.append( (lhs, rhs, lmk, rel) )

    return prob_chain, entropy_chain, lhs_rhs_parent_chain, term_prods

def get_sentence_posteriors(sentence, iterations=1, extra_meaning=None):
    meaning_probs = {}
    # parse sentence with charniak and apply surgeries
    print 'parsing ...'
    modparse = get_modparse(sentence)
    t = ParentedTree.parse(modparse)
    print '\n%s\n' % t.pprint()
    num_ancestors = count_lmk_phrases(t) - 1

    for _ in xrange(iterations):
        (lmk, _, _), (rel, _, _) = get_meaning(num_ancestors=num_ancestors)
        meaning = m2s(lmk,rel)
        if meaning not in meaning_probs:
            ps = get_tree_probs(t, lmk, rel)[0]
            # print "Tree probs: ", zip(ps,rls)
            meaning_probs[meaning] = np.prod(ps)
        print '.'

    if extra_meaning:
        meaning = m2s(*extra_meaning)
        if meaning not in meaning_probs:
            ps = get_tree_probs(t, lmk, rel)[0]
            # print "Tree prob: ", zip(ps,rls)
            meaning_probs[meaning] = np.prod(ps)
        print '.'

    summ = sum(meaning_probs.values())
    for key in meaning_probs:
        meaning_probs[key] /= summ
    return meaning_probs.items()

def get_sentence_meaning_likelihood(sentence, lmk, rel):
    modparse = get_modparse(sentence)
    t = ParentedTree.parse(modparse)
    print '\n%s\n' % t.pprint()

    probs, entropies, lrpc, tps = get_tree_probs(t, lmk, rel)
    if np.prod(probs) == 0.0:
        logger('ERROR: Probability product is 0 for sentence: %s, lmk: %s, rel: %s, probs: %s' % (sentence, lmk, rel, str(probs)))
    return np.prod(probs), sum(entropies), lrpc, tps


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('sentence')
    parser.add_argument('-i', '--iterations', type=int, default=1)
    args = parser.parse_args()

    posteriors = get_sentence_posteriors(args.sentence, args.iterations)

    for m,p in sorted(posteriors, key=itemgetter(1)):
        print 'Meaning: %s \t\t Probability: %0.4f' % (m,p)
