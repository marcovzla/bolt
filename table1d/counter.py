#!/usr/bin/env python

from __future__ import division

import os
import sys
import csv
import json
import random
import pprint
from functools import partial

from tabledb import *
from parsetools import listify, regex_replace_phrases
from generate_relations import sample_landmark, sample_reldeg

# sys.path.append(os.path.expanduser('~/github/stanford-corenlp-python'))
# from corenlp import StanfordCoreNLP
# corenlp = StanfordCoreNLP()



def parse_sentence(s):
    """Returns a dictionary with the parse results returned by
    the Stanford parser for the provided sentence."""
    return json.loads(corenlp.parse(s, verbose=False))['sentences'][0]



regex_replacement_phrases = [
    # remove FRAG
    (r'^\(ROOT \(FRAG (.+)\)\)', r'(ROOT \1)'),
    # P
    (r'\(PP \(IN on\) \(NP \(NP \(PRP\$ my\) \(NN side\)\) \(PP \(IN of\) (.+)\)\)\)',
     r'(PP (IN on) (PRP$ my) (NN side) (IN of) \1)'),
    ("\(PP \(IN on\) \(NP \(NP \(DT this\) \(NN side\)\) \(PP \(IN of\)",
     "(PP (P on this side of)"),
    (r'\(PP \(IN on\) \(NP \(NP \(DT the\) \(JJ other\) \(NN side\)\) \(PP \(IN of\)',
     r'(PP (P on the other side of)'),
    ("\(ADJP \(ADJP \(RB very\) \(RB close\)\) \(PP \(TO to\)",
     "(ADVP (RB very) (PP (P close to)"),
    ("\(ADVP \(RB far\) \(PP \(IN from\)", "(PP (P far from)"),
    ("\(ADVP \(RB close\) \(PP \(TO to\)", "(PP (P close to)"),
    # Other
    ("\(NP \(NP(?P<NP1>( \(.*?\))*)\) \(PP (?P<of>\(IN of\)) \(NP(?P<NP2>( \(.*?\))*)\)",
     "(NP (NP\g<NP1>) of (NP\g<NP2>))"),
    ("\(ADVP \(RB very\) \(PP ", "(PP (RB very) "),
    ("\(RB not\) \(PP ", "(PP (RB not) "),
    (r'\(ADVP \(RB nearly\)\) \(PP ', '(PP (RB nearly) '),
    (r'\(ROOT \(ADJP \(JJR closer\) \(PP (.+)\)\)\)', r'(ROOT (PP (JJR closer) \1))'),
    (r'\(NP \(NP \(PRP me\)\) \(PP \(IN than\) (.+)\)\)', r'(PRP me) (IN than) \1'),
]



def to_list(parsetree):
    return listify(parsetree.encode('utf-8').split())[0]



pprinter = pprint.PrettyPrinter()
def pf(obj):
    return pprinter.pformat(obj)



def ngram_tokenizer(sent, n):
    """tokenizes `sent` and adds the right number of beginning of sentence
    and end of sentence tokens, given `n`."""
    return ['<s>'] * (n-1) + sent.split() + ['</s>'] * (n>1)

def ngrams(sent, n):
    """returns the ngrams found in `sent`"""
    tokens = ngram_tokenizer(sent, n)
    return [tuple(tokens[i:i+n]) for i in xrange(len(tokens)-n+1)]

unigrams = partial(ngrams, n=1)
bigrams = partial(ngrams, n=2)
trigrams = partial(ngrams, n=3)
# what's next? quadgrams? fourgrams? And what follows that?



# FIXME there is something wrong with `generate_relations.sample_reldeg`
# so we will use this function temporarily.
# This function ignores its arguments and returns random (but valid) values.
# def sample_reldeg(loc, lmk):
#     relations = ['is-adjacent', 'is-not-adjacent', 'is-greater', 'is-less']
#     degrees = [1, 2, 3]
#     return random.choice(relations), random.choice(degrees)



