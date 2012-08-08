#!/usr/bin/env python

from __future__ import division

import os
import sys
import csv
import random
import pprint
import json
from itertools import product

from tabledb import *
from generate_relations import sample_landmark, sample_reldeg
#from parse_functions import get_parse
from post_parse_functions import modify_parse

pprinter = pprint.PrettyPrinter()
def pf(obj):
    return pprinter.pformat(obj)

if __name__ == '__main__':
    import getopt
    opts, extraparams = getopt.getopt(sys.argv[1:], 'vi:', ['verbose','iterations'])
    verbose = False
    iters = 1
    for o,p in opts:
        if o in ['-v', '--verbose']:
            verbose = True
        elif o in ['-i', '--iterations']:
            iters = int(p)

    print 'appending...'
    with open('sentences2.csv') as f:
        reader = csv.reader(f)
        next(reader)  # skip headers
        sentence_number = 0
        for row in reader:
            sentence_number += 1
            print 'Sentence #%d' % sentence_number
            # unpack row and convert to the rigth types
            location, region, nearfar, precise, utterance, parse = row
            location = int(location) / 100.0
            # precise = (precise == 'T')
            # parse sentence
            # parse = parse_sentence(phrase)['parsetree']
            rel_words, lmk_words, rel_phrases, lmk_phrases = modify_parse(parse)
            # sample landmark, relation and degree
            for j in range(iters):
                lmk_name, lmk_loc = sample_landmark(location)
                relation, degree = sample_reldeg(lmk_loc, location)

                if verbose:
                    print '-' * 70
                    print 'Utterance: %r' % utterance
                    print 'Location: %s' % location
                    print 'Landmark: %s (%s)' % (lmk_loc, lmk_name)
                    print 'Relation: %s' % relation
                    print 'Degree: %s' % degree
                    print 'Parse tree:\n%s' % parse
                    #print 'Modified parse tree:\n%s' % modparse
                    #print 'Parse tree as list:\n%s' % pf(lparse)
                    #print 'Modified parse tree as list:\n%s' % pf(lmodparse)
                    #print 'Relation chunk:\n%s' % pf(rel_chunk)
                    #print 'Landmark chunk:\n%s' % pf(lmk_chunk)
                    print 'Relation structure: %s' % rel_phrases[0][1]
                    print 'Landmark structure: %s' % lmk_phrases[0][1]
                    print 'Relation words:\n%s' % pf(rel_words)
                    print 'Landmark words:\n%s' % pf(lmk_words)
                    print

                # get context from db or create a new one

                ctx = Context(location=location,
                              landmark=lmk_loc,
                              landmark_name=lmk_name,
                              relation=relation,
                              degree=degree)

                # store structures
                for phr,exp in rel_phrases:
                    role = 'rel'
                    rs = Phrase(expansion=' '.join(exp),
                                role=role,
                                parent=phr,
                                context=ctx)

                for phr,exp in lmk_phrases:
                    role = 'lmk'
                    ls = Phrase(expansion=' '.join(exp),
                                role=role,
                                parent=phr,
                                context=ctx)

                # store words with their POS tag
                # note that these are modified POS tags

                ## for w,pos in all_words(rel_chunk, lmk_chunk):
                ##     word = Word()
                ##     word.word = w
                ##     word.pos = pos
                ##     word.context = ctx

                for w,pos,phr in rel_words:
                    role = 'rel'
                    word = Word(word=w,
                                pos=pos,
                                role=role,
                                phrase=phr,
                                context=ctx)

                for w,pos,phr in lmk_words:
                    role = 'lmk'
                    word = Word(word=w,
                                pos=pos,
                                role=role,
                                phrase=phr,
                                context=ctx)

                ## # store bigrams and trigrams
                ## for w1,w2 in bigrams(utterance):
                ##     bi = Bigram()
                ##     bi.word1 = w1
                ##     bi.word2 = w2
                ##     bi.context = ctx

                ## for w1,w2,w3 in trigrams(utterance):
                ##     tri = Trigram()
                ##     tri.word1 = w1
                ##     tri.word2 = w2
                ##     tri.word3 = w3
                ##     tri.context = ctx

            # commit each sentence
            session.commit()


    sys.exit()
    print 'counting...'
    uniq_words = [row[0] for row in session.query(Word.word).group_by(Word.word)]
    uniq_pos = [row[0] for row in session.query(Word.pos).group_by(Word.pos)]
    uniq_lmks = [row[0] for row in session.query(Context.landmark).group_by(Context.landmark)]
    uniq_rels = [row[0] for row in session.query(Context.relation).group_by(Context.relation)]
    uniq_degs = [row[0] for row in session.query(Context.degree).group_by(Context.degree)]
    uniq_exp = [row[0] for row in session.query(Phrase.expansion).group_by(Phrase.expansion)]
    uniq_roles = [row[0] for row in session.query(Phrase.role).group_by(Phrase.role)]
    uniq_phrs = [row[0] for row in session.query(Phrase.parent).group_by(Phrase.parent)]

    # word probabilities
    for w,pos,phr,lmk,rel,deg in product(uniq_words, uniq_pos, uniq_phrs, uniq_lmks, uniq_rels, uniq_degs):
        # pw = Pword.calc_prob(word=w)
        # print pw

        # pw = Pword.calc_prob(word=w, pos=pos)
        # print pw

        # pw = Pword.calc_prob(word=w, phr=phr)
        # print pw

        # pw = Pword.calc_prob(word=w, lmk=lmk)
        # print pw

        # pw = Pword.calc_prob(word=w, rel=rel)
        # print pw

        # pw = Pword.calc_prob(word=w, deg=deg)
        # print pw

        # pw = Pword.calc_prob(word=w, rel=rel, deg=deg)
        # print pw

        # pw = Pword.calc_prob(word=w, lmk=lmk, rel=rel, deg=deg)
        # print pw

        pw = Pword.calc_prob(word=w, pos=pos, phr=phr, lmk=lmk)
        print pw

        pw = Pword.calc_prob(word=w, pos=pos, phr=phr, rel=rel, deg=deg)
        print pw

        # pw = Pword.calc_prob(word=w, pos=pos, phr=phr, lmk=lmk, rel=rel, deg=deg)
        # print pw

        session.commit()

    for e,phr,lmk,rel,deg in product(uniq_exp, uniq_phrs, uniq_lmks, uniq_rels, uniq_degs):
        # pe = Pexpansion.calc_prob(expansion=e)
        # print pe

        # pe = Pexpansion.calc_prob(expansion=e, parent=phr)
        # print pe

        # pe = Pexpansion.calc_prob(expansion=e, lmk=lmk)
        # print pe

        # pe = Pexpansion.calc_prob(expansion=e, rel=rel)
        # print pe

        # pe = Pexpansion.calc_prob(expansion=e, deg=deg)
        # print pe

        # pe = Pexpansion.calc_prob(expansion=e, rel=rel, deg=deg)
        # print pe

        # pe = Pexpansion.calc_prob(expansion=e, lmk=lmk, rel=rel, deg=deg)
        # print pe

        pe = Pexpansion.calc_prob(expansion=e, parent=phr, lmk=lmk)
        print pe

        pe = Pexpansion.calc_prob(expansion=e, parent=phr, rel=rel, deg=deg)
        print pe

        session.commit()
