#!/usr/bin/env python

from __future__ import division

import os
import sys
import csv
import random
import pprint
import json

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
            # sample landmark, relation and degree
            for j in range(iters):
                lmk_name, lmk_loc = sample_landmark(location)
                relation, degree = sample_reldeg(location, lmk_loc)
                # parse sentence
                # parse = parse_sentence(phrase)['parsetree']
                rel_words, lmk_words, rel_phrases, lmk_phrases = modify_parse(parse)
                
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

                rel_ctx = RelationContext.get_or_create(
                    relation=relation,
                    degree=degree)

                lmk_ctx = LandmarkContext.get_or_create(
                    landmark_name = lmk_name,
                    landmark_location = lmk_loc)

                ctx = Context.get_or_create(
                    ## location = location,
                    relation = rel_ctx,
                    landmark = lmk_ctx)

                # store structures
                for phr,exp in rel_phrases:
                    role = 'rel'
                    rs = PhraseExpansion()
                    rs.parent = Phrase.get_or_create(phrase = str(phr), role = str(role))
                    rs.expansion = str(exp)
                    rs.role = str(role)
                    rs.context = ctx
                    rs.relation_context = rel_ctx
                    rs.landmark_context = lmk_ctx

                for phr,exp in lmk_phrases:
                    role = 'lmk'
                    ls = PhraseExpansion()
                    ls.parent = Phrase.get_or_create(phrase = str(phr), role = str(role))
                    ls.expansion = str(exp)
                    ls.role = str(role)
                    ls.context = ctx
                    ls.relation_context = rel_ctx
                    ls.landmark_context = lmk_ctx


                # store words with their POS tag
                # note that these are modified POS tags

                ## for w,pos in all_words(rel_chunk, lmk_chunk):
                ##     word = Word()
                ##     word.word = w
                ##     word.pos = pos
                ##     word.context = ctx

                for w,pos,phr in rel_words:
                    role = 'rel'
                    phrase = Phrase.get_or_create(phrase = str(phr), role = str(role))
                    part_of_speech = PartOfSpeech.get_or_create(pos = str(pos), role = str(role))
                    word = Word()
                    word.role = str(role)
                    word.word = str(w)
                    word.pos = part_of_speech
                    word.phrase = phrase
                    word.relation_context = rel_ctx
                    word.landmark_context = lmk_ctx
                    word.context = ctx

                for w,pos,phr in lmk_words:
                    role = 'lmk'
                    phrase = Phrase.get_or_create(phrase = str(phr), role = str(role))
                    part_of_speech = PartOfSpeech.get_or_create(pos = str(pos), role = str(role))
                    word = Word()
                    word.role = str(role)
                    word.word = str(w)
                    word.pos = part_of_speech
                    word.phrase = phrase
                    word.relation_context = rel_ctx
                    word.landmark_context = lmk_ctx
                    word.context = ctx

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

    # save all
    session.commit()