# NOTE the following functions return a structure built using only POS tags

def struct_desc(chunk):
    return ' '.join(n[0] for n in chunk)

rel_struct = struct_desc

def lmk_struct(chunk):
    struct = []
    for n in chunk:
        if isinstance(n, list):
            if n[0] == 'NP':
                # expand NP
                struct.append(struct_desc(n[1:]))
            else:
                struct.append(n[0])
        else:
            struct.append(n)
    return ' '.join(struct)



def get_words(chunk):
    return [(' '.join(n[1:]), n[0]) for n in chunk]

rel_words = get_words

def lmk_words(chunk):
    results = []
    for n in chunk:
        if isinstance(n, list):
            if n[0] == 'NP':
                results += get_words(n[1:])
            else:
                results.append((' '.join(n[1:]), n[0]))
        else:
            results.append((n,n))
    return results

def all_words(rel_chunk, lmk_chunk):
    return rel_words(rel_chunk) + lmk_words(lmk_chunk)



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    with open('sentences2.csv') as f:
        reader = csv.reader(f)
        next(reader)  # skip headers

        for row in reader:
            # unpack row and convert to the rigth types
            location, region, nearfar, precise, phrase, parse = row
            location = int(location)
            precise = (precise == 'T')
            # sample landmark, relation and degree
            lmk_name, lmk_loc = sample_landmark(location/100)
            relation, degree = sample_reldeg(location/100, lmk_loc)
            # parse sentence
            # parse = parse_sentence(phrase)['parsetree']
            # modify parsetree
            modparse = regex_replace_phrases(parse, regex_replacement_phrases)
            # listify parsetrees
            lparse = to_list(parse)
            lmodparse = to_list(modparse)
            # extract relation and landmark chunks of the parsetree
            rel_chunk = lmodparse[1][1:-1]
            lmk_chunk = lmodparse[1][-1][1:]

            if args.verbose:
                print '-' * 70
                print 'Phrase: %r' % phrase
                print 'Location: %s' % location
                print 'Landmark: %s (%s)' % (int(lmk_loc*100), lmk_name)
                print 'Relation: %s' % relation
                print 'Degree: %s' % degree
                print 'Parse tree:\n%s' % parse
                print 'Modified parse tree:\n%s' % modparse
                print 'Parse tree as list:\n%s' % pf(lparse)
                print 'Modified parse tree as list:\n%s' % pf(lmodparse)
                print 'Relation chunk:\n%s' % pf(rel_chunk)
                print 'Landmark chunk:\n%s' % pf(lmk_chunk)
                print 'Relation structure: %s' % rel_struct(rel_chunk)
                print 'Landmark structure: %s' % lmk_struct(lmk_chunk)
                print 'Relation words:\n%s' % pf(rel_words(rel_chunk))
                print 'Landmark words:\n%s' % pf(lmk_words(lmk_chunk))
                print

            # get context from db or create a new one
            ctx = Context.get_or_create(
                    location=location,
                    landmark_location=int(lmk_loc*100),
                    landmark_name=lmk_name,
                    relation=relation,
                    degree=degree)

            # store structures
            rs = RelationStructure()
            rs.structure = rel_struct(rel_chunk)
            rs.context = ctx

            ls = LandmarkStructure()
            ls.structure = lmk_struct(lmk_chunk)
            ls.context = ctx

            # store words with their POS tag
            # note that these are modified POS tags
            for w,pos in all_words(rel_chunk, lmk_chunk):
                word = Word()
                word.word = w
                word.pos = pos
                word.context = ctx

            # store bigrams and trigrams
            for w1,w2 in bigrams(phrase):
                bi = Bigram()
                bi.word1 = w1
                bi.word2 = w2
                bi.context = ctx

            for w1,w2,w3 in trigrams(phrase):
                tri = Trigram()
                tri.word1 = w1
                tri.word2 = w2
                tri.word3 = w3
                tri.context = ctx

    # save all
    session.commit()
