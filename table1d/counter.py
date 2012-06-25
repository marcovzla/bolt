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

## sys.path.append(os.path.expanduser('~/github/stanford-corenlp-python'))
## from corenlp import StanfordCoreNLP
## corenlp = StanfordCoreNLP()

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
    # Other (Note: I changed the way OF-phrases are parsed.  --Colin)
    ("\(NP \(NP(?P<NP1>( \(.*?\))*)\) \(PP (?P<of>\(IN of\)) \(NP(?P<NP2>( \(.*?\))*)\)",
     "(OFNP (OFNP1\g<NP1>) (OF of) (OFNP2\g<NP2>))"),
    ("\(ADVP \(RB very\) \(PP ", "(PP (RB very) "),
    ("\(RB not\) \(PP ", "(PP (NEG not) "),
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

## def lmk_struct(chunk):
##     struct = []
##     for n in chunk:
##         if isinstance(n, list):
##             if n[0] in ['NP']:
##                 #expand NP
##                 struct.append(struct_desc(n[1:]))
##             else:
##                 struct.append(n[0])
##         else:
##             struct.append(n)
##     return ' '.join(struct)

def get_expansion(parse):
    return (parse[0], map(lambda(x): x[0], parse[1:]))

def get_phrases(chunk):
    phrase_tuples = []
    if chunk[0] in ['REL', 'LMK', 'NP', 'PP', 'OFNP', 'OFNP1', 'OFNP2']:
        phrase_tuples.append(get_expansion(chunk))
    for n in chunk[1:]:
        phrase_tuples += get_phrases(n)
    return(phrase_tuples)

def get_words_once(chunk, phrase):
    #formerly get_words()
    return [(' '.join(n[1:]), n[0], phrase) for n in chunk]

def get_words(chunk):
    #formerly lmk_words()
    word_tuples = []
    for n in chunk:
        if isinstance(n, list):
            if n[0] in ['REL', 'LMK', 'NP', 'PP', 'OFNP', 'OFNP1', 'OFNP2']:
                word_tuples += get_words(n)
            else:
                word_tuples += get_words_once([n], chunk[0])
        elif n in ['REL', 'LMK', 'NP', 'PP', 'OFNP', 'OFNP1', 'OFNP2']:
            continue
        else:
            word_tuples.append((n,n,chunk[0]))
    return word_tuples

## def all_words(rel_chunk, lmk_chunk):
##     return rel_words(rel_chunk) + lmk_words(lmk_chunk)

def modify_parse(parse):
     # modify parsetree
     modparse = regex_replace_phrases(parse, regex_replacement_phrases)
     # listify parsetrees
     lparse = to_list(parse)
     lmodparse = to_list(modparse)
     # extract relation and landmark chunks of the parsetree
     rel_chunk = ['REL'] + lmodparse[1][1:-1]
     lmk_chunk = ['LMK'] + [lmodparse[1][-1]]
     rel_words = get_words(rel_chunk)
     lmk_words = get_words(lmk_chunk)
     rel_phrases = get_phrases(rel_chunk)
     lmk_phrases = get_phrases(lmk_chunk)
     return(rel_words, lmk_words, rel_phrases, lmk_phrases)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    iters = 1
    
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
                
                if args.verbose:
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

                    # store bigrams and trigrams
                    for w1,w2 in bigrams(utterance):
                        bi = Bigram()
                        bi.word1 = w1
                        bi.word2 = w2
                        bi.context = ctx

                    for w1,w2,w3 in trigrams(utterance):
                        tri = Trigram()
                        tri.word1 = w1
                        tri.word2 = w2
                        tri.word3 = w3
                        tri.context = ctx

    # save all
    session.commit()
