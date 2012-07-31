#!/usr/bin/env python
# coding: utf-8

from __future__ import division

import csv

from models import Location, Word, Production, Bigram, Trigram, session
from utils import ModelScene, parent_landmark

from table2d.landmark import Landmark

from nltk.tree import ParentedTree



def count_lmk_phrases(t):
    return sum(1 for n in t.subtrees() if n.node == 'LANDMARK-PHRASE')



def save_tree(tree, loc, rel, lmk, scene, parent=None):
    if len(tree.productions()) == 1:
        # if this tree only has one production
        # it means that its child is a terminal (word)
        word = Word()
        word.word = tree[0]
        word.pos = tree.node
        word.parent = parent
        word.location = loc
    else:
        prod = Production()
        prod.lhs = tree.node
        prod.rhs = ' '.join(n.node for n in tree)
        prod.parent = parent
        prod.location = loc

        # some productions are related to semantic representation
        if prod.lhs == 'RELATION':
            prod.relation = rel

        elif prod.lhs == 'LANDMARK-PHRASE':
            prod.landmark = scene.get_landmark_id(lmk)
            # next landmark phrase will need the parent landmark
            lmk = parent_landmark(lmk)

        elif prod.lhs == 'LANDMARK':
            prod.landmark = parent.landmark

        # save subtrees, keeping track of parent
        for subtree in tree:
            save_tree(subtree, loc, rel, lmk, scene, prod)



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('csvfile', type=file)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-i', '--iterations', type=int, default=1)
    args = parser.parse_args()

    # initialize our default scene
    scene = ModelScene()

    reader = csv.reader(args.csvfile, lineterminator='\n')
    next(reader)  # skip headers

    for i,row in enumerate(reader, start=1):
        print 'sentence', i

        # unpack row
        xloc, yloc, sentence, parse, modparse = row

        # convert variables to the right types
        xloc = float(xloc)
        yloc = float(yloc)
        loc = (xloc, yloc)
        parse = ParentedTree.parse(parse)
        modparse = ParentedTree.parse(modparse)

        # how many ancestors should the sampled landmark have?
        num_ancestors = count_lmk_phrases(modparse) - 1

        # sample `args.iterations` times for each sentence
        for _ in xrange(args.iterations):
            lmk, rel = scene.sample_lmk_rel(loc, num_ancestors)

            # relation type
            rel_type = rel.__class__.__name__

            if args.verbose:
                print 'utterance:', repr(sentence)
                print 'location: %s' % repr(loc)
                print 'landmark: %s (%s)' % (lmk, scene.get_landmark_id(lmk))
                print 'relation: %s' % rel_type
                print 'parse:'
                print parse.pprint()
                print 'modparse:'
                print modparse.pprint()
                print '-' * 70

            location = Location(x=xloc, y=yloc)
            save_tree(modparse, location, rel_type, lmk, scene)
            Bigram.make_bigrams(location.words)
            Trigram.make_trigrams(location.words)
            session.commit()
