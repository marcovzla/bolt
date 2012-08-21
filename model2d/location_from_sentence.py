#!/usr/bin/env python
# coding: utf-8

from __future__ import division

from collections import defaultdict
from operator import itemgetter

import numpy as np
from nltk.tree import ParentedTree
from parse import get_modparse
from utils import (parent_landmark, get_meaning, lmk_id, rel_type, m2s,
                   count_lmk_phrases, NONTERMINALS)
from models import WordCPT, ExpansionCPT, CProduction, CWord



def uniquify_distribution(labels, probs):
    new_dist = defaultdict(float)
    for j in xrange(len(labels)):
        marker = str(labels[j])
        new_dist[marker] = probs[j]
    return new_dist.items()



def get_tree_prob(tree, lmk=None, rel=None):
    prob = 1.0

    if len(tree.productions()) == 1:
        # if this tree only has one production
        # it means that its child is a terminal (word)
        word = tree[0]
        pos = tree.node

        p = WordCPT.probability(word=word, pos=pos,
                                lmk=lmk_id(lmk), rel=rel_type(rel))
        print p, pos, '->', word, m2s(lmk,rel)
        prob *= p

    else:
        lhs = tree.node
        rhs = ' '.join(n.node for n in tree)
        parent = tree.parent.node if tree.parent else None

        if lhs == 'RELATION':
            # everything under a RELATION node should ignore the landmark
            lmk = None
        elif lhs == 'LANDMARK-PHRASE':
            # everything under a LANDMARK-PHRASE node should ignore the relation
            rel = None

            if parent == 'LANDMARK-PHRASE':
                # if the current node is a LANDMARK-PHRASE and the parent node
                # is also a LANDMARK-PHRASE then we should move to the parent
                # of the current landmark
                lmk = parent_landmark(lmk)

        if not parent:
            # LOCATION-PHRASE has no parent and is not related to lmk and rel
            p = ExpansionCPT.probability(rhs=rhs, lhs=lhs)
            print p, repr(lhs), '->', repr(rhs)
        else:
            p = ExpansionCPT.probability(rhs=rhs, lhs=lhs, parent=parent,
                                         lmk=lmk_id(lmk), rel=rel_type(rel))
            print p, repr(lhs), '->', repr(rhs), 'parent=%r'%parent, m2s(lmk,rel)
        prob *= p

        # call get_tree_prob recursively for each subtree
        for subtree in tree:
            prob *= get_tree_prob(subtree, lmk, rel)

    return prob

def get_tree_probs(tree, lmk=None, rel=None):

    # lhs_rhs_parent_chain = []
    prob_chain = []
    entropy_chain = []
    # terminals = []
    # rels_lmks = []


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

    # rels_lmks.append( (rel,lmk) )

    lmk_class = (lmk.object_class if lmk and lhs != 'LOCATION-PHRASE' else None)
    rel_class = rel_type(rel) if lhs != 'LOCATION-PHRASE' else None
    dist_class = (rel.measurement.best_distance_class if hasattr(rel, 'measurement') and lhs != 'LOCATION-PHRASE' else None)
    deg_class = (rel.measurement.best_degree_class if hasattr(rel, 'measurement') and lhs != 'LOCATION-PHRASE' else None)

    if lhs in NONTERMINALS:


        cp_db = CProduction.get_production_counts(lhs=lhs,
                                                  parent=parent,
                                                  lmk_class=lmk_class,
                                                  rel=rel_class,
                                                  dist_class=dist_class,
                                                  deg_class=deg_class)

        # if cp_db.count() <= 0:
        #     print 'Could not expand %s (parent: %s, lmk_class: %s, rel: %s, dist_class: %s, deg_class: %s)' % (n, parent, lmk_class, rel_class, dist_class, deg_class)
        #     terminals.append( n )
        #     continue

        ckeys, ccounts = zip(*[(cprod.rhs,cprod.count) for cprod in cp_db.all()])

        ccounter = {}
        for cprod in cp_db.all():
            if cprod.rhs in ccounter: ccounter[cprod.rhs] += cprod.count
            else: ccounter[cprod.rhs] = cprod.count

        ckeys, ccounts = zip(*ccounter.items())

        print 'ckeys', ckeys
        print 'ccounts', ccounts

        ccounts = np.array(ccounts, dtype=float)

        cprod_prob = ccounter[rhs]/ccounts.sum()
        cprod_entropy = -np.sum( (ccounts * np.log(ccounts)) )
        print rhs, cprod_prob, cprod_entropy

        # lhs_rhs_parent_chain.append( ( n,cprod,parent,(lmk.object_class if lmk else None) ) )
        prob_chain.append( cprod_prob )
        entropy_chain.append( cprod_entropy )

        # lrpc, pc, ec, t, ls = get_expansion( lhs=cprod, parent=n, lmk=lmk, rel=rel )
        # lhs_rhs_parent_chain.extend( lrpc )
        for subtree in tree:
            pc, ec = get_tree_probs(subtree, lmk, rel)
            prob_chain.extend( pc )
            entropy_chain.extend( ec )
            # rels_lmks.extend( rls )
        # terminals.extend( t )
        # landmarks.extend( ls )
    else:
        cw_db = CWord.get_word_counts(pos=lhs,
                                      lmk_class=lmk_class,
                                      rel=rel_class,
                                      rel_dist_class=dist_class,
                                      rel_deg_class=deg_class)

        # if cp_db.count() <= 0:
        #     print 'Could not expand %s (lmk_class: %s, rel: %s, dist_class: %s, deg_class: %s)' % (n, lmk_class, rel_class, dist_class, deg_class)
        #     terminals.append( n )
        #     continue

        ckeys, ccounts = zip(*[(cword.word,cword.count) for cword in cw_db.all()])

        ccounter = {}
        for cword in cw_db.all():
            if cword.word in ccounter: ccounter[cword.word] += cword.count
            else: ccounter[cword.word] = cword.count

        ckeys, ccounts = zip(*ccounter.items())

        print 'ckeys', ckeys
        print 'ccounts', ccounts

        ccounts = np.array(ccounts, dtype=float)

        # w, w_prob, w_entropy = categorical_sample(ckeys, ccounts)
        w_prob = ccounter[rhs]/ccounts.sum()
        w_entropy = -np.sum( (ccounts * np.log(ccounts)) )
        # words.append(w)
        prob_chain.append(w_prob)
        entropy_chain.append(w_entropy)

        # terminals.append( n )
        # landmarks.append( lmk )

    return prob_chain, entropy_chain#, rels_lmks

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
            ps, es = get_tree_probs(t, lmk, rel)
            # print "Tree probs: ", zip(ps,rls)
            meaning_probs[meaning] = np.prod(ps)
        print '.'

    if extra_meaning:
        meaning = m2s(*extra_meaning)
        if meaning not in meaning_probs:
            ps, es = get_tree_probs(t, lmk, rel)
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

    probs, entropies = get_tree_probs(t, lmk, rel)
    return np.prod(probs), sum(entropies)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('sentence')
    parser.add_argument('-i', '--iterations', type=int, default=1)
    args = parser.parse_args()

    posteriors = get_sentence_posteriors(args.sentence, args.iterations)

    for m,p in sorted(posteriors, key=itemgetter(1)):
        print 'Meaning: %s \t\t Probability: %0.4f' % (m,p)
