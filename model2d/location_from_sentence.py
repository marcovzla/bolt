#!/usr/bin/env python
# coding: utf-8

from __future__ import division

from collections import defaultdict

import numpy as np
from nltk.tree import ParentedTree
from parse import get_modparse
from utils import ModelScene, parent_landmark
from models import WordCPT, ExpansionCPT

scene = ModelScene()



def lmk_id(lmk):
    if lmk: return scene.get_landmark_id(lmk)

def rel_type(rel):
    if rel: return rel.__class__.__name__

def count_lmk_phrases(t):
    return sum(1 for n in t.subtrees() if n.node == 'LANDMARK-PHRASE')

def m2s(lmk, rel):
    return '<lmk=%s(%s), rel=%s>' % (repr(lmk), lmk_id(lmk), rel_type(rel))




def try_meaning(num_ancestors=None):
    # get a random location on the table
    loc = scene.get_rand_loc()
    # sample landmark and relation for location
    lmk, rel = scene.sample_lmk_rel(loc, num_ancestors)
    return lmk, rel



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

        for subtree in tree:
            prob *= get_tree_prob(subtree, lmk, rel)

    return prob



def get_sentence_posteriors(sentence, iterations):
    probs = []
    meanings = []

    # parse sentence with charniak and apply surgeries
    print 'parsing ...'
    modparse = get_modparse(sentence)
    t = ParentedTree.parse(modparse)
    num_ancestors = count_lmk_phrases(t) - 1

    for _ in xrange(iterations):
        meaning = try_meaning(num_ancestors)
        lmk, rel = meaning
        probs.append(get_tree_prob(t, *meaning))
        meanings.append(m2s(lmk,rel))
        print '.'

    probs = np.array(probs) / sum(probs)
    return uniquify_distribution(meanings,  probs)




if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('sentence')
    parser.add_argument('-i', '--iterations', type=int, default=1)
    args = parser.parse_args()

    posteriors = get_sentence_posteriors(args.sentence, args.iterations)

    for m,p in posteriors:
        print 'Meaning: %s \t\t Probability: %0.4f' % (m,p)
