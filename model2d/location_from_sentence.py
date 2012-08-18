#!/usr/bin/env python
# coding: utf-8

from __future__ import division

from collections import defaultdict
from operator import itemgetter

import numpy as np
from nltk.tree import ParentedTree
from parse import get_modparse
from utils import (parent_landmark, get_meaning, lmk_id, rel_type, m2s,
                   count_lmk_phrases)
from models import WordCPT, ExpansionCPT



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



def get_sentence_posteriors(sentence, iterations=1, extra_meaning=None):
    probs = []
    meanings = []

    # parse sentence with charniak and apply surgeries
    print 'parsing ...'
    modparse = get_modparse(sentence)
    t = ParentedTree.parse(modparse)
    print '\n%s\n' % t.pprint()
    num_ancestors = count_lmk_phrases(t) - 1

    for _ in xrange(iterations):
        meaning = get_meaning(num_ancestors=num_ancestors)
        probs.append(get_tree_prob(t, *meaning))
        meanings.append(m2s(*meaning))
        print '.'

    if extra_meaning:
        probs.append(get_tree_prob(t, *extra_meaning))
        meanings.append(m2s(*extra_meaning))
        print '.'

    probs = np.array(probs) / sum(probs)
    return uniquify_distribution(meanings,  probs)

def get_sentence_meaning_likelihood(sentence, lmk, rel):
    modparse = get_modparse(sentence)
    t = ParentedTree.parse(modparse)
    print '\n%s\n' % t.pprint()

    return get_tree_prob(t, lmk, rel)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('sentence')
    parser.add_argument('-i', '--iterations', type=int, default=1)
    args = parser.parse_args()

    posteriors = get_sentence_posteriors(args.sentence, args.iterations)

    for m,p in sorted(posteriors, key=itemgetter(1)):
        print 'Meaning: %s \t\t Probability: %0.4f' % (m,p)
