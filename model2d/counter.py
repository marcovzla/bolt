#!/usr/bin/env python
# coding: utf-8

from __future__ import division

import csv

from models import (Location, Word, Production, Bigram, Trigram,
                    CWord, CProduction, session)
from utils import parent_landmark, count_lmk_phrases, get_meaning, rel_type, lmk_id

from table2d.landmark import Landmark

from nltk.tree import ParentedTree

from sqlalchemy import func
from sqlalchemy.orm import aliased



def save_tree(tree, loc, rel, lmk, parent=None):
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
            prod.relation = rel_type(rel)
            if hasattr(rel, 'measurement'):
                prod.relation_distance_class = rel.measurement.best_distance_class
                prod.relation_degree_class = rel.measurement.best_degree_class

        elif prod.lhs == 'LANDMARK-PHRASE':
            prod.landmark = lmk_id(lmk)
            prod.landmark_class = lmk.object_class
            # next landmark phrase will need the parent landmark
            lmk = parent_landmark(lmk)

        elif prod.lhs == 'LANDMARK':
            # LANDMARK has the same landmark as its parent LANDMARK-PHRASE
            prod.landmark = parent.landmark
            prod.landmark_class = parent.landmark_class

        # save subtrees, keeping track of parent
        for subtree in tree:
            save_tree(subtree, loc, rel, lmk, prod)



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('csvfile', type=file)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-i', '--iterations', type=int, default=1)
    args = parser.parse_args()

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
            lmk, rel = get_meaning(loc, num_ancestors)
            lmk, _, _ = lmk
            rel, _, _ = rel

            if args.verbose:
                print 'utterance:', repr(sentence)
                print 'location: %s' % repr(loc)
                print 'landmark: %s (%s)' % (lmk, lmk_id(lmk))
                print 'relation: %s' % rel_type(rel)
                print 'parse:'
                print parse.pprint()
                print 'modparse:'
                print modparse.pprint()
                print '-' * 70

            location = Location(x=xloc, y=yloc)
            save_tree(modparse, location, rel, lmk)
            Bigram.make_bigrams(location.words)
            Trigram.make_trigrams(location.words)
            session.commit()



    # count words
    parent = aliased(Production)
    qry = session.query(Word.word, Word.pos,
                        parent.landmark, parent.landmark_class,
                        parent.relation, parent.relation_distance_class,
                        parent.relation_degree_class, func.count(Word.id)).\
                  join(parent, Word.parent).\
                  group_by(Word.word, Word.pos,
                           parent.landmark, parent.landmark_class,
                           parent.relation, parent.relation_distance_class,
                           parent.relation_degree_class)
    for row in qry:
        cw = CWord(word=row[0],
                   pos=row[1],
                   landmark=row[2],
                   landmark_class=row[3],
                   relation=row[4],
                   relation_distance_class=row[5],
                   relation_degree_class=row[6],
                   count=row[7])

    # count productions with no parent
    parent = aliased(Production)
    qry = session.query(Production.lhs, Production.rhs,
                        Production.landmark, Production.landmark_class,
                        Production.relation, Production.relation_distance_class,
                        Production.relation_degree_class, func.count(Production.id)).\
                  filter_by(parent=None).\
                  group_by(Production.lhs, Production.rhs,
                           Production.landmark, Production.landmark_class,
                           Production.relation, Production.relation_distance_class,
                           Production.relation_degree_class)
    for row in qry:
        cp = CProduction(lhs=row[0],
                         rhs=row[1],
                         landmark=row[2],
                         landmark_class=row[3],
                         relation=row[4],
                         relation_distance_class=row[5],
                         relation_degree_class=row[6],
                         count=row[7])

    # count productions with parent
    parent = aliased(Production)
    qry = session.query(Production.lhs, Production.rhs,
                        parent.lhs, Production.landmark, Production.landmark_class,
                        Production.relation, Production.relation_distance_class,
                        Production.relation_degree_class, func.count(Production.id)).\
                  join(parent, Production.parent).\
                  group_by(Production.lhs, Production.rhs,
                           parent.lhs, Production.landmark, Production.landmark_class,
                           Production.relation, Production.relation_distance_class,
                           Production.relation_degree_class)
    for row in qry:
        cp = CProduction(lhs=row[0],
                         rhs=row[1],
                         parent=row[2],
                         landmark=row[3],
                         landmark_class=row[4],
                         relation=row[5],
                         relation_distance_class=row[6],
                         relation_degree_class=row[7],
                         count=row[8])

    session.commit()
